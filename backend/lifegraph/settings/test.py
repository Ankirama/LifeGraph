"""
Test settings for LifeGraph.

Uses stricter security settings to properly test authentication.
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# Use a simpler secret key for tests
SECRET_KEY = "test-secret-key-not-for-production"

# Database - use the same PostgreSQL for tests
DATABASES = {
    "default": env.db(  # noqa: F405
        "DATABASE_URL",
        default="postgresql://lifegraph:lifegraph@localhost:5432/lifegraph",
    )
}

# Disable CORS restrictions in tests
CORS_ALLOW_ALL_ORIGINS = True

# Disable rate limiting in tests
RATELIMIT_ENABLE = False

# Email - use in-memory backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Media files - local storage for tests
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "test_media"  # noqa: F405

# Disable password validators for faster tests
AUTH_PASSWORD_VALIDATORS = []

# REST Framework - require authentication in tests
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

# Use local memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Celery - run tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Logging - reduce noise in tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}

# Remove debug toolbar from installed apps
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]  # noqa: F405
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]  # noqa: F405
