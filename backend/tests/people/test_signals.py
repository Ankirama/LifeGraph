"""
Tests for relationship signals.
"""

import pytest

from apps.people.models import Relationship, RelationshipType
from tests.factories import (
    PersonFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
    SymmetricRelationshipTypeFactory,
)


# =============================================================================
# Auto-Create Inverse Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestAutoCreateInverseRelationship:
    """Tests for auto-creating inverse relationships."""

    def test_symmetric_relationship_creates_inverse(self):
        """Test that symmetric relationships auto-create inverse."""
        # Create symmetric relationship type with auto_create_inverse=True
        rt = SymmetricRelationshipTypeFactory(
            name="Friend",
            is_symmetric=True,
            auto_create_inverse=True,
        )
        person_a = PersonFactory(first_name="Alice")
        person_b = PersonFactory(first_name="Bob")

        # Create relationship from Alice to Bob
        Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        # Inverse should exist (Bob to Alice)
        inverse = Relationship.objects.filter(
            person_a=person_b,
            person_b=person_a,
            relationship_type=rt,
        ).first()

        assert inverse is not None
        assert inverse.auto_created is True

    def test_asymmetric_relationship_creates_inverse_with_inverse_type(self):
        """Test that asymmetric relationships create inverse with matching type."""
        # Create parent -> child relationship types
        parent_type = RelationshipTypeFactory(
            name="Parent",
            inverse_name="Child",
            is_symmetric=False,
            auto_create_inverse=True,
        )
        child_type = RelationshipTypeFactory(
            name="Child",
            inverse_name="Parent",
            is_symmetric=False,
            auto_create_inverse=True,
        )

        parent = PersonFactory(first_name="Parent")
        child = PersonFactory(first_name="Child")

        # Create Parent -> Child relationship
        Relationship.objects.create(
            person_a=parent,
            person_b=child,
            relationship_type=parent_type,
        )

        # Inverse should exist with Child type
        inverse = Relationship.objects.filter(
            person_a=child,
            person_b=parent,
            relationship_type=child_type,
        ).first()

        assert inverse is not None
        assert inverse.auto_created is True

    def test_no_inverse_when_auto_create_disabled(self):
        """Test that no inverse is created when auto_create_inverse is False."""
        rt = RelationshipTypeFactory(
            name="Acquaintance",
            inverse_name="Acquaintance",
            auto_create_inverse=False,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()

        Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        # Inverse should NOT exist
        inverse_count = Relationship.objects.filter(
            person_a=person_b,
            person_b=person_a,
            relationship_type=rt,
        ).count()

        assert inverse_count == 0

    def test_no_duplicate_inverse_created(self):
        """Test that inverse is not duplicated if already exists."""
        rt = SymmetricRelationshipTypeFactory(
            name="Colleague",
            auto_create_inverse=True,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()

        # Create first relationship - should auto-create inverse
        Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        # Count relationships
        rel_count = Relationship.objects.filter(relationship_type=rt).count()

        # Should be exactly 2 (original + inverse)
        assert rel_count == 2

    def test_auto_created_relationship_doesnt_trigger_signal(self):
        """Test that auto-created relationships don't trigger another inverse."""
        rt = SymmetricRelationshipTypeFactory(
            name="Sibling",
            auto_create_inverse=True,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()

        # Create relationship
        Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        # Should only have 2 relationships (not more from recursive signals)
        rel_count = Relationship.objects.filter(
            relationship_type=rt,
        ).count()

        assert rel_count == 2

    def test_no_inverse_when_inverse_type_not_found(self):
        """Test that no inverse is created if inverse type doesn't exist."""
        rt = RelationshipTypeFactory(
            name="OnlyOneWay",
            inverse_name="NonExistent",
            is_symmetric=False,
            auto_create_inverse=True,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()

        # Create relationship
        Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        # Only the original relationship should exist
        rel_count = Relationship.objects.filter(
            person_a__in=[person_a, person_b],
            person_b__in=[person_a, person_b],
        ).count()

        assert rel_count == 1

    def test_inverse_copies_metadata(self):
        """Test that inverse relationship copies started_date, notes, strength."""
        import datetime

        rt = SymmetricRelationshipTypeFactory(
            name="Partner",
            auto_create_inverse=True,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()

        started = datetime.date(2020, 5, 15)

        Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
            started_date=started,
            notes="Met at conference",
            strength=4,
        )

        inverse = Relationship.objects.get(
            person_a=person_b,
            person_b=person_a,
            relationship_type=rt,
        )

        assert inverse.started_date == started
        assert inverse.notes == "Met at conference"
        assert inverse.strength == 4


# =============================================================================
# Auto-Delete Inverse Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestAutoDeleteInverseRelationship:
    """Tests for auto-deleting inverse relationships."""

    def test_deleting_relationship_deletes_inverse(self):
        """Test that deleting a relationship also deletes its inverse."""
        rt = SymmetricRelationshipTypeFactory(
            name="Mentor",
            auto_create_inverse=True,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()

        # Create relationship (inverse auto-created)
        rel = Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        # Verify both exist
        assert Relationship.objects.filter(relationship_type=rt).count() == 2

        # Delete the original
        rel.delete()

        # Both should be gone
        assert Relationship.objects.filter(relationship_type=rt).count() == 0

    def test_delete_inverse_symmetric(self):
        """Test deleting symmetric relationship deletes inverse."""
        rt = SymmetricRelationshipTypeFactory(
            name="Spouse",
            auto_create_inverse=True,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()

        Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        # Delete the auto-created inverse instead
        inverse = Relationship.objects.get(
            person_a=person_b,
            person_b=person_a,
            relationship_type=rt,
        )
        inverse.delete()

        # Both should be gone
        assert Relationship.objects.filter(
            person_a__in=[person_a, person_b],
            person_b__in=[person_a, person_b],
        ).count() == 0

    def test_delete_asymmetric_with_inverse_type(self):
        """Test deleting asymmetric relationship with different inverse type."""
        manager_type = RelationshipTypeFactory(
            name="Manager",
            inverse_name="Report",
            is_symmetric=False,
            auto_create_inverse=True,
        )
        report_type = RelationshipTypeFactory(
            name="Report",
            inverse_name="Manager",
            is_symmetric=False,
            auto_create_inverse=True,
        )

        manager = PersonFactory(first_name="Manager")
        report = PersonFactory(first_name="Report")

        # Create Manager -> Report
        rel = Relationship.objects.create(
            person_a=manager,
            person_b=report,
            relationship_type=manager_type,
        )

        # Verify inverse exists with Report type
        assert Relationship.objects.filter(
            person_a=report,
            person_b=manager,
            relationship_type=report_type,
        ).exists()

        # Delete original
        rel.delete()

        # Inverse should also be deleted
        assert not Relationship.objects.filter(
            person_a=report,
            person_b=manager,
            relationship_type=report_type,
        ).exists()

    def test_delete_no_infinite_loop(self):
        """Test that deletion doesn't cause infinite recursion."""
        rt = SymmetricRelationshipTypeFactory(
            name="Roommate",
            auto_create_inverse=True,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()

        rel = Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        # This should not raise RecursionError
        rel.delete()

        # All relationships should be deleted
        assert Relationship.objects.filter(relationship_type=rt).count() == 0
