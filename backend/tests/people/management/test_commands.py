"""
Tests for People app management commands.
"""

from io import StringIO

import pytest
from django.core.management import call_command

from apps.people.models import RelationshipType


# =============================================================================
# seed_relationship_types Tests
# =============================================================================


@pytest.mark.django_db
class TestSeedRelationshipTypesCommand:
    """Tests for seed_relationship_types management command."""

    def test_creates_default_types(self):
        """Test that the command creates default relationship types."""
        out = StringIO()

        call_command("seed_relationship_types", stdout=out)

        output = out.getvalue()
        assert "Done!" in output

        # Verify some key types were created
        assert RelationshipType.objects.filter(name="friend").exists()
        assert RelationshipType.objects.filter(name="spouse").exists()
        assert RelationshipType.objects.filter(name="colleague").exists()
        assert RelationshipType.objects.filter(name="parent").exists()

    def test_creates_symmetric_types_correctly(self):
        """Test that symmetric types are created with correct settings."""
        call_command("seed_relationship_types")

        friend_type = RelationshipType.objects.get(name="friend")
        assert friend_type.is_symmetric is True
        assert friend_type.inverse_name == "friend"
        assert friend_type.auto_create_inverse is True

    def test_creates_asymmetric_types_correctly(self):
        """Test that asymmetric types are created with correct settings."""
        call_command("seed_relationship_types")

        parent_type = RelationshipType.objects.get(name="parent")
        assert parent_type.is_symmetric is False
        assert parent_type.inverse_name == "child"
        assert parent_type.auto_create_inverse is True

        child_type = RelationshipType.objects.get(name="child")
        assert child_type.is_symmetric is False
        assert child_type.inverse_name == "parent"

    def test_idempotent_execution(self):
        """Test that running the command multiple times doesn't create duplicates."""
        call_command("seed_relationship_types")
        initial_count = RelationshipType.objects.count()

        # Run again
        call_command("seed_relationship_types")
        final_count = RelationshipType.objects.count()

        assert final_count == initial_count

    def test_updates_existing_types(self):
        """Test that existing types are updated, not duplicated."""
        # Delete existing friend type if any
        RelationshipType.objects.filter(name="friend").delete()

        # Create a type with different settings
        RelationshipType.objects.create(
            name="friend",
            inverse_name="enemy",  # Wrong inverse
            category="other",  # Wrong category
            is_symmetric=False,  # Wrong setting
        )

        call_command("seed_relationship_types")

        # Verify it was updated
        friend_type = RelationshipType.objects.get(name="friend")
        assert friend_type.inverse_name == "friend"
        assert friend_type.category == "social"
        assert friend_type.is_symmetric is True

    def test_creates_all_categories(self):
        """Test that types from all categories are created."""
        call_command("seed_relationship_types")

        categories = RelationshipType.objects.values_list("category", flat=True).distinct()

        assert "family" in categories
        assert "social" in categories
        assert "professional" in categories

    def test_output_shows_created_count(self):
        """Test that output shows the correct created count."""
        out = StringIO()

        call_command("seed_relationship_types", stdout=out)

        output = out.getvalue()
        assert "Created" in output

    def test_family_types_created(self):
        """Test that all family types are created."""
        call_command("seed_relationship_types")

        family_types = RelationshipType.objects.filter(category="family")

        family_names = list(family_types.values_list("name", flat=True))
        assert "spouse" in family_names
        assert "parent" in family_names
        assert "child" in family_names
        assert "sibling" in family_names

    def test_professional_types_created(self):
        """Test that all professional types are created."""
        call_command("seed_relationship_types")

        prof_types = RelationshipType.objects.filter(category="professional")

        prof_names = list(prof_types.values_list("name", flat=True))
        assert "colleague" in prof_names
        assert "manager" in prof_names
        assert "mentor" in prof_names
