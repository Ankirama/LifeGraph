"""
Encrypted field utilities for sensitive data protection.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC) for field-level
encryption of sensitive personal data at rest.
"""

from django.conf import settings
from encrypted_fields.fields import (
    EncryptedCharField,
    EncryptedEmailField,
    EncryptedJSONField,
    EncryptedTextField,
)

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
