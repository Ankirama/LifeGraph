"""
Tests for Relationship and RelationshipType models.
"""

import datetime

import pytest
from django.db import IntegrityError

from apps.people.models import Relationship, RelationshipType
from tests.factories import (
    FamilyRelationshipTypeFactory,
    PersonFactory,
    ProfessionalRelationshipTypeFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
    SymmetricRelationshipTypeFactory,
)


# =============================================================================
# RelationshipType Creation Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipTypeCreation:
    """Tests for RelationshipType model creation."""

    def test_create_basic_relationship_type(self):
        """Test creating a basic relationship type."""
        rt = RelationshipTypeFactory(
            name="Friend",
            inverse_name="Friend",
            category=RelationshipType.Category.SOCIAL,
        )

        assert rt.name == "Friend"
        assert rt.inverse_name == "Friend"
        assert rt.category == RelationshipType.Category.SOCIAL
        assert rt.pk is not None

    def test_create_family_relationship_type(self):
        """Test creating a family relationship type."""
        rt = FamilyRelationshipTypeFactory(name="Father", inverse_name="Child")

        assert rt.category == RelationshipType.Category.FAMILY

    def test_create_professional_relationship_type(self):
        """Test creating a professional relationship type."""
        rt = ProfessionalRelationshipTypeFactory(name="Manager", inverse_name="Report")

        assert rt.category == RelationshipType.Category.PROFESSIONAL

    def test_relationship_type_unique_name(self):
        """Test that relationship type names must be unique."""
        RelationshipTypeFactory(name="Unique Type")

        with pytest.raises(IntegrityError):
            RelationshipType.objects.create(name="Unique Type")


# =============================================================================
# Symmetric RelationshipType Tests
# =============================================================================


@pytest.mark.django_db
class TestSymmetricRelationshipType:
    """Tests for symmetric relationship types."""

    def test_symmetric_relationship_type(self):
        """Test creating a symmetric relationship type."""
        rt = SymmetricRelationshipTypeFactory(name="Spouse")

        assert rt.is_symmetric is True

    def test_symmetric_sets_inverse_name_on_save(self):
        """Test that symmetric relationships auto-set inverse_name."""
        rt = RelationshipType(
            name="Best Friend",
            is_symmetric=True,
            inverse_name="",
        )
        rt.save()

        assert rt.inverse_name == "Best Friend"

    def test_non_symmetric_keeps_inverse_name(self):
        """Test that non-symmetric relationships keep different inverse_name."""
        rt = RelationshipType(
            name="Parent",
            inverse_name="Child",
            is_symmetric=False,
        )
        rt.save()

        assert rt.inverse_name == "Child"


# =============================================================================
# RelationshipType String Representation Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipTypeStrRepresentation:
    """Tests for RelationshipType __str__ method."""

    def test_str_representation(self):
        """Test string representation of relationship type."""
        rt = RelationshipTypeFactory(name="Colleague")

        assert str(rt) == "Colleague"


# =============================================================================
# RelationshipType Ordering Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipTypeOrdering:
    """Tests for RelationshipType ordering."""

    def test_ordering_by_category_and_name(self):
        """Test that relationship types are ordered by category, then name."""
        # Create in non-alphabetical order
        rt1 = RelationshipTypeFactory(name="Zebra", category=RelationshipType.Category.SOCIAL)
        rt2 = RelationshipTypeFactory(name="Alpha", category=RelationshipType.Category.SOCIAL)
        rt3 = FamilyRelationshipTypeFactory(name="Beta")

        # Filter to only our test records to avoid interference from other tests
        test_ids = [rt1.pk, rt2.pk, rt3.pk]
        types = list(RelationshipType.objects.filter(pk__in=test_ids))

        # Family comes before Social alphabetically
        assert types[0].category == RelationshipType.Category.FAMILY
        assert types[1].name == "Alpha"
        assert types[2].name == "Zebra"


# =============================================================================
# Relationship Creation Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipCreation:
    """Tests for Relationship model creation."""

    def test_create_basic_relationship(self):
        """Test creating a basic relationship."""
        person_a = PersonFactory(first_name="Alice")
        person_b = PersonFactory(first_name="Bob")
        rt = RelationshipTypeFactory(name="Friend")

        relationship = RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        assert relationship.person_a == person_a
        assert relationship.person_b == person_b
        assert relationship.relationship_type == rt
        assert relationship.pk is not None

    def test_relationship_with_dates_and_notes(self):
        """Test creating a relationship with all fields."""
        started = datetime.date(2020, 1, 1)

        relationship = RelationshipFactory(
            started_date=started,
            notes="Met at a conference",
            strength=4,
        )

        assert relationship.started_date == started
        assert relationship.notes == "Met at a conference"
        assert relationship.strength == 4

    def test_relationship_auto_created_flag(self):
        """Test the auto_created flag."""
        relationship = RelationshipFactory(auto_created=True)

        assert relationship.auto_created is True


# =============================================================================
# Relationship Constraints Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipConstraints:
    """Tests for Relationship model constraints."""

    def test_no_self_relationship(self):
        """Test that a person cannot have a relationship with themselves."""
        person = PersonFactory()
        rt = RelationshipTypeFactory()

        with pytest.raises(IntegrityError):
            Relationship.objects.create(
                person_a=person,
                person_b=person,
                relationship_type=rt,
            )

    def test_unique_relationship(self):
        """Test that duplicate relationships are not allowed."""
        person_a = PersonFactory()
        person_b = PersonFactory()
        rt = RelationshipTypeFactory()

        Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        with pytest.raises(IntegrityError):
            Relationship.objects.create(
                person_a=person_a,
                person_b=person_b,
                relationship_type=rt,
            )

    def test_different_relationship_types_allowed(self):
        """Test that same persons can have different relationship types."""
        person_a = PersonFactory()
        person_b = PersonFactory()
        rt1 = RelationshipTypeFactory(name="Friend")
        rt2 = RelationshipTypeFactory(name="Colleague")

        rel1 = Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt1,
        )
        rel2 = Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt2,
        )

        assert rel1.pk != rel2.pk


# =============================================================================
# Relationship String Representation Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipStrRepresentation:
    """Tests for Relationship __str__ method."""

    def test_str_representation(self):
        """Test string representation of relationship."""
        person_a = PersonFactory(first_name="Alice", last_name="Smith")
        person_b = PersonFactory(first_name="Bob", last_name="Jones")
        rt = RelationshipTypeFactory(name="Friend")

        relationship = RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )

        expected = "Alice Smith → Friend → Bob Jones"
        assert str(relationship) == expected


# =============================================================================
# Relationship Ordering Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipOrdering:
    """Tests for Relationship ordering."""

    def test_ordering_by_created_at_desc(self):
        """Test that relationships are ordered by created_at descending."""
        rel1 = RelationshipFactory()
        rel2 = RelationshipFactory()
        rel3 = RelationshipFactory()

        relationships = list(Relationship.objects.all())

        # Most recent first
        assert relationships[0].pk == rel3.pk
        assert relationships[1].pk == rel2.pk
        assert relationships[2].pk == rel1.pk


# =============================================================================
# Relationship Strength Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipStrength:
    """Tests for Relationship strength field."""

    def test_strength_range(self):
        """Test setting strength within valid range."""
        for strength in [1, 2, 3, 4, 5]:
            relationship = RelationshipFactory(strength=strength)
            assert relationship.strength == strength

    def test_strength_optional(self):
        """Test that strength is optional."""
        relationship = RelationshipFactory(strength=None)

        assert relationship.strength is None


# =============================================================================
# Relationship Cascade Delete Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipCascadeDelete:
    """Tests for Relationship cascade delete behavior."""

    def test_delete_person_deletes_relationships(self):
        """Test that deleting a person deletes their relationships."""
        person_a = PersonFactory()
        person_b = PersonFactory()
        rt = RelationshipTypeFactory()

        relationship = Relationship.objects.create(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rt,
        )
        rel_id = relationship.pk

        person_a.delete()

        assert not Relationship.objects.filter(pk=rel_id).exists()

    def test_delete_relationship_type_protected(self):
        """Test that deleting a relationship type is protected if used."""
        rt = RelationshipTypeFactory()
        RelationshipFactory(relationship_type=rt)

        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            rt.delete()


# =============================================================================
# Person Relationship Related Managers Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonRelationshipManagers:
    """Tests for Person relationship related managers."""

    def test_person_relationships_as_a(self):
        """Test getting relationships where person is person_a."""
        person = PersonFactory()
        other1 = PersonFactory()
        other2 = PersonFactory()
        rt = RelationshipTypeFactory()

        Relationship.objects.create(person_a=person, person_b=other1, relationship_type=rt)
        Relationship.objects.create(person_a=person, person_b=other2, relationship_type=rt)

        assert person.relationships_as_a.count() == 2

    def test_person_relationships_as_b(self):
        """Test getting relationships where person is person_b."""
        person = PersonFactory()
        other1 = PersonFactory()
        other2 = PersonFactory()
        rt = RelationshipTypeFactory()

        Relationship.objects.create(person_a=other1, person_b=person, relationship_type=rt)
        Relationship.objects.create(person_a=other2, person_b=person, relationship_type=rt)

        assert person.relationships_as_b.count() == 2
