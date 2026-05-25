import time
import requests
import urllib.parse
import secrets
import logging
from typing import Optional, Dict, Any, Tuple
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from functools import wraps
from firebase_admin import firestore, auth as firebase_auth
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_http_methods

from Smarko_App.utils import (
    get_client_ip,
    log_security_event,
    fetch_firestore_doc,
    fetch_firestore_collection,
    get_session_user,
    validate_password_match,
    render_error,
    get_firestore_client
)
from Smarko_App.email_templates import EmailTemplate

logger = logging.getLogger(__name__)
db = get_firestore_client()


def firebase_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.session.get('uid'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_has_valid_consent(uid: str) -> bool:
    if not db:
        return True
    filters = [
        ('firebase_uid', '==', uid),
        ('is_active', '==', True),
    ]
    docs = fetch_firestore_collection('consent_records', filters=filters, limit=1, db=db)
    return len(docs) > 0


def get_or_create_user_from_identifier(identificador: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    email_login = None
    uid = None
    username_real = None

    if '@' in identificador:
        email_login = identificador
        try:
            user_record = firebase_auth.get_user_by_email(email_login)
            uid = user_record.uid
            username_real = user_record.display_name
        except Exception as e:
            logger.debug(f"User lookup by email failed: {e}")
    else:
        filters = [('username', '==', identificador)]
        docs = fetch_firestore_collection('perfis', filters=filters, limit=1, db=db)
        if docs:
            email_login = docs[0].get('email')
            uid = docs[0].get('uid')
            username_real = docs[0].get('username')

    return email_login, uid, username_real or identificador


def check_login_attempt_limit(uid: str, request: HttpRequest) -> Tuple[bool, Optional[int]]:
    perfil = fetch_firestore_doc('perfis', uid, db)
    bloqueio = perfil.get('bloqueado_ate')

    if bloqueio and timezone.now() < bloqueio:
        minutos_restantes = int((bloqueio - timezone.now()).total_seconds() / 60) + 1
        return False, minutos_restantes
    return True, None


def handle_login_failure(uid: str, username: str, email: str, request: HttpRequest) -> None:
    perfil = fetch_firestore_doc('perfis', uid, db)
    tentativas = perfil.get('tentativas_falhas', 0) + 1

    if not db:
        return

    perfil_ref = db.collection('perfis').document(uid)
    perfil_ref.update({'tentativas_falhas': tentativas})

    if tentativas >= 3:
        perfil_ref.update({'bloqueado_ate': timezone.now() + timedelta(minutes=5)})
        event = 'Falha login - Conta bloqueada (3 tentativas)'
        log_security_event(uid, username, event, get_client_ip(request))
        messages.error(request, 'Múltiplas tentativas falhas. Conta bloqueada por 5 minutos.')
    else:
        event = f'Falha login - Senha incorreta (tentativa {tentativas}/3)'
        log_security_event(uid, username, event, get_client_ip(request))
        messages.error(request, f'Senha incorreta. Tentativa {tentativas} de 3.')


def authenticate_with_firebase(email: str, password: str) -> Optional[Dict[str, Any]]:
    api_key = getattr(settings, 'FIREBASE_WEB_API_KEY', '')
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}'

    try:
        resp = requests.post(
            url,
            json={
                'email': email,
                'password': password,
                'returnSecureToken': True
            },
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"Firebase auth failed: {e}")
    return None


def send_2fa_email(email: str, code: str, name: Optional[str] = None) -> None:
    body = f"Your login code: {code}\n\nValid for 2 minutes."
    html_message = EmailTemplate.render_2fa(code, name)
    try:
        send_mail(
            "Smarko - Login Code",
            body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message
        )
    except Exception as e:
        logger.error(f"Failed to send 2FA email: {e}")


def send_password_reset_email(email: str, reset_link: str) -> None:
    html_msg = EmailTemplate.render_password_reset(reset_link)
    try:
        send_mail(
            "Smarko - Password Reset",
            f"Reset link: {reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_msg
        )
    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")


def register_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        if not db:
            return render_error(
                request,
                'Smarko_App/register.html',
                'Firebase não está configurado.'
            )

        usuario = request.POST.get('usuario')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        confirmacao = request.POST.get('confirmacao')
        accepted_terms = request.POST.get('accepted_terms')
        accepted_privacy = request.POST.get('accepted_privacy')

        if not (usuario and senha and email):
            return render_error(request, 'Smarko_App/register.html', 'Preencha todos os campos.')

        if not (accepted_terms and accepted_privacy):
            return render_error(
                request,
                'Smarko_App/register.html',
                'Você deve aceitar Política de Privacidade e Termos de Uso.'
            )

        if not validate_password_match(senha, confirmacao):
            return render_error(request, 'Smarko_App/register.html', 'As senhas não coincidem.')

        try:
            user_record = firebase_auth.create_user(
                email=email,
                password=senha,
                display_name=usuario
            )

            if db:
                db.collection('perfis').document(user_record.uid).set({
                    'username': usuario,
                    'email': email,
                    'senha_hash': make_password(senha),
                    'tentativas_falhas': 0,
                    'bloqueado_ate': None,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'role': 'user'
                })

                db.collection('consent_records').document(user_record.uid).set({
                    'firebase_uid': user_record.uid,
                    'email': email,
                    'version': 1,
                    'ip_address': get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                    'accepted_terms': accepted_terms == 'on',
                    'accepted_privacy': accepted_privacy == 'on',
                    'is_active': True,
                    'given_at': firestore.SERVER_TIMESTAMP
                })

                log_security_event(user_record.uid, usuario, 'Conta Criada', get_client_ip(request))

            messages.success(request, 'Conta criada com sucesso! Faça login para continuar.')
            return redirect('login')
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return render_error(request, 'Smarko_App/register.html', f'Erro ao registar: {str(e)}')

    return render(request, 'Smarko_App/register.html')


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        if not db:
            return render_error(request, 'Smarko_App/login.html', 'Firebase não está configurado.')

        identificador = request.POST.get('username')
        senha_digitada = request.POST.get('password')

        try:
            email_login, uid, username_real = get_or_create_user_from_identifier(identificador)

            if not (email_login and uid):
                messages.error(request, 'Utilizador ou senha incorretos.')
                return render(request, 'Smarko_App/login.html')

            allowed, mins_left = check_login_attempt_limit(uid, request)
            if not allowed:
                log_security_event(uid, username_real, 'Tentativa de login bloqueada (cooldown)', get_client_ip(request))
                messages.error(request, f'Conta bloqueada. Tente novamente em {mins_left} min.')
                return render(request, 'Smarko_App/login.html')

            auth_response = authenticate_with_firebase(email_login, senha_digitada)

            if auth_response:
                if db:
                    db.collection('perfis').document(uid).update({
                        'tentativas_falhas': 0,
                        'bloqueado_ate': None
                    })

                codigo = str(secrets.randbelow(1000000)).zfill(6)
                request.session['codigo_2fa'] = codigo
                request.session['user_id_pre_auth'] = uid
                request.session['user_name_pre_auth'] = username_real
                request.session['user_email_pre_auth'] = email_login
                request.session['codigo_2fa_timestamp'] = time.time()

                send_2fa_email(email_login, codigo, username_real)
                return redirect('verificar_2fa')
            else:
                handle_login_failure(uid, username_real, email_login, request)

        except Exception as e:
            logger.error(f"Login error: {e}")
            messages.error(request, f'Erro ao consultar dados: {str(e)}')

    return render(request, 'Smarko_App/login.html')


def verificar_2fa_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        uid = request.session.get('user_id_pre_auth')
        username = request.session.get('user_name_pre_auth')

        if time.time() - request.session.get('codigo_2fa_timestamp', 0) > 120:
            log_security_event(uid, username, 'Falha 2FA - Código expirado', get_client_ip(request))
            messages.error(request, 'O código expirou. Tente novamente.')
            return redirect('login')

        if request.POST.get('codigo') == request.session.get('codigo_2fa'):
            request.session['uid'] = uid
            request.session['username'] = request.session.get('user_name_pre_auth')
            request.session['email'] = request.session.get('user_email_pre_auth')
            log_security_event(uid, request.session['username'], 'Login Sucesso', get_client_ip(request))

            if not user_has_valid_consent(uid):
                request.session['pending_consent_uid'] = uid
                return redirect('update_consent')

            return redirect('home')

        log_security_event(uid, username, 'Falha 2FA - Código inválido', get_client_ip(request))
        messages.error(request, 'Código inválido.')

    return render(request, 'Smarko_App/verificar_2fa.html', {'hide_footer': True})


def reset_password_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        email = request.POST.get('email')
        ip = get_client_ip(request)

        try:
            action_settings = firebase_auth.ActionCodeSettings(
                url='https://smarkoo.vercel.app/reset_confirm/',
                handle_code_in_app=False,
            )
            fb_link = firebase_auth.generate_password_reset_link(email, action_settings)
            parsed_url = urllib.parse.urlparse(fb_link)
            oob_code = urllib.parse.parse_qs(parsed_url.query).get('oobCode', [None])[0]

            if oob_code and db:
                db.collection('tokens_recuperacao').document(oob_code).set({
                    'email': email,
                    'criado_em': time.time()
                })

                reset_link = f"https://smarkoo.vercel.app/reset_confirm/?oobCode={oob_code}"
                send_password_reset_email(email, reset_link)
                log_security_event('SISTEMA', email, 'Reset Solicitado', ip)
                return redirect('password_reset_done')
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'Smarko_App/password_reset.html')


def password_reset_confirm_view(request: HttpRequest) -> HttpResponse:
    oob_code = request.GET.get('oobCode') or request.POST.get('oobCode')
    ip = get_client_ip(request)

    if not oob_code or not db:
        return render(request, 'Smarko_App/password_reset_confirm_fail.html')

    token_ref = db.collection('tokens_recuperacao').document(oob_code)
    token_doc = token_ref.get()

    if not token_doc.exists:
        log_security_event('SISTEMA', 'Desconhecido', 'Falha Reset - Token Inexistente', ip)
        return render(request, 'Smarko_App/password_reset_confirm_fail.html')

    token_data = token_doc.to_dict()
    tempo_passado = time.time() - token_data.get('criado_em', 0)

    if token_data.get('used_at'):
        log_security_event('SISTEMA', token_data.get('email'), 'Falha Reset - Token Já Utilizado', ip)
        return render(request, 'Smarko_App/password_reset_confirm_fail.html')

    if tempo_passado > 900:
        token_ref.delete()
        log_security_event('SISTEMA', token_data.get('email'), 'Falha Reset - Token Expirado', ip)
        return render(request, 'Smarko_App/password_reset_confirm_fail.html')

    if request.method == "GET":
        return render(request, 'Smarko_App/password_reset_confirm.html', {'oobCode': oob_code})

    if request.method == "POST":
        nova_senha = request.POST.get('nova_senha')
        confirmacao = request.POST.get('confirmacao')

        if not validate_password_match(nova_senha, confirmacao):
            return render_error(
                request,
                'Smarko_App/password_reset_confirm.html',
                'As senhas não coincidem.',
                {'oobCode': oob_code}
            )

        try:
            api_key = getattr(settings, 'FIREBASE_WEB_API_KEY', '')
            reset_url = f"https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={api_key}"
            resp = requests.post(reset_url, json={"oobCode": oob_code, "newPassword": nova_senha}, timeout=5)

            if resp.status_code == 200:
                uid = resp.json().get('localId')
                token_ref.update({'used_at': time.time(), 'used_by_uid': uid})

                if uid and db:
                    db.collection('perfis').document(uid).update({'senha_hash': make_password(nova_senha)})

                log_security_event(uid, token_data.get('email'), 'Senha Redefinida', ip)
                messages.success(request, 'Senha atualizada com sucesso! Faça login.')
                return redirect('login')
            else:
                error_msg = resp.json().get('error', {}).get('message', 'Unknown API error')
                log_security_event('SISTEMA', token_data.get('email'), f'Falha Firebase API: {error_msg}', ip)
                messages.error(request, f'Erro do servidor Firebase: {error_msg}')
        except Exception as e:
            logger.error(f"Password reset confirm error: {e}")
            messages.error(request, f'Erro interno do sistema: {str(e)}')

    return render(request, 'Smarko_App/password_reset_confirm.html', {'oobCode': oob_code})


def reset_password_sent_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'Smarko_App/password_reset_sent.html')


@firebase_login_required
def home_view(request: HttpRequest) -> HttpResponse:
    uid = request.session.get('uid')
    perfil = fetch_firestore_doc('perfis', uid, db)
    user_role = perfil.get('role', 'user')
    return render(request, 'Smarko_App/index.html', {'user_role': user_role})


def logout_view(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    return redirect('login')


def ping_view(request: HttpRequest) -> JsonResponse:
    if request.session.get('uid'):
        request.session.modified = True
    return JsonResponse({'status': 'alive'})


def get_current_policy_version() -> Dict[str, str]:
    return {'version': '1.0', 'effective_date': '2025-01-01'}


def privacy_policy_view(request: HttpRequest) -> HttpResponse:
    version = get_current_policy_version()
    return render(request, 'Smarko_App/privacy_policy.html', {'policy_version': version})


@firebase_login_required
def user_data_view(request: HttpRequest) -> HttpResponse:
    uid, email = get_session_user(request)
    perfil = fetch_firestore_doc('perfis', uid, db)

    filters = [
        ('firebase_uid', '==', uid),
        ('is_active', '==', True),
    ]
    order_by = ('given_at', 'DESCENDING')
    consents = fetch_firestore_collection('consent_records', filters=filters, order_by=order_by, db=db)

    filters = [('usuario_id', '==', uid)]
    audit_logs = fetch_firestore_collection('logs_seguranca', filters=filters, limit=10, db=db)

    filters = [
        ('firebase_uid', '==', uid),
        ('status', '==', 'pending'),
    ]
    deletion_requests = fetch_firestore_collection('account_deletion_requests', filters=filters, limit=1, db=db)
    deletion_request = deletion_requests[0] if deletion_requests else None

    context = {
        'username': perfil.get('username', email),
        'email': email,
        'user_role': perfil.get('role', 'user'),
        'consents': consents,
        'audit_logs': audit_logs[:10],
        'deletion_request': deletion_request,
    }

    return render(request, 'Smarko_App/user_data_dashboard.html', context)


@firebase_login_required
def export_user_data_view(request: HttpRequest) -> JsonResponse:
    uid, email = get_session_user(request)
    perfil = fetch_firestore_doc('perfis', uid, db)

    filters = [('usuario_id', '==', uid)]
    logs = fetch_firestore_collection('logs_seguranca', filters=filters, db=db)

    filters = [('firebase_uid', '==', uid)]
    order_by = ('given_at', 'DESCENDING')
    consents = fetch_firestore_collection('consent_records', filters=filters, order_by=order_by, db=db)

    data = {
        'export_date': timezone.now().isoformat(),
        'profile': {
            'username': perfil.get('username'),
            'email': email,
        },
        'audit_logs': logs,
        'consent_history': [
            {
                'version': c.get('version'),
                'given_at': c.get('given_at'),
                'revoked_at': c.get('revoked_at'),
                'purposes': c.get('purposes', []),
                'ip_address': c.get('ip_address'),
            } for c in consents
        ]
    }

    response = JsonResponse(data, safe=False)
    response['Content-Disposition'] = f'attachment; filename="meus_dados_{uid}.json"'
    return response


def save_consent_record(firebase_uid: str, email: str, request: HttpRequest, purposes: list = None) -> None:
    if not db or purposes is None:
        return
    version_info = get_current_policy_version()
    db.collection('consent_records').document(f"{firebase_uid}_consent").set({
        'firebase_uid': firebase_uid,
        'email': email,
        'version': version_info.get('version'),
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
        'accepted_terms': request.POST.get('accepted_terms') == 'on',
        'accepted_privacy': request.POST.get('accepted_privacy') == 'on',
        'purposes': purposes,
        'given_at': firestore.SERVER_TIMESTAMP,
    })


@require_http_methods(["POST"])
def register_consent_view(request: HttpRequest) -> JsonResponse:
    try:
        firebase_uid = request.POST.get('firebase_uid')
        email = request.POST.get('email')
        purposes = request.POST.getlist('purpose_ids')

        save_consent_record(firebase_uid, email, request, purposes)
        version_info = get_current_policy_version()
        log_security_event(
            firebase_uid,
            email,
            f"Consentimento LGPD Concedido v{version_info.get('version')}",
            get_client_ip(request)
        )

        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Register consent error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def get_purposes() -> list:
    filters = []
    return fetch_firestore_collection('data_purposes', filters=filters, db=db)


@firebase_login_required
@require_http_methods(["POST"])
def revoke_consent_view(request: HttpRequest) -> HttpResponse:
    uid, email = get_session_user(request)
    username = request.session.get('username')

    try:
        filters = [
            ('firebase_uid', '==', uid),
            ('is_active', '==', True),
        ]
        order_by = ('given_at', 'DESCENDING')
        consent_docs = fetch_firestore_collection('consent_records', filters=filters, order_by=order_by, limit=1, db=db)

        if not consent_docs:
            messages.error(request, 'Nenhum registro de consentimento encontrado.')
            return redirect('user_data')

        if not db:
            return redirect('user_data')

        revoked_at = timezone.now()
        consent_doc = consent_docs[0]

        db.collection('consent_records').document(f"{uid}_consent").update({
            'revoked_at': revoked_at,
            'is_active': False,
        })

        log_security_event(uid, username, 'Consentimento Revogado', get_client_ip(request))
        html_msg = EmailTemplate.render_consent_revoked(username)

        send_mail(
            "Smarko - Confirmação de Revogação de Consentimento",
            f"Seu consentimento foi revogado em {revoked_at}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_msg
        )

        messages.success(request, 'Seu consentimento foi revogado com sucesso.')
        return redirect('user_data')
    except Exception as e:
        logger.error(f"Revoke consent error: {e}")
        messages.error(request, f'Erro ao revogar consentimento: {str(e)}')
        return redirect('user_data')


@firebase_login_required
@require_http_methods(["POST"])
def request_account_deletion_view(request: HttpRequest) -> HttpResponse:
    uid, email = get_session_user(request)
    username = request.session.get('username')

    try:
        if not db:
            messages.error(request, 'Firebase não está configurado.')
            return redirect('user_data')

        token = secrets.token_urlsafe(32)
        requested_at = timezone.now()
        deletion_scheduled_for = requested_at + timedelta(days=30)

        db.collection('account_deletion_requests').document(f"{uid}_{token}").set({
            'firebase_uid': uid,
            'email': email,
            'requested_at': requested_at,
            'deletion_scheduled_for': deletion_scheduled_for,
            'confirmation_token': token,
            'status': 'pending'
        })

        cancel_url = f"https://smarkoo.vercel.app/cancel-deletion/?token={token}"
        html_msg = EmailTemplate.render_account_deletion(email, 30)

        send_mail(
            "Smarko - Account Deletion Request",
            f"Sua conta será deletada em 30 dias",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_msg
        )

        log_security_event(uid, username, 'Exclusão de Conta Solicitada (30 dias)', get_client_ip(request))
        messages.success(request, 'Solicitação de exclusão enviada. Você tem 30 dias para cancelar.')
        return redirect('user_data')
    except Exception as e:
        logger.error(f"Request account deletion error: {e}")
        messages.error(request, f'Erro ao solicitar exclusão: {str(e)}')
        return redirect('user_data')


@require_http_methods(["GET"])
def cancel_account_deletion_view(request: HttpRequest) -> HttpResponse:
    token = request.GET.get('token')
    ip = get_client_ip(request)

    if not token or not db:
        messages.error(request, 'Token inválido.')
        return redirect('login')

    try:
        filters = [('confirmation_token', '==', token)]
        deletion_docs = fetch_firestore_collection('account_deletion_requests', filters=filters, limit=1, db=db)

        if not deletion_docs:
            messages.error(request, 'Token não encontrado.')
            return redirect('login')

        deletion_data = deletion_docs[0]

        if deletion_data.get('status') != 'pending':
            messages.error(request, 'Esta solicitação já foi processada.')
            return redirect('login')

        db.collection('account_deletion_requests').document(f"{deletion_data.get('firebase_uid')}_{token}").update({
            'status': 'canceled'
        })

        log_security_event(
            deletion_data.get('firebase_uid'),
            deletion_data.get('email'),
            'Exclusão de Conta Cancelada',
            ip
        )

        messages.success(request, 'Exclusão de conta cancelada. Sua conta está segura.')
        return redirect('login')
    except Exception as e:
        logger.error(f"Cancel account deletion error: {e}")
        messages.error(request, f'Erro ao cancelar exclusão: {str(e)}')
        return redirect('login')


def update_consent_view(request: HttpRequest) -> HttpResponse:
    uid = request.session.get('pending_consent_uid')
    email = request.session.get('email')

    if not uid:
        return redirect('login')

    purposes = get_purposes()

    if request.method == "GET":
        context = {'purposes': purposes, 'user_email': email}
        return render(request, 'Smarko_App/update_consent.html', context)

    if request.method == "POST":
        try:
            accepted_privacy = request.POST.get('accepted_privacy') == 'on'
            accepted_terms = request.POST.get('accepted_terms') == 'on'

            if not (accepted_privacy and accepted_terms):
                msg = 'Você deve aceitar a Política de Privacidade e os Termos de Uso.'
                messages.error(request, msg)
                context = {'purposes': purposes, 'user_email': email}
                return render(request, 'Smarko_App/update_consent.html', context)

            purposes_list = request.POST.getlist('purpose_ids')
            version_info = get_current_policy_version()

            if db:
                db.collection('consent_records').document(f"{uid}_consent").set({
                    'firebase_uid': uid,
                    'email': email,
                    'version': version_info.get('version'),
                    'ip_address': get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                    'accepted_terms': accepted_terms,
                    'accepted_privacy': accepted_privacy,
                    'is_active': True,
                    'purposes': purposes_list,
                    'given_at': firestore.SERVER_TIMESTAMP,
                })

                log_security_event(uid, email, f"Consentimento Atualizado v{version_info.get('version')}", get_client_ip(request))

            if 'pending_consent_uid' in request.session:
                del request.session['pending_consent_uid']

            messages.success(request, 'Consent saved successfully. Welcome to Smarko.')
            return redirect('home')
        except Exception as e:
            logger.error(f"Update consent error: {e}")
            messages.error(request, f'Erro ao atualizar consentimento: {str(e)}')
            context = {'purposes': purposes, 'user_email': email}
            return render(request, 'Smarko_App/update_consent.html', context)
