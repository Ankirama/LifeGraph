"""
Development settings for LifeGraph.
"""

import secrets

from .base import *  # noqa: F401, F403

DEBUG = True

# Development-only encryption key (generated at startup if not set)
# WARNING: This key changes on each restart - data encrypted with it won't be readable after restart
# For persistent development data, set FIELD_ENCRYPTION_KEYS in your .env file
if not FIELD_ENCRYPTION_KEYS:  # noqa: F405
    FIELD_ENCRYPTION_KEYS = [secrets.token_hex(32)]  # noqa: F405

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])  # noqa: F405

# Database
DATABASES = {
    "default": env.db(  # noqa: F405
        "DATABASE_URL",
        default="postgresql://lifegraph:lifegraph@localhost:5432/lifegraph",
    )
}

# CORS - allow frontend in development with credentials
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# CSRF - trust frontend origin (for proxy setup)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Redirect to frontend after login (relative - works with proxy)
LOGIN_REDIRECT_URL = "/"

# Debug toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# Email - console backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Media files - local storage in development
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405

# Use simpler password validation in development (still validates, but less strict)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 4},  # Shorter minimum for dev convenience
    },
]

# REST Framework - use IsAuthenticated (same as production)
# Session authentication allows browser-based access after login
REST_FRAMEWORK = {  # noqa: F405
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

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
