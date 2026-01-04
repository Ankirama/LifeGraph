"""
Tests for Person API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.people.models import Person
from tests.factories import (
    AnecdoteFactory,
    EmploymentFactory,
    GroupFactory,
    PersonFactory,
    PhotoFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
    TagFactory,
)


# =============================================================================
# Person List Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonListAPI:
    """Tests for Person list endpoint."""

    def test_list_persons_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_persons_authenticated(self, authenticated_client):
        """Test listing persons when authenticated."""
        PersonFactory.create_batch(3)
        url = reverse("person-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Response may be paginated - check that we have results
        if "count" in response.data:
            # Paginated response - at least 3 persons exist
            assert response.data["count"] >= 3
        else:
            # Non-paginated response
            data = response.data.get("results", response.data)
            assert len(data) >= 3  # At least the 3 we created

    def test_list_persons_empty(self, authenticated_client):
        """Test listing persons when none exist."""
        url = reverse("person-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_persons_pagination(self, authenticated_client):
        """Test pagination of person list."""
        PersonFactory.create_batch(25)
        url = reverse("person-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # If paginated, should have pagination fields
        if "results" in response.data:
            assert "count" in response.data

    def test_list_persons_filter_by_group(self, authenticated_client):
        """Test filtering persons by group."""
        group = GroupFactory(name="Friends")
        person_in_group = PersonFactory()
        person_in_group.groups.add(group)
        PersonFactory()  # Not in group

        url = reverse("person-list")
        response = authenticated_client.get(url, {"groups": group.pk})

        assert response.status_code == status.HTTP_200_OK

    def test_list_persons_filter_by_tag(self, authenticated_client):
        """Test filtering persons by tag."""
        tag = TagFactory(name="VIP")
        person_with_tag = PersonFactory()
        person_with_tag.tags.add(tag)
        PersonFactory()  # Without tag

        url = reverse("person-list")
        response = authenticated_client.get(url, {"tags": tag.pk})

        assert response.status_code == status.HTTP_200_OK

    def test_list_persons_search(self, authenticated_client):
        """Test searching persons by name."""
        PersonFactory(first_name="John", last_name="Smith")
        PersonFactory(first_name="Jane", last_name="Doe")

        url = reverse("person-list")
        response = authenticated_client.get(url, {"search": "John"})

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Person Create Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonCreateAPI:
    """Tests for Person create endpoint."""

    def test_create_person_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-list")
        data = {"first_name": "Test", "last_name": "User"}

        response = api_client.post(url, data)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_person_minimal(self, authenticated_client):
        """Test creating a person with minimal data."""
        url = reverse("person-list")
        data = {"first_name": "John"}

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "John"

    def test_create_person_full(self, authenticated_client):
        """Test creating a person with all fields."""
        url = reverse("person-list")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "nickname": "Johnny",
            "birthday": "1990-01-15",
            "notes": "Test notes",
            "linkedin_url": "https://linkedin.com/in/johndoe",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "John"
        assert response.data["last_name"] == "Doe"

    def test_create_person_with_emails(self, authenticated_client):
        """Test creating a person with email addresses."""
        url = reverse("person-list")
        data = {
            "first_name": "John",
            "emails": [{"email": "john@example.com", "label": "work"}],
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["emails"]) == 1

    def test_create_person_missing_required(self, authenticated_client):
        """Test creating a person without required field."""
        url = reverse("person-list")
        data = {"last_name": "Doe"}  # Missing first_name

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Person Detail Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonDetailAPI:
    """Tests for Person detail endpoint."""

    def test_get_person_unauthenticated(self, api_client, person):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-detail", kwargs={"pk": person.pk})

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_person(self, authenticated_client, person):
        """Test getting a person detail."""
        url = reverse("person-detail", kwargs={"pk": person.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(person.pk)

    def test_get_person_not_found(self, authenticated_client):
        """Test getting a non-existent person."""
        import uuid
        url = reverse("person-detail", kwargs={"pk": uuid.uuid4()})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Person Update Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonUpdateAPI:
    """Tests for Person update endpoint."""

    def test_update_person_unauthenticated(self, api_client, person):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-detail", kwargs={"pk": person.pk})

        response = api_client.put(url, {"first_name": "Updated"})

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_person_full(self, authenticated_client, person):
        """Test full update of a person."""
        url = reverse("person-detail", kwargs={"pk": person.pk})
        data = {
            "first_name": "Updated",
            "last_name": "Name",
        }

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"

    def test_update_person_partial(self, authenticated_client, person):
        """Test partial update of a person."""
        url = reverse("person-detail", kwargs={"pk": person.pk})
        original_last_name = person.last_name
        data = {"first_name": "Patched"}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Patched"
        # Last name should remain unchanged
        assert response.data["last_name"] == original_last_name


# =============================================================================
# Person Delete Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonDeleteAPI:
    """Tests for Person delete endpoint (soft delete)."""

    def test_delete_person_unauthenticated(self, api_client, person):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-detail", kwargs={"pk": person.pk})

        response = api_client.delete(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_person_soft_delete(self, authenticated_client, person):
        """Test soft deleting a person."""
        url = reverse("person-detail", kwargs={"pk": person.pk})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Person should still exist but be inactive
        person.refresh_from_db()
        assert person.is_active is False


# =============================================================================
# Person Relationships Endpoint Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonRelationshipsAPI:
    """Tests for Person relationships nested endpoint."""

    def test_get_person_relationships(self, authenticated_client, person):
        """Test getting relationships for a person."""
        other = PersonFactory()
        rt = RelationshipTypeFactory()
        RelationshipFactory(person_a=person, person_b=other, relationship_type=rt)

        url = reverse("person-relationships", kwargs={"pk": person.pk})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_get_person_relationships_empty(self, authenticated_client, person):
        """Test getting relationships when none exist."""
        url = reverse("person-relationships", kwargs={"pk": person.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Person Anecdotes Endpoint Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonAnecdotesAPI:
    """Tests for Person anecdotes nested endpoint."""

    def test_get_person_anecdotes(self, authenticated_client, person):
        """Test getting anecdotes for a person."""
        anecdote = AnecdoteFactory()
        anecdote.persons.add(person)

        url = reverse("person-anecdotes", kwargs={"pk": person.pk})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Person Photos Endpoint Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonPhotosAPI:
    """Tests for Person photos nested endpoint."""

    def test_get_person_photos(self, authenticated_client, person):
        """Test getting photos for a person."""
        photo = PhotoFactory()
        photo.persons.add(person)

        url = reverse("person-photos", kwargs={"pk": person.pk})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Person Employments Endpoint Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonEmploymentsAPI:
    """Tests for Person employments nested endpoint."""

    def test_get_person_employments(self, authenticated_client, person):
        """Test getting employments for a person."""
        EmploymentFactory(person=person)

        url = reverse("person-employments", kwargs={"pk": person.pk})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Person History Endpoint Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonHistoryAPI:
    """Tests for Person audit history endpoint."""

    def test_get_person_history(self, authenticated_client, person):
        """Test getting audit history for a person."""
        url = reverse("person-history", kwargs={"pk": person.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
