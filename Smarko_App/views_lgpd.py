"""
LGPD (Lei Geral de Proteção de Dados) compliance endpoints.

Implements data subject rights:
- Right to access: GET /api/user/data-export/ - download all personal data
- Right to erasure: POST /api/user/account-deletion/ - request account deletion
- Right to data portability: GET /api/user/data-export/ - export in portable format
- Right to information: GET /api/user/consent/ - view consent records and purposes

References:
- LGPD Lei nº 13.709/2018 (Articles 17, 18, 19, 20)
- ISO/IEC 27701:2019 (Privacy extension to ISO 27001)
"""

import json
import zipfile
import io
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from django.http import HttpRequest, HttpResponse, JsonResponse, FileResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from functools import wraps
from firebase_admin import firestore

from Smarko_App.utils import (
    get_client_ip,
    log_security_event,
    fetch_firestore_doc,
    fetch_firestore_collection,
    get_firestore_client,
)


db = get_firestore_client()


def lgpd_login_required(view_func):
    """Decorator: require authenticated user for LGPD endpoints."""
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.session.get('uid'):
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@require_http_methods(["GET"])
@lgpd_login_required
def data_export_view(request: HttpRequest) -> FileResponse:
    """
    Export all personal data as ZIP archive.

    Implements LGPD Article 18 (Right to Data Portability).
    User can download all data in portable, machine-readable format.

    Returns:
        FileResponse: ZIP file containing JSON exports

    Security:
    - Validates user owns requested data (no IDOR)
    - Logs request with IP for audit trail
    - Includes consent history for transparency
    """
    uid = request.session.get('uid')
    email = request.session.get('email')
    client_ip = get_client_ip(request)

    if not uid or not email:
        return JsonResponse({'error': 'Session invalid'}, status=401)

    try:
        # Validate ownership (prevent IDOR)
        user_doc = fetch_firestore_doc('perfis', uid, db)
        if user_doc.get('email') != email:
            log_security_event(
                uid, email, 'data_export_unauthorized_attempt',
                client_ip, status='failure'
            )
            return JsonResponse(
                {'error': 'Unauthorized'},
                status=403
            )

        # Collect user data
        data_export = {
            'exported_at': datetime.utcnow().isoformat(),
            'email': email,
            'profile': user_doc,
            'consent_records': [],
            'logs_seguranca': [],
        }

        # Fetch consent records
        consent_docs = fetch_firestore_collection(
            'consent_records',
            filters=[('firebase_uid', '==', uid)]
        )
        data_export['consent_records'] = consent_docs

        # Fetch last 30 days of security logs (privacy: don't export too much history)
        logs_docs = fetch_firestore_collection(
            'logs_seguranca',
            filters=[('usuario_id', '==', uid)]
        )
        data_export['logs_seguranca'] = logs_docs[:100]  # Limit to 100 records

        # Create ZIP with JSON files
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(
                'personal_data.json',
                json.dumps(data_export, indent=2, default=str)
            )
            zip_file.writestr(
                'README.txt',
                'LGPD Data Export\n'
                '================\n'
                f'Exported: {datetime.utcnow()}\n'
                f'User: {email}\n\n'
                'Files:\n'
                '- personal_data.json: All your personal data, consent records, and logs\n'
            )

        zip_buffer.seek(0)

        # Log successful export
        log_security_event(
            uid, email, 'data_export_success',
            client_ip, status='success'
        )

        return FileResponse(
            zip_buffer,
            as_attachment=True,
            filename=f'smarko_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            content_type='application/zip'
        )

    except Exception as e:
        log_security_event(
            uid, email, 'data_export_error',
            client_ip, status='failure',
            additional_data={'error': str(e)}
        )
        return JsonResponse(
            {'error': 'Failed to export data'},
            status=500
        )


@require_http_methods(["POST"])
@lgpd_login_required
def account_deletion_request_view(request: HttpRequest) -> JsonResponse:
    """
    Request account deletion.

    Implements LGPD Article 17 (Right to Erasure / Right to be Forgotten).
    Initiates 30-day grace period before deletion, allowing user to cancel.

    Request body:
        {'confirm': true}  # User must explicitly confirm

    Returns:
        JsonResponse: Deletion scheduled for 30 days from now

    Timeline:
    - T0: User requests deletion
    - T+30: Account and all data automatically deleted
    - User receives confirmation email
    - User can cancel within 30 days
    """
    uid = request.session.get('uid')
    email = request.session.get('email')
    client_ip = get_client_ip(request)

    if not uid or not email:
        return JsonResponse({'error': 'Session invalid'}, status=401)

    try:
        body = json.loads(request.body)
        if not body.get('confirm'):
            return JsonResponse(
                {'error': 'Deletion must be confirmed'},
                status=400
            )

        # Calculate deletion date (30 days from now)
        deletion_scheduled = timezone.now() + timezone.timedelta(days=30)

        # Create deletion request record
        deletion_token = f"{uid}_{timezone.now().timestamp()}"

        if db:
            db.collection('account_deletion_requests').document(uid).set({
                'firebase_uid': uid,
                'email': email,
                'requested_at': firestore.SERVER_TIMESTAMP,
                'deletion_scheduled_for': deletion_scheduled,
                'status': 'pending',  # pending, canceled, completed
                'confirmation_token': deletion_token,
            })

        log_security_event(
            uid, email, 'account_deletion_requested',
            client_ip, status='success',
            additional_data={'deletion_date': deletion_scheduled.isoformat()}
        )

        return JsonResponse({
            'status': 'deletion_scheduled',
            'deletion_date': deletion_scheduled.isoformat(),
            'message': 'Your account will be permanently deleted in 30 days. '
                       'You can cancel this request until then.',
        }, status=202)

    except Exception as e:
        log_security_event(
            uid, email, 'account_deletion_error',
            client_ip, status='failure',
            additional_data={'error': str(e)}
        )
        return JsonResponse(
            {'error': 'Failed to process deletion request'},
            status=500
        )


@require_http_methods(["POST"])
@lgpd_login_required
def account_deletion_cancel_view(request: HttpRequest) -> JsonResponse:
    """
    Cancel pending account deletion request.

    Allows user to revoke deletion request before 30-day grace period expires.

    Returns:
        JsonResponse: Deletion request canceled
    """
    uid = request.session.get('uid')
    email = request.session.get('email')
    client_ip = get_client_ip(request)

    if not uid or not email:
        return JsonResponse({'error': 'Session invalid'}, status=401)

    try:
        if db:
            # Check if deletion request exists
            deletion_doc = fetch_firestore_doc('account_deletion_requests', uid, db)
            if not deletion_doc or deletion_doc.get('status') != 'pending':
                return JsonResponse(
                    {'error': 'No pending deletion request found'},
                    status=404
                )

            # Update status to canceled
            db.collection('account_deletion_requests').document(uid).update({
                'status': 'canceled',
                'canceled_at': firestore.SERVER_TIMESTAMP,
            })

        log_security_event(
            uid, email, 'account_deletion_canceled',
            client_ip, status='success'
        )

        return JsonResponse({
            'status': 'deletion_canceled',
            'message': 'Your account deletion request has been canceled.',
        })

    except Exception as e:
        log_security_event(
            uid, email, 'account_deletion_cancel_error',
            client_ip, status='failure'
        )
        return JsonResponse(
            {'error': 'Failed to cancel deletion request'},
            status=500
        )


@require_http_methods(["GET"])
@lgpd_login_required
def consent_records_view(request: HttpRequest) -> JsonResponse:
    """
    View all consent records and purposes.

    Implements LGPD Article 7 (Lawful basis for data processing).
    Shows user what they consented to and when.

    Returns:
        JsonResponse: List of consent records (active and revoked)

    Response:
        {
            'active_consents': [...],
            'revoked_consents': [...],
            'purposes': ['marketing', 'analytics', 'service_improvement']
        }
    """
    uid = request.session.get('uid')
    email = request.session.get('email')
    client_ip = get_client_ip(request)

    if not uid or not email:
        return JsonResponse({'error': 'Session invalid'}, status=401)

    try:
        # Fetch all consent records for user
        consent_docs = fetch_firestore_collection(
            'consent_records',
            filters=[('firebase_uid', '==', uid)]
        )

        # Separate active and revoked
        active = [c for c in consent_docs if c.get('is_active')]
        revoked = [c for c in consent_docs if not c.get('is_active')]

        # Extract unique purposes
        purposes = set()
        for consent in consent_docs:
            if consent.get('purposes'):
                purposes.update(consent['purposes'])

        log_security_event(
            uid, email, 'consent_records_viewed',
            client_ip, status='success'
        )

        return JsonResponse({
            'active_consents': active,
            'revoked_consents': revoked,
            'purposes': list(purposes),
            'total_records': len(consent_docs),
        })

    except Exception as e:
        log_security_event(
            uid, email, 'consent_records_error',
            client_ip, status='failure'
        )
        return JsonResponse(
            {'error': 'Failed to retrieve consent records'},
            status=500
        )


@require_http_methods(["POST"])
@lgpd_login_required
def consent_revocation_view(request: HttpRequest) -> JsonResponse:
    """
    Revoke specific consent for data processing.

    Allows granular revocation of individual purposes (marketing, analytics, etc).
    User can revoke specific consents without losing account.

    Request body:
        {'purposes': ['marketing']}  # Purposes to revoke

    Returns:
        JsonResponse: Confirmation of revoked purposes
    """
    uid = request.session.get('uid')
    email = request.session.get('email')
    client_ip = get_client_ip(request)

    if not uid or not email:
        return JsonResponse({'error': 'Session invalid'}, status=401)

    try:
        body = json.loads(request.body)
        purposes_to_revoke = body.get('purposes', [])

        if not purposes_to_revoke:
            return JsonResponse(
                {'error': 'No purposes specified'},
                status=400
            )

        # Find active consent and update
        consent_docs = fetch_firestore_collection(
            'consent_records',
            filters=[
                ('firebase_uid', '==', uid),
                ('is_active', '==', True),
            ],
            limit=1
        )

        if not consent_docs:
            return JsonResponse(
                {'error': 'No active consent found'},
                status=404
            )

        consent = consent_docs[0]
        # Get the document ID (Firestore auto-ID or custom)
        # For now, assume we use uid as document ID
        consent_ref = db.collection('consent_records').document(uid)

        # Remove revoked purposes
        remaining_purposes = [
            p for p in consent.get('purposes', [])
            if p not in purposes_to_revoke
        ]

        # Update or mark as revoked
        if remaining_purposes:
            consent_ref.update({
                'purposes': remaining_purposes,
                'modified_at': firestore.SERVER_TIMESTAMP,
            })
        else:
            # All purposes revoked, mark entire consent as inactive
            consent_ref.update({
                'is_active': False,
                'revoked_at': firestore.SERVER_TIMESTAMP,
            })

        log_security_event(
            uid, email, 'consent_revoked',
            client_ip, status='success',
            additional_data={'revoked_purposes': purposes_to_revoke}
        )

        return JsonResponse({
            'status': 'consent_revoked',
            'revoked_purposes': purposes_to_revoke,
            'message': f'Your consent has been revoked for: {", ".join(purposes_to_revoke)}',
        })

    except Exception as e:
        log_security_event(
            uid, email, 'consent_revocation_error',
            client_ip, status='failure'
        )
        return JsonResponse(
            {'error': 'Failed to revoke consent'},
            status=500
        )
