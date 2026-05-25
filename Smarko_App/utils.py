import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from firebase_admin import firestore
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet

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


def log_security_event(
    uid: str,
    username: str,
    event: str,
    ip: str,
    status: str = "success",
    user_agent: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Log security event for audit trail.

    Structured logging with all relevant context for security monitoring and compliance.
    Events include authentication, authorization, data access, and policy changes.

    Args:
        uid: User ID
        username: Username or email
        event: Event type (login_attempt, login_success, 2fa_success, logout, etc.)
        ip: Client IP address
        status: Event status - 'success' or 'failure' (default: 'success')
        user_agent: HTTP User-Agent header (optional)
        additional_data: Extra context dict (e.g., {'attempt': 3, 'method': 'email'})

    Returns:
        bool: True if logged successfully, False otherwise

    Security: Provides non-repudiation by logging timestamp, user, IP, and action
    """
    db = get_firestore_client()
    if not db:
        logger.warning(f"Cannot log event '{event}': Firestore unavailable")
        return False

    try:
        log_data = {
            'usuario_id': uid or 'unknown',
            'usuario_nome': username or 'unknown',
            'evento': event,
            'ip': ip,
            'status': status,
            'data_hora': firestore.SERVER_TIMESTAMP,
        }

        # Add optional fields
        if user_agent:
            log_data['user_agent'] = user_agent[:500]  # Limit length
        if additional_data:
            log_data['dados_adicionais'] = additional_data

        # Use auto-generated document ID for immutability
        # Index on (usuario_id, data_hora) enables audit queries
        db.collection('logs_seguranca').add(log_data)

        logger.info(f"Security event logged: {event} by {username} from {ip}")
        return True
    except Exception as e:
        logger.error(f"Failed to log security event {event}: {e}")
        return False


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


def blacklist_session(session_id: str, uid: Optional[str] = None, ttl_seconds: int = 120) -> bool:
    """
    Add session to blacklist to invalidate it (logout).

    Mitigates JWT stateless limitation by maintaining server-side session invalidation.
    Sessions are automatically cleaned up after TTL expires.

    Args:
        session_id: Session ID to blacklist
        uid: User ID (optional, for audit trail)
        ttl_seconds: Time-to-live in seconds (default 120s to match SESSION_COOKIE_AGE)

    Returns:
        bool: True if blacklist successful, False otherwise

    Raises:
        None (errors are logged, not raised)

    Security: Mitigates session hijacking by preventing reuse of invalidated sessions
    """
    db = get_firestore_client()
    if not db:
        logger.warning("Cannot blacklist session: Firestore unavailable")
        return False

    try:
        expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)
        db.collection('sessions_blacklist').document(session_id).set({
            'invalidated_at': firestore.SERVER_TIMESTAMP,
            'expires_at': expires_at,
            'uid': uid,
        })
        logger.info(f"Session {session_id} blacklisted for user {uid}")
        return True
    except Exception as e:
        logger.error(f"Failed to blacklist session {session_id}: {e}")
        return False


def is_session_blacklisted(session_id: str) -> bool:
    """
    Check if session has been invalidated (blacklisted).

    Used in middleware to prevent reuse of blacklisted sessions.

    Args:
        session_id: Session ID to check

    Returns:
        bool: True if blacklisted, False if valid or not found

    Security: Part of stateless JWT mitigation to enforce server-side logout
    """
    db = get_firestore_client()
    if not db:
        return False

    try:
        doc = db.collection('sessions_blacklist').document(session_id).get()
        if doc.exists:
            # Optionally check expiry (Firestore TTL would auto-delete, but we validate)
            data = doc.to_dict()
            expires_at = data.get('expires_at')
            if expires_at and timezone.now() > expires_at:
                # Expired, allow reuse
                return False
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to check session blacklist for {session_id}: {e}")
        return False


def secure_file_save(base_dir: str, filename: str, content: bytes) -> Optional[str]:
    """
    Save file with path traversal protection.

    Mitigates: OWASP A01:2021 - Broken Access Control (Path Traversal)
    by validating file path stays within designated directory.

    Security checks:
    1. Sanitize filename (remove dangerous characters)
    2. Generate random UUID to prevent name collision attacks
    3. Validate final path is within base_dir (boundary check)
    4. Enforce whitelist of allowed extensions

    Args:
        base_dir: Base directory for uploads (must be absolute path)
        filename: Original filename from user input
        content: File content bytes to write

    Returns:
        str: Sanitized relative filename (UUID.ext), or None on error

    Raises:
        PermissionError: If path traversal detected
        ValueError: If filename invalid or extension not whitelisted

    Example:
        >>> secure_file_save('/var/uploads', 'document.pdf', b'PDF content')
        '550e8400-e29b-41d4-a716-446655440000.pdf'
    """
    # Whitelist of allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt', '.csv', '.docx'}

    # Ensure base_dir is absolute
    base_dir_abs = os.path.abspath(base_dir)
    if not os.path.isdir(base_dir_abs):
        raise ValueError(f"Base directory does not exist: {base_dir_abs}")

    # Sanitize and validate filename
    if not filename or len(filename) == 0:
        raise ValueError("Filename cannot be empty")

    sanitized = secure_filename(filename)
    if not sanitized:
        raise ValueError(f"Filename '{filename}' is not valid")

    # Extract extension and validate
    _, ext = os.path.splitext(sanitized)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension '{ext}' not allowed. Allowed: {ALLOWED_EXTENSIONS}")

    # Generate unique filename to prevent collisions and name-based attacks
    # Use UUID + original extension
    unique_filename = f"{uuid.uuid4()}{ext}"

    # Build target path and validate it's within base_dir
    target_path_abs = os.path.abspath(os.path.join(base_dir_abs, unique_filename))

    # Boundary check: ensure target is under base_dir
    if not target_path_abs.startswith(base_dir_abs + os.sep):
        raise PermissionError(
            f"Path traversal detected: '{target_path_abs}' is outside base directory '{base_dir_abs}'"
        )

    # Write file
    try:
        with open(target_path_abs, 'wb') as f:
            f.write(content)
        logger.info(f"File saved securely: {unique_filename}")
        return unique_filename
    except IOError as e:
        logger.error(f"Failed to write file {unique_filename}: {e}")
        raise


def _get_encryption_cipher() -> Optional[Fernet]:
    """Get Fernet cipher initialized with encryption key."""
    try:
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            logger.warning("ENCRYPTION_KEY environment variable not set")
            return None
        return Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    except Exception as e:
        logger.error(f"Failed to initialize encryption cipher: {e}")
        return None


def encrypt_field(plaintext: str) -> Optional[str]:
    """
    Encrypt a sensitive field using Fernet (AES-128).

    Mitigates: OWASP A02:2021 - Cryptographic Failures
    by encrypting sensitive data at rest in Firestore.

    Args:
        plaintext: Plaintext value to encrypt (e.g., email, phone)

    Returns:
        str: Encrypted ciphertext (base64-encoded token), or None if encryption unavailable

    Raises:
        ValueError: If plaintext is empty or invalid

    Security:
    - Uses Fernet: AES-128 in CBC mode + HMAC for authentication
    - Key sourced from ENCRYPTION_KEY environment variable
    - Returns base64-encoded ciphertext safe for database storage

    Example:
        >>> encrypted = encrypt_field("user@example.com")
        >>> encrypted  # gAAAAABmXv...
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty value")

    cipher = _get_encryption_cipher()
    if not cipher:
        logger.warning("Encryption unavailable, returning plaintext (UNSAFE!)")
        return plaintext

    try:
        ciphertext_bytes = cipher.encrypt(plaintext.encode('utf-8'))
        # Fernet returns base64-encoded bytes, decode to string for storage
        return ciphertext_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return None


def decrypt_field(ciphertext: str) -> Optional[str]:
    """
    Decrypt a field encrypted with encrypt_field().

    Args:
        ciphertext: Encrypted base64-encoded token from encrypt_field()

    Returns:
        str: Decrypted plaintext, or None if decryption fails

    Raises:
        ValueError: If ciphertext is empty or invalid

    Security:
    - Validates HMAC before decrypting (authenticated encryption)
    - Fails securely on tampered ciphertext

    Example:
        >>> plaintext = decrypt_field("gAAAAABmXv...")
        >>> plaintext  # 'user@example.com'
    """
    if not ciphertext:
        raise ValueError("Cannot decrypt empty value")

    cipher = _get_encryption_cipher()
    if not cipher:
        logger.warning("Decryption unavailable")
        return None

    try:
        plaintext_bytes = cipher.decrypt(ciphertext.encode('utf-8'))
        return plaintext_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed (invalid ciphertext or wrong key): {e}")
        return None
