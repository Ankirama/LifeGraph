"""
Encrypted field utilities for sensitive data protection.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC) for field-level
encryption of sensitive personal data at rest.
"""

import json

from django.conf import settings  # noqa: F401 - used in validate_encryption_config
from encrypted_fields.fields import (
    EncryptedCharField,
    EncryptedEmailField,
    EncryptedFieldMixin,
    EncryptedTextField,
)
from django.db import models


class EncryptedJSONField(EncryptedFieldMixin, models.TextField):
    """
    Encrypted JSON field that stores JSON data with encryption at rest.
    Uses the same encryption as EncryptedTextField from encrypted_fields library.
    """

    def get_internal_type(self):
        return "BinaryField"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        # Decrypt using the mixin's decrypt method (same as EncryptedTextField)
        try:
            decrypted = self.decrypt(value)
        except Exception:
            return None
        # Parse JSON
        try:
            return json.loads(decrypted)
        except (json.JSONDecodeError, TypeError):
            return None

    def get_prep_value(self, value):
        if value is None:
            return None
        # Convert to JSON string - encryption is handled by get_db_prep_save
        return json.dumps(value, default=str)

    def to_python(self, value):
        """Handle form data and other Python-side conversions."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            # Parse JSON string (from form input, fixtures, or after decryption)
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

# Re-export encrypted field types for consistent usage across models
__all__ = [
    "EncryptedCharField",
    "EncryptedTextField",
    "EncryptedJSONField",
    "EncryptedEmailField",
]


def validate_encryption_config():
    """
    Validate that encryption is properly configured.

    Call this during app startup to ensure encryption is working.
    """
    keys = getattr(settings, "FIELD_ENCRYPTION_KEYS", None)
    if not keys:
        return False, "FIELD_ENCRYPTION_KEYS not set in settings"

    # Check that at least one key is valid (32 bytes = 64 hex chars)
    for key in keys:
        if len(key) != 64:
            return False, f"FIELD_ENCRYPTION_KEYS must be 64 hex characters (32 bytes), got {len(key)}"
        try:
            bytes.fromhex(key)
        except ValueError as e:
            return False, f"Invalid hex key: {e}"

    return True, "Encryption configured correctly"
