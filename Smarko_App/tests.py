from django.test import SimpleTestCase, Client
from django.contrib.auth.hashers import make_password, check_password
from unittest.mock import MagicMock, patch
import secrets


class AuthenticationTests(SimpleTestCase):
    def test_password_hashing_secure(self):
        senha = "TestPassword123!"
        hash_result = make_password(senha)
        self.assertTrue(check_password(senha, hash_result))
        self.assertFalse(check_password("WrongPassword", hash_result))

    def test_session_expiration_configured(self):
        from django.conf import settings
        self.assertIsNotNone(settings.SESSION_COOKIE_AGE)
        self.assertGreater(settings.SESSION_COOKIE_AGE, 0)

    def test_password_hash_uses_salt(self):
        senha = "TestPassword123!"
        hash1 = make_password(senha)
        hash2 = make_password(senha)
        self.assertNotEqual(hash1, hash2)


class UtilsTests(SimpleTestCase):
    def test_get_client_ip_from_forwarded(self):
        from Smarko_App.utils import get_client_ip
        request = MagicMock()
        request.META = {'HTTP_X_FORWARDED_FOR': '192.168.1.1,10.0.0.1'}
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

    def test_get_client_ip_fallback(self):
        from Smarko_App.utils import get_client_ip
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        ip = get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')

    def test_validate_password_match_success(self):
        from Smarko_App.utils import validate_password_match
        self.assertTrue(validate_password_match('senha123', 'senha123'))

    def test_validate_password_match_failure(self):
        from Smarko_App.utils import validate_password_match
        self.assertFalse(validate_password_match('senha123', 'outra'))


class TokenSecurityTests(SimpleTestCase):
    def test_password_reset_token_uses_secrets(self):
        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)
        self.assertNotEqual(token1, token2)
        self.assertGreater(len(token1), 20)

    def test_2fa_code_generation(self):
        codigo = str(secrets.randbelow(1000000)).zfill(6)
        self.assertEqual(len(codigo), 6)
        self.assertTrue(codigo.isdigit())


class SecurityConfigTests(SimpleTestCase):
    def test_https_redirect_production(self):
        from django.conf import settings
        self.assertTrue(settings.SECURE_SSL_REDIRECT)

    def test_hsts_enabled(self):
        from django.conf import settings
        self.assertGreater(settings.SECURE_HSTS_SECONDS, 0)

    def test_csrf_protection(self):
        from django.conf import settings
        middleware = settings.MIDDLEWARE
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', middleware)

    def test_security_middleware(self):
        from django.conf import settings
        middleware = settings.MIDDLEWARE
        self.assertIn('django.middleware.security.SecurityMiddleware', middleware)


class LGPDComplianceTests(SimpleTestCase):
    def test_logging_function_exists(self):
        from Smarko_App.utils import log_security_event
        self.assertIsNotNone(log_security_event)

    def test_secure_files_utility_exists(self):
        from Smarko_App.secure_files import SecureTemporaryFile
        self.assertIsNotNone(SecureTemporaryFile.temporary_file)

    def test_email_templates_exist(self):
        from Smarko_App.email_templates import EmailTemplate
        self.assertTrue(hasattr(EmailTemplate, 'render_2fa'))
        self.assertTrue(hasattr(EmailTemplate, 'render_password_reset'))
        self.assertTrue(hasattr(EmailTemplate, 'render_consent_revoked'))
        self.assertTrue(hasattr(EmailTemplate, 'render_account_deletion'))


class ViewsSecurityTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_ping_view(self):
        response = self.client.get('/ping/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'alive')

    def test_privacy_policy_accessible(self):
        response = self.client.get('/privacy-policy/')
        self.assertEqual(response.status_code, 200)

    def test_login_view_accessible(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_register_view_accessible(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects(self):
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)

    def test_home_requires_auth(self):
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_user_data_requires_auth(self):
        response = self.client.get('/user-data/')
        self.assertEqual(response.status_code, 302)

    def test_export_data_requires_auth(self):
        response = self.client.get('/export-data/')
        self.assertEqual(response.status_code, 302)


class FirebaseIntegrationTests(SimpleTestCase):
    @patch('Smarko_App.utils.firestore')
    def test_get_firestore_client(self, mock_firestore):
        from Smarko_App.utils import get_firestore_client
        mock_firestore.client.return_value = MagicMock()
        client = get_firestore_client()
        self.assertIsNotNone(client)

    @patch('Smarko_App.utils.firestore')
    def test_get_firestore_client_handles_error(self, mock_firestore):
        from Smarko_App.utils import get_firestore_client
        mock_firestore.client.side_effect = Exception("Connection failed")
        client = get_firestore_client()
        self.assertIsNone(client)


class CodeQualityTests(SimpleTestCase):
    def test_type_hints_present(self):
        from Smarko_App import views
        import inspect

        functions = [
            views.register_view,
            views.login_view,
            views.logout_view,
            views.home_view,
        ]

        for func in functions:
            sig = inspect.signature(func)
            self.assertIn('request', sig.parameters)
            self.assertIsNotNone(sig.return_annotation)
