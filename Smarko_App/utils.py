import logging
from typing import Any, Dict, List, Optional, Tuple
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.contrib import messages
from firebase_admin import firestore

logger = logging.getLogger(__name__)


def get_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR', '')


def get_firestore_client() -> Optional[Any]:
    try:
        return firestore.client()
    except Exception:
        return None


def log_security_event(uid: str, username: str, event: str, ip: str) -> None:
    db = get_firestore_client()
    if not db:
        return
    try:
        db.collection('logs_seguranca').add({
            'usuario_id': uid,
            'usuario_nome': username,
            'evento': event,
            'ip': ip,
            'data_hora': firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        logger.error(f"Failed to log security event {event}: {e}")


def fetch_firestore_doc(collection: str, doc_id: str, db: Any) -> Dict[str, Any]:
    if not db:
        return {}
    try:
        doc = db.collection(collection).document(doc_id).get()
        return doc.to_dict() or {}
    except Exception as e:
        logger.warning(f"Failed to fetch {collection}/{doc_id}: {e}")
        return {}


def fetch_firestore_collection(
    collection: str,
    filters: Optional[List[Tuple[str, str, Any]]] = None,
    order_by: Optional[Tuple[str, str]] = None,
    limit: Optional[int] = None,
    db: Optional[Any] = None
) -> List[Dict[str, Any]]:
    if db is None:
        db = get_firestore_client()
    if not db:
        return []

    try:
        query = db.collection(collection)

        if filters:
            for field, operator, value in filters:
                query = query.where(field, operator, value)

        if order_by:
            field, direction = order_by
            query = query.order_by(field, direction=direction)

        if limit:
            query = query.limit(limit)

        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.warning(f"Failed to fetch {collection}: {e}")
        return []


def get_session_user(request: HttpRequest) -> Tuple[Optional[str], Optional[str]]:
    uid = request.session.get('uid')
    email = request.session.get('email')
    return uid, email


def validate_password_match(pwd1: str, pwd2: str) -> bool:
    return pwd1 == pwd2


def render_error(
    request: HttpRequest,
    template: str,
    error_msg: str,
    context: Optional[Dict[str, Any]] = None
) -> HttpResponse:
    if context is None:
        context = {}
    messages.error(request, error_msg)
    return render(request, template, context)
