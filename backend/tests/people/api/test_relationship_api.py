"""
Tests for Relationship and RelationshipType API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.people.models import Relationship, RelationshipType
from tests.factories import (
    PersonFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
    SymmetricRelationshipTypeFactory,
)


# =============================================================================
# RelationshipType List Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipTypeListAPI:
    """Tests for RelationshipType list endpoint."""

    def test_list_relationship_types_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("relationshiptype-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_relationship_types(self, authenticated_client):
        """Test listing relationship types."""
        RelationshipTypeFactory.create_batch(3)
        url = reverse("relationshiptype-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# RelationshipType Create Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipTypeCreateAPI:
    """Tests for RelationshipType create endpoint."""

    def test_create_relationship_type(self, authenticated_client):
        """Test creating a relationship type."""
        url = reverse("relationshiptype-list")
        data = {
            "name": "Mentor",
            "inverse_name": "Mentee",
            "category": "professional",
            "is_symmetric": False,
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Mentor"

    def test_create_symmetric_relationship_type(self, authenticated_client):
        """Test creating a symmetric relationship type."""
        url = reverse("relationshiptype-list")
        data = {
            "name": "Spouse",
            "is_symmetric": True,
            "category": "family",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_symmetric"] is True


# =============================================================================
# RelationshipType Detail Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipTypeDetailAPI:
    """Tests for RelationshipType detail endpoint."""

    def test_get_relationship_type(self, authenticated_client, relationship_type):
        """Test getting a relationship type."""
        url = reverse("relationshiptype-detail", kwargs={"pk": relationship_type.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == relationship_type.name

    def test_update_relationship_type(self, authenticated_client, relationship_type):
        """Test updating a relationship type."""
        url = reverse("relationshiptype-detail", kwargs={"pk": relationship_type.pk})
        data = {
            "name": "Updated Type",
            "inverse_name": "Updated Inverse",
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Type"

    def test_delete_relationship_type_no_relationships(self, authenticated_client):
        """Test deleting a relationship type with no relationships."""
        rt = RelationshipTypeFactory()
        url = reverse("relationshiptype-detail", kwargs={"pk": rt.pk})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# Relationship List Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipListAPI:
    """Tests for Relationship list endpoint."""

    def test_list_relationships_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("relationship-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_relationships(self, authenticated_client):
        """Test listing relationships."""
        RelationshipFactory.create_batch(3)
        url = reverse("relationship-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_filter_relationships_by_person(self, authenticated_client):
        """Test filtering relationships by person."""
        person = PersonFactory()
        other = PersonFactory()
        rt = RelationshipTypeFactory()
        RelationshipFactory(person_a=person, person_b=other, relationship_type=rt)
        RelationshipFactory()  # Different relationship

        url = reverse("relationship-list")
        response = authenticated_client.get(url, {"person_a": person.pk})

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Relationship Create Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipCreateAPI:
    """Tests for Relationship create endpoint."""

    def test_create_relationship(self, authenticated_client):
        """Test creating a relationship."""
        person_a = PersonFactory()
        person_b = PersonFactory()
        rt = RelationshipTypeFactory()

        url = reverse("relationship-list")
        data = {
            "person_a": str(person_a.pk),
            "person_b": str(person_b.pk),
            "relationship_type": str(rt.pk),
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_relationship_with_details(self, authenticated_client):
        """Test creating a relationship with all details."""
        person_a = PersonFactory()
        person_b = PersonFactory()
        rt = RelationshipTypeFactory()

        url = reverse("relationship-list")
        data = {
            "person_a": str(person_a.pk),
            "person_b": str(person_b.pk),
            "relationship_type": str(rt.pk),
            "started_date": "2020-01-01",
            "notes": "Met at conference",
            "strength": 4,
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_self_relationship_fails(self, authenticated_client):
        """Test that self-relationships are rejected."""
        person = PersonFactory()
        rt = RelationshipTypeFactory()

        url = reverse("relationship-list")
        data = {
            "person_a": str(person.pk),
            "person_b": str(person.pk),
            "relationship_type": str(rt.pk),
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_duplicate_relationship_fails(self, authenticated_client):
        """Test that duplicate relationships are rejected."""
        person_a = PersonFactory()
        person_b = PersonFactory()
        rt = RelationshipTypeFactory()

        # Create first relationship
        RelationshipFactory(person_a=person_a, person_b=person_b, relationship_type=rt)

        url = reverse("relationship-list")
        data = {
            "person_a": str(person_a.pk),
            "person_b": str(person_b.pk),
            "relationship_type": str(rt.pk),
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Relationship Detail Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipDetailAPI:
    """Tests for Relationship detail endpoint."""

    def test_get_relationship(self, authenticated_client, relationship):
        """Test getting a relationship detail."""
        url = reverse("relationship-detail", kwargs={"pk": relationship.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_update_relationship(self, authenticated_client, relationship):
        """Test updating a relationship."""
        url = reverse("relationship-detail", kwargs={"pk": relationship.pk})
        data = {
            "notes": "Updated notes",
            "strength": 5,
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["strength"] == 5

    def test_delete_relationship(self, authenticated_client, relationship):
        """Test deleting a relationship."""
        url = reverse("relationship-detail", kwargs={"pk": relationship.pk})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Relationship.objects.filter(pk=relationship.pk).exists()
