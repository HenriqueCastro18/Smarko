import os
import json
from pathlib import Path
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from django.contrib.auth.hashers import BCryptSHA256PasswordHasher

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-dev-key-2026')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

WHITENOISE_USE_FINDERS = True

ALLOWED_HOSTS = [
    'smarkoo.vercel.app',
    'smarko.app',
    'smarko-tfc.vercel.app',
    '*.vercel.app',
    'localhost',
    '127.0.0.1'
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Smarko_App',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Smarko.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Smarko.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy'
    }
}

class SmarkoBcryptHasher(BCryptSHA256PasswordHasher):
    rounds = 14

PASSWORD_HASHERS = [
    'Smarko.settings.SmarkoBcryptHasher', 
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Europe/Lisbon'
USE_I18N = True
USE_TZ = True  # Garante que timestamps são salvos em UTC e convertidos para TIME_ZONE

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'Smarko_App', 'Static'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 120
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False

EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = "Smarko Security <noreply@smarko.app>"

FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_API_KEY')

if not firebase_admin._apps:
    try:
        cred = None

        project_id = os.getenv('FIREBASE_PROJECT_ID')
        client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        private_key = os.getenv('FIREBASE_PRIVATE_KEY')

        if project_id and client_email and private_key:
            cred_dict = {
                'type': 'service_account',
                'project_id': project_id,
                'private_key_id': os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
                'private_key': private_key.replace('\\n', '\n'),
                'client_email': client_email,
                'client_id': os.getenv('FIREBASE_CLIENT_ID', ''),
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            }
            cred = credentials.Certificate(cred_dict)

        elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
            cred_dict = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'), strict=False)
            cred = credentials.Certificate(cred_dict)

        else:
            cred_path = os.path.join(BASE_DIR, 'serviceAccountKey.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)

        if cred:
            firebase_admin.initialize_app(cred)
        else:
            print("⚠️ Firebase não configurado. Nenhuma credencial encontrada (env vars ou arquivo local).")
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")

db = firestore.client() if firebase_admin._apps else None

if os.getenv('VERCEL') or not DEBUG:
    # Produção: Força HTTPS completo
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # Desenvolvimento: Cookies seguros mesmo em HTTP local
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0