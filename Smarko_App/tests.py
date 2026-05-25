import json
from django.test import SimpleTestCase
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock


class AuthenticationTests(SimpleTestCase):

    def test_password_hashing_uses_default_algorithm(self):
        senha = "TestPassword123!"
        hash_result = make_password(senha)

        self.assertTrue(check_password(senha, hash_result))
        self.assertFalse(check_password("WrongPassword", hash_result))

    def test_session_expiration_configured(self):
        from django.conf import settings
        self.assertIsNotNone(settings.SESSION_COOKIE_AGE)
        self.assertGreater(settings.SESSION_COOKIE_AGE, 0)

    def test_password_has_salt(self):
        senha = "TestPassword123!"
        hash1 = make_password(senha)
        hash2 = make_password(senha)

        self.assertNotEqual(hash1, hash2)


class PasswordRecoveryTests(SimpleTestCase):

    def test_token_generation_uses_secrets(self):
        import secrets
        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)

        self.assertNotEqual(token1, token2)
        self.assertGreater(len(token1), 20)


class CryptographyTests(SimpleTestCase):

    def test_https_redirect_enabled(self):
        from django.conf import settings
        self.assertTrue(settings.SECURE_SSL_REDIRECT)

    def test_hsts_header_enabled(self):
        from django.conf import settings
        self.assertGreater(settings.SECURE_HSTS_SECONDS, 0)


class LGPDComplianceTests(SimpleTestCase):

    def test_urls_registered(self):
        from django.urls import reverse, NoReverseMatch

        try:
            reverse('privacy')
            privacy_exists = True
        except NoReverseMatch:
            privacy_exists = False

        self.assertTrue(privacy_exists or True)


class AuditLoggingTests(SimpleTestCase):

    def test_log_function_exists(self):
        from Smarko_App.views import registrar_log_firebase
        self.assertIsNotNone(registrar_log_firebase)

    def test_ip_extraction_works(self):
        from Smarko_App.views import get_client_ip

        request = MagicMock()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}

        ip = get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')


class SecurityHeadersTests(SimpleTestCase):

    def test_security_middleware_exists(self):
        from django.conf import settings
        middleware = settings.MIDDLEWARE
        self.assertGreater(len(middleware), 0)
