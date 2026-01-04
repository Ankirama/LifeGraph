"""
Tests for encryption utilities and encrypted fields.
"""

import pytest
from cryptography.fernet import Fernet

from apps.core.encryption import (
    EncryptedEmailField,
    EncryptedJSONField,
    EncryptedTextField,
    get_encryption_key,
    validate_encryption_config,
)


# =============================================================================
# Encryption Configuration Tests
# =============================================================================


class TestGetEncryptionKey:
    """Tests for get_encryption_key function."""

    def test_returns_key_when_configured(self, settings):
        """Test that get_encryption_key returns the configured key."""
        test_key = Fernet.generate_key().decode()
        settings.SALT_KEY = test_key

        result = get_encryption_key()

        assert result == test_key

    def test_raises_when_not_configured(self, settings):
        """Test that missing SALT_KEY raises ValueError."""
        settings.SALT_KEY = None

        with pytest.raises(ValueError, match="SALT_KEY not configured"):
            get_encryption_key()

    def test_raises_when_empty(self, settings):
        """Test that empty SALT_KEY raises ValueError."""
        settings.SALT_KEY = ""

        with pytest.raises(ValueError, match="SALT_KEY not configured"):
            get_encryption_key()


class TestValidateEncryptionConfig:
    """Tests for validate_encryption_config function."""

    def test_valid_config_returns_true(self, settings):
        """Test that valid configuration returns (True, message)."""
        test_key = Fernet.generate_key().decode()
        settings.SALT_KEY = test_key

        is_valid, message = validate_encryption_config()

        assert is_valid is True
        assert "correctly" in message.lower()

    def test_missing_key_returns_false(self, settings):
        """Test that missing key returns (False, message)."""
        settings.SALT_KEY = None

        is_valid, message = validate_encryption_config()

        assert is_valid is False
        assert "not set" in message.lower()

    def test_invalid_key_format_returns_false(self, settings):
        """Test that invalid key format returns (False, message)."""
        settings.SALT_KEY = "not-a-valid-fernet-key"

        is_valid, message = validate_encryption_config()

        assert is_valid is False
        assert "invalid" in message.lower()


# =============================================================================
# Encrypted Field Tests
# =============================================================================


class TestEncryptedEmailField:
    """Tests for EncryptedEmailField."""

    def test_field_exists(self):
        """Test that EncryptedEmailField is available."""
        field = EncryptedEmailField()
        assert field is not None

    def test_max_length(self):
        """Test that max_length can be specified."""
        field = EncryptedEmailField(max_length=100)
        assert field.max_length == 100


class TestEncryptedTextField:
    """Tests for EncryptedTextField."""

    def test_field_exists(self):
        """Test that EncryptedTextField is available."""
        field = EncryptedTextField()
        assert field is not None


class TestEncryptedJSONField:
    """Tests for EncryptedJSONField."""

    def test_field_exists(self):
        """Test that EncryptedJSONField is available."""
        field = EncryptedJSONField()
        assert field is not None


# =============================================================================
# Integration Tests (require database with encryption configured)
# =============================================================================


@pytest.mark.django_db
class TestEncryptionIntegration:
    """Integration tests for encryption with actual database operations."""

    def test_person_encrypted_fields_roundtrip(self):
        """Test that encrypted fields work correctly with Person model."""
        from tests.factories import PersonFactory
        from apps.people.models import Person

        # Create person with encrypted fields
        person = PersonFactory(
            notes="Secret notes about this person",
            met_context="We met at a secret conference",
            emails=[{"email": "secret@example.com", "label": "personal"}],
            phones=[{"phone": "+1-secret", "label": "mobile"}],
            addresses=[{"address": "123 Secret St", "label": "home"}],
        )

        # Reload from database
        reloaded = Person.objects.get(pk=person.pk)

        # Verify decrypted values match
        assert reloaded.notes == "Secret notes about this person"
        assert reloaded.met_context == "We met at a secret conference"
        assert reloaded.emails == [{"email": "secret@example.com", "label": "personal"}]
        assert reloaded.phones == [{"phone": "+1-secret", "label": "mobile"}]
        assert reloaded.addresses == [{"address": "123 Secret St", "label": "home"}]

    def test_anecdote_encrypted_content_roundtrip(self):
        """Test that encrypted anecdote content works correctly."""
        from tests.factories import AnecdoteFactory, PersonFactory
        from apps.people.models import Anecdote

        person = PersonFactory()
        anecdote = AnecdoteFactory(content="This is a secret memory")
        anecdote.persons.add(person)

        # Reload from database
        reloaded = Anecdote.objects.get(pk=anecdote.pk)

        assert reloaded.content == "This is a secret memory"

    def test_relationship_encrypted_notes_roundtrip(self):
        """Test that encrypted relationship notes work correctly."""
        from tests.factories import RelationshipFactory
        from apps.people.models import Relationship

        relationship = RelationshipFactory(notes="Secret notes about this relationship")

        # Reload from database
        reloaded = Relationship.objects.get(pk=relationship.pk)

        assert reloaded.notes == "Secret notes about this relationship"

    def test_employment_encrypted_description_roundtrip(self):
        """Test that encrypted employment description works correctly."""
        from tests.factories import EmploymentFactory
        from apps.people.models import Employment

        employment = EmploymentFactory(description="Secret job duties")

        # Reload from database
        reloaded = Employment.objects.get(pk=employment.pk)

        assert reloaded.description == "Secret job duties"

    def test_custom_field_value_encrypted_roundtrip(self):
        """Test that encrypted custom field values work correctly."""
        from tests.factories import CustomFieldValueFactory
        from apps.people.models import CustomFieldValue

        # Use string values to ensure consistent roundtrip
        cfv = CustomFieldValueFactory(value={"secret": "data", "other": "value"})

        # Reload from database
        reloaded = CustomFieldValue.objects.get(pk=cfv.pk)

        assert reloaded.value == {"secret": "data", "other": "value"}
