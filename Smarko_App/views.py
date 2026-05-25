import random
import time
import requests
import urllib.parse
import secrets
import json
from django.http import JsonResponse
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

try:
    db = firestore.client()
except Exception:
    db = None

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def registrar_log_firebase(uid, username, evento, ip):
    if not db:
        return
    try:
        db.collection('logs_seguranca').add({
            'usuario_id': uid,
            'usuario_nome': username,
            'evento': evento,
            'ip': ip,
            'data_hora': firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"Failed to log {evento}: {e}")

def firebase_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('uid'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def user_has_valid_consent(uid):
    if not db:
        return True
    try:
        docs = db.collection('consent_records').where('firebase_uid', '==', uid).where('is_active', '==', True).limit(1).stream()
        return next(iter(docs), None) is not None
    except:
        return False

def _render_2fa_email(code, name):
    greeting = f"Hello {name}" if name else "Hello"
    return f"""
    <div style="font-family: Arial; max-width: 500px; margin: 0 auto;">
        <div style="background: #1a182e; color: white; padding: 20px; text-align: center;">
            <h2>Smarko Login</h2>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <p>{greeting},</p>
            <p>Your authentication code:</p>
            <div style="background: white; padding: 20px; text-align: center; border: 1px solid #ddd; margin: 20px 0;">
                <code style="font-size: 24px; font-weight: bold; letter-spacing: 4px;">{code}</code>
            </div>
            <p style="color: #666; font-size: 12px;">Valid for 2 minutes. Don't share this code.</p>
        </div>
    </div>
    """

def send_2fa_email(email, code, name=None):
    body = f"Your login code: {code}\n\nValid for 2 minutes."
    send_mail(
        "Smarko - Login Code",
        body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=_render_2fa_email(code, name)
    )

def register_view(request):
    if request.method == "POST":
        if not db:
            messages.error(request, "Firebase não está configurado. Por favor, configure as credenciais do Firebase.")
            return render(request, 'Smarko_App/register.html')

        usuario = request.POST.get('usuario')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        confirmacao = request.POST.get('confirmacao')
        accepted_terms = request.POST.get('accepted_terms')
        accepted_privacy = request.POST.get('accepted_privacy')


        if not usuario or not senha or not email:
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return render(request, 'Smarko_App/register.html')

        if not accepted_terms or not accepted_privacy:
            messages.error(request, "Você deve aceitar a Política de Privacidade e os Termos de Uso para continuar.")
            return render(request, 'Smarko_App/register.html')

        if senha != confirmacao:
            messages.error(request, "As senhas não coincidem.")
            return render(request, 'Smarko_App/register.html')

        try:
            user_record = firebase_auth.create_user(email=email, password=senha, display_name=usuario)

            senha_hash = make_password(senha)

            db.collection('perfis').document(user_record.uid).set({
                'username': usuario,
                'email': email,
                'senha_hash': senha_hash,
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

            registrar_log_firebase(user_record.uid, usuario, "Conta Criada", get_client_ip(request))
            messages.success(request, "Conta criada com sucesso! Faça login para continuar.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Erro ao registar: {str(e)}")

    return render(request, 'Smarko_App/register.html')

def login_view(request):
    if request.method == "POST":
        if not db:
            messages.error(request, "Firebase não está configurado. Por favor, configure as credenciais do Firebase.")
            return render(request, 'Smarko_App/login.html')

        identificador = request.POST.get('username')
        senha_digitada = request.POST.get('password')

        email_login = None
        uid = None
        username_real = identificador

        try:
            if '@' in identificador:
                email_login = identificador
                try:
                    user_record = firebase_auth.get_user_by_email(email_login)
                    uid = user_record.uid
                    username_real = user_record.display_name
                except: pass
            else:
                docs = db.collection('perfis').where('username', '==', identificador).limit(1).get()
                if docs:
                    email_login = docs[0].to_dict().get('email')
                    uid = docs[0].id

            if not email_login or not uid:
                messages.error(request, "Utilizador ou senha incorretos.")
                return render(request, 'Smarko_App/login.html')
        except Exception as e:
            messages.error(request, f"Erro ao consultar dados: {str(e)}")
            return render(request, 'Smarko_App/login.html')

        perfil_ref = db.collection('perfis').document(uid)
        p_data = perfil_ref.get().to_dict() or {}
        bloqueio = p_data.get('bloqueado_ate')

        if bloqueio and timezone.now() < bloqueio:
            minutos_restantes = int((bloqueio - timezone.now()).total_seconds() / 60) + 1
            registrar_log_firebase(uid, username_real or email_login, f"Tentativa de login bloqueada (conta em cooldown)", get_client_ip(request))
            messages.error(request, f"Conta bloqueada por excesso de tentativas. Tente novamente em {minutos_restantes} min.")
            return render(request, 'Smarko_App/login.html')

        api_key = getattr(settings, 'FIREBASE_WEB_API_KEY', '')
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        resp = requests.post(url, json={"email": email_login, "password": senha_digitada, "returnSecureToken": True})
        
        if resp.status_code == 200:
            perfil_ref.update({'tentativas_falhas': 0, 'bloqueado_ate': None})

            codigo = str(random.randint(100000, 999999))
            request.session['codigo_2fa'] = codigo
            request.session['user_id_pre_auth'] = uid
            request.session['user_name_pre_auth'] = username_real
            request.session['user_email_pre_auth'] = email_login
            request.session['codigo_2fa_timestamp'] = time.time()

            send_2fa_email(email_login, codigo, username_real)
            return redirect('verificar_2fa')
        else:
            tentativas = p_data.get('tentativas_falhas', 0) + 1
            perfil_ref.update({'tentativas_falhas': tentativas})
            if tentativas >= 3:
                perfil_ref.update({'bloqueado_ate': timezone.now() + timedelta(minutes=5)})
                registrar_log_firebase(uid, username_real or email_login, "Falha login - Conta bloqueada (3 tentativas)", get_client_ip(request))
                messages.error(request, "Múltiplas tentativas falhas. Conta bloqueada por 5 minutos.")
            else:
                registrar_log_firebase(uid, username_real or email_login, f"Falha login - Senha incorreta (tentativa {tentativas}/3)", get_client_ip(request))
                messages.error(request, f"Senha incorreta. Tentativa {tentativas} de 3.")

    return render(request, 'Smarko_App/login.html')

def verificar_2fa_view(request):
    if request.method == "POST":
        uid = request.session.get('user_id_pre_auth')
        username = request.session.get('user_name_pre_auth')

        if time.time() - request.session.get('codigo_2fa_timestamp', 0) > 120:
            registrar_log_firebase(uid, username, "Falha 2FA - Código expirado", get_client_ip(request))
            messages.error(request, "O código expirou. Tente novamente.")
            return redirect('login')

        if request.POST.get('codigo') == request.session.get('codigo_2fa'):
            uid = request.session.get('user_id_pre_auth')
            request.session['uid'] = uid
            request.session['username'] = request.session.get('user_name_pre_auth')
            request.session['email'] = request.session.get('user_email_pre_auth')
            registrar_log_firebase(request.session['uid'], request.session['username'], "Login Sucesso", get_client_ip(request))

            if not user_has_valid_consent(uid):
                request.session['pending_consent_uid'] = uid
                return redirect('update_consent')

            return redirect('home')

        registrar_log_firebase(uid, username, "Falha 2FA - Código inválido", get_client_ip(request))
        messages.error(request, "Código inválido.")
    return render(request, 'Smarko_App/verificar_2fa.html', {'hide_footer': True})

def reset_password_view(request):
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

            if oob_code:
                db.collection('tokens_recuperacao').document(oob_code).set({
                    'email': email, 'criado_em': time.time()
                })

                meu_link = f"https://smarkoo.vercel.app/reset_confirm/?oobCode={oob_code}"
                unique_id = time.time()

                html_msg = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 15px; overflow: hidden;">
                    <div style="background: linear-gradient(135deg, #1a182e 0%, #252245 100%); padding: 30px; text-align: center;">
                        <h2 style="color: #ffffff; margin: 0;">Smarko Security</h2>
                    </div>
                    <div style="padding: 40px; text-align: center; background: #ffffff;">
                        <p style="color: #333; font-size: 16px;">Pedido de redefinição de senha recebido.</p>
                        <p style="color: #dc3545; font-weight: bold; margin-bottom: 30px;">Valid for 10 minutes.</p>
                        <a href="{meu_link}" style="background: #1a182e; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Redefinir Senha</a>
                    </div>
                    <div style="display: none; visibility: hidden; opacity: 0; font-size: 1px;">{unique_id}</div>
                </div>
                """
                try:
                    send_mail(
                        "Smarko - Password Reset",
                        f"Reset link: {meu_link}",
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        html_message=html_msg
                    )
                except Exception as e:
                    print(f"Failed to send reset email: {e}")

                registrar_log_firebase("SISTEMA", email, "Reset Solicitado", ip)
                return redirect('password_reset_done')
        except Exception as e:
            print(f"Reset error: {e}")
            messages.error(request, f"Error: {str(e)}")
            return redirect('password_reset_done')
    return render(request, 'Smarko_App/password_reset.html')

def password_reset_confirm_view(request):
    oob_code = request.GET.get('oobCode') or request.POST.get('oobCode')
    ip = get_client_ip(request)

    if not oob_code:
        return render(request, 'Smarko_App/password_reset_confirm_fail.html')

    token_ref = db.collection('tokens_recuperacao').document(oob_code)
    token_doc = token_ref.get()

    if not token_doc.exists:
        registrar_log_firebase("SISTEMA", "Desconhecido", "Falha Reset - Token Inexistente", ip)
        return render(request, 'Smarko_App/password_reset_confirm_fail.html')

    token_data = token_doc.to_dict()
    tempo_passado = time.time() - token_data.get('criado_em', 0)

    if tempo_passado > 180:
        token_ref.delete()
        registrar_log_firebase("SISTEMA", token_data.get('email'), "Falha Reset - Token Expirado", ip)
        return render(request, 'Smarko_App/password_reset_confirm_fail.html')

    api_key = getattr(settings, 'FIREBASE_WEB_API_KEY', '')

    if request.method == "GET":
        return render(request, 'Smarko_App/password_reset_confirm.html', {'oobCode': oob_code})

    if request.method == "POST":
        nova_senha = request.POST.get('nova_senha')
        confirmacao = request.POST.get('confirmacao')

        if nova_senha != confirmacao:
            messages.error(request, "As senhas não coincidem.")
            return render(request, 'Smarko_App/password_reset_confirm.html', {'oobCode': oob_code})

        try:
            reset_url = f"https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={api_key}"
            resp = requests.post(reset_url, json={"oobCode": oob_code, "newPassword": nova_senha})
            
            if resp.status_code == 200:
                uid = resp.json().get('localId')
                if uid:
                    db.collection('perfis').document(uid).update({'senha_hash': make_password(nova_senha)})

                registrar_log_firebase(uid, token_data.get('email'), "Senha Redefinida", ip)
                token_ref.delete() 
                messages.success(request, "Senha atualizada com sucesso! Faça login.")
                return redirect('login')
            else:
                error_msg = resp.json().get('error', {}).get('message', 'Unknown API error')
                registrar_log_firebase("SISTEMA", token_data.get('email'), f"Falha Firebase API: {error_msg}", ip)
                messages.error(request, f"Erro do servidor Firebase: {error_msg}")
                return render(request, 'Smarko_App/password_reset_confirm.html', {'oobCode': oob_code})
        except Exception as e:
            messages.error(request, f"Erro interno do sistema: {str(e)}")
            return render(request, 'Smarko_App/password_reset_confirm.html', {'oobCode': oob_code})

def reset_password_sent_view(request):
    return render(request, 'Smarko_App/password_reset_sent.html')

@firebase_login_required
def home_view(request):
    uid = request.session.get('uid')
    try:
        perfil = db.collection('perfis').document(uid).get().to_dict() or {}
        user_role = perfil.get('role', 'user')
    except:
        user_role = 'user'

    context = {'user_role': user_role}
    return render(request, 'Smarko_App/index.html', context)

def logout_view(request):
    request.session.flush()
    return redirect('login')

def ping_view(request):
    if request.session.get('uid'):
        request.session.modified = True
    return JsonResponse({'status': 'alive'})

def get_current_policy_version():
    return {
        'version': '1.0',
        'effective_date': '2025-01-01',
    }

def privacy_policy_view(request):
    version = get_current_policy_version()
    context = {'policy_version': version}
    return render(request, 'Smarko_App/privacy_policy.html', context)

@firebase_login_required
def user_data_view(request):
    uid = request.session.get('uid')
    email = request.session.get('email')

    try:
        perfil = db.collection('perfis').document(uid).get().to_dict() or {}
    except:
        perfil = {}

    try:
        consent_docs = db.collection('consent_records').where('firebase_uid', '==', uid).where('is_active', '==', True).order_by('given_at', direction=firestore.Query.DESCENDING).stream()
        consents = [doc.to_dict() for doc in consent_docs]
    except:
        consents = []

    try:
        logs = db.collection('logs_seguranca').where('usuario_id', '==', uid).limit(10).stream()
        audit_logs = [log.to_dict() for log in logs]
    except:
        audit_logs = []

    try:
        deletion_docs = db.collection('account_deletion_requests').where('firebase_uid', '==', uid).where('status', '==', 'pending').limit(1).stream()
        deletion_request = next(iter(deletion_docs), None)
        if deletion_request:
            deletion_request = deletion_request.to_dict()
    except:
        deletion_request = None

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
def export_user_data_view(request):
    uid = request.session.get('uid')
    email = request.session.get('email')

    try:
        perfil = db.collection('perfis').document(uid).get().to_dict()
    except:
        perfil = {}

    try:
        logs_stream = db.collection('logs_seguranca').where('usuario_id', '==', uid).stream()
        logs = [log.to_dict() for log in logs_stream]
    except:
        logs = []

    try:
        consent_docs = db.collection('consent_records').where('firebase_uid', '==', uid).order_by('given_at', direction=firestore.Query.DESCENDING).stream()
        consents = [doc.to_dict() for doc in consent_docs]
    except:
        consents = []

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

@require_http_methods(["POST"])
def register_consent_view(request):
    try:
        firebase_uid = request.POST.get('firebase_uid')
        email = request.POST.get('email')
        purposes = request.POST.getlist('purpose_ids')

        version_info = get_current_policy_version()

        db.collection('consent_records').document(f"{firebase_uid}_consent").set({
            'firebase_uid': firebase_uid,
            'email': email,
            'version': version_info.get('version'),
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            'accepted_terms': request.POST.get('accepted_terms') == 'on',
            'accepted_privacy': request.POST.get('accepted_privacy') == 'on',
            'purposes': purposes if purposes else [],
            'given_at': firestore.SERVER_TIMESTAMP,
        })

        registrar_log_firebase(
            firebase_uid,
            email,
            f"Consentimento LGPD Concedido v{version_info.get('version')}",
            get_client_ip(request)
        )

        return JsonResponse({'status': 'success', 'consent_id': consent.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@firebase_login_required
@require_http_methods(["POST"])
def revoke_consent_view(request):
    uid = request.session.get('uid')
    email = request.session.get('email')
    username = request.session.get('username')

    try:
        consent_docs = db.collection('consent_records').where('firebase_uid', '==', uid).where('is_active', '==', True).order_by('given_at', direction=firestore.Query.DESCENDING).limit(1).stream()
        consent_doc = next(iter(consent_docs), None)

        if not consent_doc:
            messages.error(request, "Nenhum registro de consentimento encontrado.")
            return redirect('user_data')

        consent_data = consent_doc.to_dict()
        revoked_at = timezone.now()

        db.collection('consent_records').document(consent_doc.id).update({
            'revoked_at': revoked_at,
            'is_active': False,
        })

        registrar_log_firebase(uid, username, "Consentimento Revogado", get_client_ip(request))

        html_msg = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
            <div style="background: #1a182e; padding: 25px; text-align: center; color: white;">
                <h2>Smarko Security</h2>
            </div>
            <div style="padding: 40px; background: white;">
                <p>Olá,</p>
                <p>Seu consentimento foi revogado em <strong>{revoked_at.strftime('%d/%m/%Y às %H:%M')}</strong>.</p>
                <p>Deixaremos de processar dados para as finalidades anteriormente consentidas.</p>
                <p style="color: #666; font-size: 12px;">Se não foi você, entre em contato imediatamente.</p>
            </div>
        </div>
        """

        send_mail(
            "Smarko - Confirmação de Revogação de Consentimento",
            f"Seu consentimento foi revogado em {revoked_at}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_msg
        )

        messages.success(request, "Seu consentimento foi revogado com sucesso. Enviamos um email de confirmação.")
        return redirect('user_data')
    except Exception as e:
        messages.error(request, f"Erro ao revogar consentimento: {str(e)}")
        return redirect('user_data')

@firebase_login_required
@require_http_methods(["POST"])
def request_account_deletion_view(request):
    uid = request.session.get('uid')
    email = request.session.get('email')
    username = request.session.get('username')

    try:
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

        html_msg = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #dc3545; padding: 25px; text-align: center; color: white;">
                <h2>Account Deletion Request</h2>
            </div>
            <div style="padding: 40px; background: white;">
                <p>Olá {username},</p>
                <p>Recebemos sua solicitação de exclusão de conta.</p>
                <p><strong>Sua conta será deletada em 30 dias</strong> ({deletion_scheduled_for.strftime('%d/%m/%Y')}).</p>
                <p>Se mudou de ideia, clique abaixo para cancelar:</p>
                <a href="{cancel_url}" style="background: #1a182e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Cancelar Exclusão</a>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">
                    Se você não fez esta solicitação, ignore este email ou entre em contato conosco.
                </p>
            </div>
        </div>
        """

        send_mail(
            "Smarko - Account Deletion Request",
            f"Sua conta será deletada em 30 dias",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_msg
        )

        registrar_log_firebase(uid, username, "Exclusão de Conta Solicitada (30 dias)", get_client_ip(request))

        messages.success(request, "Solicitação de exclusão enviada. Você tem 30 dias para cancelar.")
        return redirect('user_data')
    except Exception as e:
        messages.error(request, f"Erro ao solicitar exclusão: {str(e)}")
        return redirect('user_data')

@require_http_methods(["GET"])
def cancel_account_deletion_view(request):
    token = request.GET.get('token')

    if not token:
        messages.error(request, "Token inválido.")
        return redirect('login')

    try:
        deletion_docs = db.collection('account_deletion_requests').where('confirmation_token', '==', token).limit(1).stream()
        deletion_doc = next(iter(deletion_docs), None)

        if not deletion_doc:
            messages.error(request, "Token não encontrado.")
            return redirect('login')

        deletion_data = deletion_doc.to_dict()

        if deletion_data.get('status') != 'pending':
            messages.error(request, "Esta solicitação já foi processada.")
            return redirect('login')

        db.collection('account_deletion_requests').document(deletion_doc.id).update({
            'status': 'canceled'
        })

        registrar_log_firebase(
            deletion_data.get('firebase_uid'),
            deletion_data.get('email'),
            "Exclusão de Conta Cancelada",
            get_client_ip(request)
        )

        messages.success(request, "Exclusão de conta cancelada. Sua conta está segura.")
        return redirect('login')
    except Exception as e:
        messages.error(request, f"Erro ao cancelar exclusão: {str(e)}")
        return redirect('login')

def update_consent_view(request):
    uid = request.session.get('pending_consent_uid')
    email = request.session.get('email')

    if not uid:
        return redirect('login')

    if request.method == "GET":
        try:
            purpose_docs = db.collection('data_purposes').stream()
            purposes = [doc.to_dict() for doc in purpose_docs]
        except:
            purposes = []

        context = {
            'purposes': purposes,
            'user_email': email,
        }
        return render(request, 'Smarko_App/update_consent.html', context)

    if request.method == "POST":
        try:
            accepted_privacy = request.POST.get('accepted_privacy') == 'on'
            accepted_terms = request.POST.get('accepted_terms') == 'on'


            if not accepted_privacy or not accepted_terms:
                try:
                    purpose_docs = db.collection('data_purposes').stream()
                    purposes = [doc.to_dict() for doc in purpose_docs]
                except:
                    purposes = []

                messages.error(request, "Você deve aceitar a Política de Privacidade e os Termos de Uso.")
                return render(request, 'Smarko_App/update_consent.html', {
                    'purposes': purposes,
                    'user_email': email,
                })

            purposes = request.POST.getlist('purpose_ids')
            version_info = get_current_policy_version()


            db.collection('consent_records').document(f"{uid}_consent").set({
                'firebase_uid': uid,
                'email': email,
                'version': version_info.get('version'),
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'accepted_terms': accepted_terms,
                'accepted_privacy': accepted_privacy,
                'is_active': True,
                'purposes': purposes if purposes else [],
                'given_at': firestore.SERVER_TIMESTAMP,
            })

            registrar_log_firebase(uid, email, f"Consentimento Atualizado v{version_info.get('version')}", get_client_ip(request))

            if 'pending_consent_uid' in request.session:
                del request.session['pending_consent_uid']

            messages.success(request, "Consent saved successfully. Welcome to Smarko.")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Erro ao atualizar consentimento: {str(e)}")
            try:
                purpose_docs = db.collection('data_purposes').stream()
                purposes = [doc.to_dict() for doc in purpose_docs]
            except:
                purposes = []
            return render(request, 'Smarko_App/update_consent.html', {
                'purposes': purposes,
                'user_email': email,
            })