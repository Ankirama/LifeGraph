"""
Encrypted field utilities for sensitive data protection.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC) for field-level
encryption of sensitive personal data at rest.
"""

import json

from django.conf import settings
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
    Uses TextField base with encryption mixin to store as bytea.
    """

    def get_internal_type(self):
        return "BinaryField"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        # Database returns bytes (bytea), convert to string for Fernet
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        # Decrypt using the Fernet instance directly
        try:
            decrypted = self.f.decrypt(bytes(value, "utf-8")).decode("utf-8")
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
        # Convert to JSON string and encrypt directly
        # (bypasses super chain which calls to_python and breaks empty containers)
        json_str = json.dumps(value, default=str)
        return self.f.encrypt(bytes(json_str, "utf-8")).decode("utf-8")

    def to_python(self, value):
        """Handle form data and other Python-side conversions."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            # Try parsing as plain JSON first (form input, fixtures)
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
            # Try decrypting (could be encrypted data)
            try:
                decrypted = self.f.decrypt(bytes(value, "utf-8")).decode("utf-8")
                return json.loads(decrypted)
            except Exception:
                return None
        return None

# Re-export encrypted field types for consistent usage across models
__all__ = [
    "EncryptedCharField",
    "EncryptedTextField",
    "EncryptedJSONField",
    "EncryptedEmailField",
]


def get_encryption_key():
    """
    Get the Fernet encryption key from settings.

    The key should be a URL-safe base64-encoded 32-byte key.
    Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    key = getattr(settings, "SALT_KEY", None)
    if not key:
        raise ValueError(
            "SALT_KEY not configured. Generate a key with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return key


def validate_encryption_config():
    """
    Validate that encryption is properly configured.

    Call this during app startup to ensure encryption is working.
    """
    from cryptography.fernet import Fernet, InvalidToken

    key = getattr(settings, "SALT_KEY", None)
    if not key:
        return False, "SALT_KEY not set in settings"

    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        # Test encryption/decryption
        test_data = b"encryption_test"
        encrypted = f.encrypt(test_data)
        decrypted = f.decrypt(encrypted)
        if decrypted != test_data:
            return False, "Encryption round-trip failed"
    except (InvalidToken, ValueError) as e:
        return False, f"Invalid encryption key: {e}"

    return True, "Encryption configured correctly"
