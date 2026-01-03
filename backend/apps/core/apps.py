import logging
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        # Register models with auditlog
        from auditlog.registry import auditlog

        from .models import Group, Tag

        auditlog.register(Tag)
        auditlog.register(Group)

        # Validate encryption configuration (skip during migrations/shell)
        if not any(cmd in sys.argv for cmd in ["migrate", "makemigrations", "shell"]):
            self._validate_encryption()

    def _validate_encryption(self):
        """Validate field encryption is properly configured."""
        from .encryption import validate_encryption_config

        is_valid, message = validate_encryption_config()
        if not is_valid:
            logger.warning(
                "⚠️  Field encryption not configured: %s\n"
                "   Sensitive data will NOT be encrypted until FERNET_KEYS is set.\n"
                "   Generate a key with: python manage.py generate_encryption_key",
                message,
            )
