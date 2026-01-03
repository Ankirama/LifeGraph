"""
Base Django settings for LifeGraph project.

Common settings shared between development and production.
"""

import os
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Read .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.openid_connect",
    "django_celery_beat",
    "auditlog",
    "storages",
]

LOCAL_APPS = [
    "apps.core",
    "apps.people",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "lifegraph.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "lifegraph.wsgi.application"
ASGI_APPLICATION = "lifegraph.asgi.application"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sites framework
SITE_ID = 1

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# DRF Spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    "TITLE": "LifeGraph API",
    "DESCRIPTION": "Personal CRM for long-term relationship memory",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Celery Configuration
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Allauth Configuration
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "optional"

# OAuth2 / OpenID Connect (Authentik)
SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "authentik",
                "name": "Authentik",
                "client_id": env("OAUTH2_CLIENT_ID", default=""),
                "secret": env("OAUTH2_CLIENT_SECRET", default=""),
                "settings": {
                    "server_url": env("OAUTH2_SERVER_URL", default=""),
                },
            }
        ]
    }
}

# Auditlog
AUDITLOG_INCLUDE_ALL_MODELS = False  # We register models explicitly
AUDITLOG_INCLUDE_TRACKING_MODELS = (
    "apps.people",
    "apps.core",
)

# OpenAI
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")

# LinkedIn Integration
# WARNING: Uses unofficial API. Use sparingly to avoid account restrictions.
LINKEDIN_EMAIL = env("LINKEDIN_EMAIL", default="")
LINKEDIN_PASSWORD = env("LINKEDIN_PASSWORD", default="")

# Rate Limiting Configuration
# Uses django-ratelimit for per-view rate limiting
RATELIMIT_ENABLE = env.bool("RATELIMIT_ENABLE", default=True)
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "apps.core.views.ratelimited_error"

# Rate limit settings (requests per time period)
RATELIMIT_API_DEFAULT = env("RATELIMIT_API_DEFAULT", default="100/m")  # 100 requests/minute
RATELIMIT_API_AI = env("RATELIMIT_API_AI", default="10/m")  # 10 AI requests/minute
RATELIMIT_API_UPLOAD = env("RATELIMIT_API_UPLOAD", default="20/m")  # 20 uploads/minute
RATELIMIT_LOGIN = env("RATELIMIT_LOGIN", default="5/m")  # 5 login attempts/minute

# Cache configuration (required for rate limiting)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    }
}

# Field-Level Encryption (Fernet/AES-128-CBC)
# Generate key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# You can add multiple keys for key rotation - first key is used for encryption,
# all keys are tried for decryption (newest first)
FERNET_KEYS = env.list("FERNET_KEYS", default=[])
