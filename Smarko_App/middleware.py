"""
Security middlewares for rate limiting, request validation, and attack mitigation.

This module implements defense-in-depth security controls:
- Rate limiting via Token Bucket pattern
- Payload size validation (prevents DoS via large uploads)
- Request logging for security audit trails
"""

import time
import logging
from typing import Optional, Dict, Any
from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect
from django.utils.timezone import now as django_now
from datetime import timedelta
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Implements Token Bucket rate limiting for critical endpoints.

    Mitigates OWASP A07:2021 - Identification and Authentication Failures
    by limiting brute force attempts on auth endpoints.

    Configuration:
    - login, register, reset_password: 5 requests per minute per IP
    - Default: 100 requests per minute per IP

    Storage: Firestore collection 'rate_limit_buckets' for distributed environments
    """

    # Rate limit rules: endpoint pattern -> (requests_per_minute, window_seconds)
    RATE_LIMIT_RULES: Dict[str, tuple] = {
        '/login/': (5, 60),
        '/register/': (3, 60),
        '/reset_password/': (3, 60),
        '/reset_confirm/': (5, 300),  # 5 requests per 5 minutes
        '/verificar-2fa/': (10, 60),  # More lenient for 2FA attempts
    }

    DEFAULT_LIMIT = (100, 60)  # 100 requests per minute for other endpoints

    def __init__(self, get_response):
        self.get_response = get_response
        try:
            self.db = firestore.client()
        except Exception as e:
            logger.warning(f"Firestore not available for rate limiting: {e}")
            self.db = None

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request through rate limiting middleware."""
        path = request.path

        # Check if this endpoint needs rate limiting
        is_rate_limited = any(path.startswith(endpoint) for endpoint in self.RATE_LIMIT_RULES)

        if is_rate_limited or path.startswith('/api/'):
            # Get rate limit config for this endpoint
            limit_config = self.RATE_LIMIT_RULES.get(path, self.DEFAULT_LIMIT)
            max_requests, window_seconds = limit_config

            # Extract client IP (respects X-Forwarded-For for proxies)
            client_ip = self._get_client_ip(request)

            # Check rate limit
            if not self._check_rate_limit(client_ip, path, max_requests, window_seconds):
                logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
                return HttpResponse(
                    "Too Many Requests. Please try again later.",
                    status=429,
                    content_type="text/plain"
                )

        response = self.get_response(request)
        return response

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP, respecting proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def _check_rate_limit(
        self,
        client_ip: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if client has exceeded rate limit using Firestore-backed Token Bucket.

        Args:
            client_ip: Client IP address
            endpoint: Request path
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed, False if rate limited
        """
        if not self.db:
            # If Firestore unavailable, allow request (fail open)
            return True

        try:
            bucket_id = f"{client_ip}:{endpoint}"
            bucket_ref = self.db.collection('rate_limit_buckets').document(bucket_id)
            bucket_doc = bucket_ref.get()

            current_time = django_now()

            if not bucket_doc.exists:
                # New bucket: initialize with max_requests tokens
                bucket_ref.set({
                    'tokens': max_requests - 1,  # Consume 1 token for this request
                    'last_refill': current_time,
                    'endpoint': endpoint,
                    'client_ip': client_ip,
                    'created_at': current_time,
                })
                return True

            bucket_data = bucket_doc.to_dict()
            last_refill = bucket_data.get('last_refill')
            tokens = bucket_data.get('tokens', 0)

            # Calculate elapsed time and refill tokens
            if isinstance(last_refill, int):
                # Handle unix timestamp
                elapsed_seconds = (current_time.timestamp() - last_refill) if isinstance(last_refill, (int, float)) else (current_time - last_refill).total_seconds()
            else:
                elapsed_seconds = (current_time - last_refill).total_seconds()

            # Refill rate: max_requests tokens per window_seconds
            refill_rate = max_requests / window_seconds
            tokens = min(max_requests, tokens + (refill_rate * elapsed_seconds))

            if tokens >= 1:
                # Consume 1 token
                bucket_ref.update({
                    'tokens': tokens - 1,
                    'last_refill': current_time,
                })
                return True
            else:
                # No tokens available
                return False

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open: allow request if we can't check limit
            return True


class PayloadSizeMiddleware:
    """
    Validates request payload size to prevent DoS via large uploads.

    Mitigates: OWASP A08:2021 - Software and Data Integrity Failures
    and resource exhaustion attacks.

    Limit: 5MB per request (configurable)
    """

    MAX_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5MB

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Check request payload size."""
        content_length = request.META.get('CONTENT_LENGTH')

        if content_length:
            try:
                content_size = int(content_length)
                if content_size > self.MAX_PAYLOAD_SIZE:
                    logger.warning(
                        f"Payload too large from {request.META.get('REMOTE_ADDR')}: "
                        f"{content_size} bytes (max {self.MAX_PAYLOAD_SIZE})"
                    )
                    return HttpResponse(
                        f"Payload Too Large. Maximum {self.MAX_PAYLOAD_SIZE // (1024*1024)}MB allowed.",
                        status=413,
                        content_type="text/plain"
                    )
            except ValueError:
                logger.warning(f"Invalid CONTENT_LENGTH header: {content_length}")

        response = self.get_response(request)
        return response


class SessionBlacklistMiddleware:
    """
    Validates that session is not blacklisted (invalidated).

    Enforces server-side logout by preventing use of invalidated sessions.
    Mitigates: JWT stateless limitation (OWASP A07:2021)

    Workflow:
    1. User calls /logout/ -> session added to blacklist
    2. Next request with this session_id -> middleware rejects it (401)
    3. User redirected to login
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Import here to avoid circular imports
        from Smarko_App.utils import is_session_blacklisted
        self.is_session_blacklisted = is_session_blacklisted

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Check if session is blacklisted before processing request."""
        session_id = request.session.session_key

        if session_id and self.is_session_blacklisted(session_id):
            # Session has been invalidated, flush it and return 401
            request.session.flush()
            return HttpResponse(
                "Session Invalidated. Please login again.",
                status=401,
                content_type="text/plain"
            )

        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """
    Adds security headers to all responses.

    Mitigates: OWASP A01:2021, A05:2021 (XSS, Clickjacking)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'

        # Referrer policy (privacy)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response
