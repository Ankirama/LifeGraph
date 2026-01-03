"""
Encrypted field utilities for sensitive data protection.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC) for field-level
encryption of sensitive personal data at rest.
"""

from django.conf import settings
from fernet_fields import EncryptedCharField, EncryptedTextField
from fernet_fields.fields import EncryptedField

# Re-export encrypted field types for consistent usage across models
__all__ = [
    "EncryptedCharField",
    "EncryptedTextField",
    "EncryptedJSONField",
    "EncryptedEmailField",
]


class EncryptedEmailField(EncryptedCharField):
    """
    Encrypted email field that stores email addresses securely.

    Note: Email validation happens at the application layer since
    the encrypted value cannot be validated at the database level.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 254)
        super().__init__(*args, **kwargs)


class EncryptedJSONField(EncryptedTextField):
    """
    Encrypted JSON field for storing complex structured data securely.

    Stores JSON as encrypted text. Serialization/deserialization happens
    at the Python layer.

    Note: This field stores JSON as text, not as a native JSON type.
    For querying, you'll need to decrypt first.
    """

    def __init__(self, *args, default=None, **kwargs):
        if default is None:
            default = dict
        kwargs["default"] = default
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        """Convert database value to Python object."""
        import json

        # First, let parent class decrypt the value
        decrypted = super().from_db_value(value, expression, connection)

        if decrypted is None:
            return self.get_default()

        if isinstance(decrypted, (dict, list)):
            return decrypted

        try:
            return json.loads(decrypted)
        except (json.JSONDecodeError, TypeError):
            return self.get_default()

    def get_prep_value(self, value):
        """Convert Python object to database value."""
        import json

        if value is None:
            return None

        if isinstance(value, str):
            # Already a string, validate it's JSON
            try:
                json.loads(value)
                return super().get_prep_value(value)
            except json.JSONDecodeError:
                return super().get_prep_value(json.dumps(value))

        # Serialize to JSON string, then let parent encrypt
        json_str = json.dumps(value, ensure_ascii=False)
        return super().get_prep_value(json_str)

    def get_default(self):
        """Return default value."""
        if callable(self.default):
            return self.default()
        return self.default


def get_encryption_key():
    """
    Get the Fernet encryption key from settings.

    The key should be a URL-safe base64-encoded 32-byte key.
    Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    key = getattr(settings, "FERNET_KEYS", None)
    if not key:
        raise ValueError(
            "FERNET_KEYS not configured. Generate a key with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return key


def validate_encryption_config():
    """
    Validate that encryption is properly configured.

    Call this during app startup to ensure encryption is working.
    """
    from cryptography.fernet import Fernet, InvalidToken

    keys = getattr(settings, "FERNET_KEYS", None)
    if not keys:
        return False, "FERNET_KEYS not set in settings"

    if isinstance(keys, str):
        keys = [keys]

    for key in keys:
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
