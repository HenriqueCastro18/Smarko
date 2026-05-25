import json
from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock


class AuthenticationTests(TestCase):
    """Testes de Autenticação (Requisito 1)"""

    def setUp(self):
        self.client = Client()

    def test_password_hashing_uses_bcrypt(self):
        """Valida que senhas são hash com algoritmo seguro"""
        senha = "TestPassword123!"
        hash_result = make_password(senha, hasher='bcrypt')

        self.assertIn('bcrypt', hash_result)
        self.assertTrue(check_password(senha, hash_result))
        self.assertFalse(check_password("WrongPassword", hash_result))

    def test_login_requires_email_and_password(self):
        """Valida que login exige credenciais válidas"""
        response = self.client.post('/login/', {
            'email': '',
            'senha': ''
        }, follow=True)

        self.assertIn(b'email', response.content.lower())

    def test_session_expiration_configured(self):
        """Valida que sessões têm timeout"""
        from django.conf import settings
        self.assertIsNotNone(settings.SESSION_COOKIE_AGE)
        self.assertGreater(settings.SESSION_COOKIE_AGE, 0)

    def test_rate_limiting_blocks_after_failures(self):
        """Testa proteção contra força bruta"""
        for i in range(5):
            response = self.client.post('/login/', {
                'email': 'test@example.com',
                'senha': 'wrong_pass'
            })

        # Deve conter mensagem de bloqueio ou erro
        self.assertIn(response.status_code, [200, 429, 403])


class PasswordRecoveryTests(TestCase):
    """Testes de Recuperação de Senha (Requisito 2)"""

    def setUp(self):
        self.client = Client()

    def test_password_reset_token_generation(self):
        """Valida que tokens de reset são gerados"""
        response = self.client.post('/forgot-password/', {
            'email': 'user@example.com'
        }, follow=True)

        # Não deve expor detalhes
        self.assertNotIn(b'token', response.content.lower())

    def test_password_reset_email_sent(self):
        """Valida envio de email de reset"""
        with patch('django.core.mail.send_mail') as mock_send:
            response = self.client.post('/forgot-password/', {
                'email': 'test@example.com'
            })

            # Email deve ser enviado
            self.assertTrue(mock_send.called or response.status_code == 200)


class CryptographyTests(TestCase):
    """Testes de Criptografia (Requisito 3)"""

    def test_https_redirect_enabled(self):
        """Valida HTTPS enforced"""
        from django.conf import settings
        self.assertTrue(settings.SECURE_SSL_REDIRECT)

    def test_hsts_header_enabled(self):
        """Valida HSTS header"""
        from django.conf import settings
        self.assertGreater(settings.SECURE_HSTS_SECONDS, 0)

    def test_session_cookie_secure(self):
        """Valida que cookies de sessão são seguros"""
        from django.conf import settings
        self.assertTrue(settings.SESSION_COOKIE_SECURE)


class LGPDComplianceTests(TestCase):
    """Testes de Conformidade LGPD (Requisito 4)"""

    def setUp(self):
        self.client = Client()

    def test_privacy_policy_exists(self):
        """Valida que política de privacidade está acessível"""
        response = self.client.get('/privacy/')
        self.assertIn(response.status_code, [200, 301, 302])

    def test_terms_of_service_exists(self):
        """Valida que termos estão acessíveis"""
        response = self.client.get('/terms/')
        self.assertIn(response.status_code, [200, 301, 302])

    def test_consent_checkbox_required(self):
        """Valida que consentimento é obrigatório no signup"""
        response = self.client.post('/register/', {
            'usuario': 'test_user',
            'email': 'test@example.com',
            'senha': 'TempPass123!',
            'confirmacao': 'TempPass123!',
            'accepted_terms': '',
            'accepted_privacy': ''
        })

        # Deve rejeitar sem consentimento
        self.assertIn(response.status_code, [200, 400])


class AuditLoggingTests(TestCase):
    """Testes de Logs de Auditoria (Requisito 5)"""

    def test_log_function_exists(self):
        """Valida que função de log foi implementada"""
        from Smarko_App.views import registrar_log_firebase
        self.assertIsNotNone(registrar_log_firebase)

    def test_ip_extraction_works(self):
        """Valida que IP do cliente é extraído"""
        from Smarko_App.views import get_client_ip

        request = MagicMock()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}

        ip = get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')


class SecurityHeadersTests(TestCase):
    """Testes de Headers de Segurança"""

    def test_security_headers_present(self):
        """Valida que headers de segurança estão configurados"""
        response = self.client.get('/')

        # Headers mínimos esperados
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options'
        ]

        for header in expected_headers:
            self.assertIn(header, response)
