"""
Tests for Anecdote API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.people.models import Anecdote
from tests.factories import AnecdoteFactory, PersonFactory, TagFactory


# =============================================================================
# Anecdote List Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteListAPI:
    """Tests for Anecdote list endpoint."""

    def test_list_anecdotes_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("anecdote-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_anecdotes(self, authenticated_client):
        """Test listing anecdotes."""
        AnecdoteFactory.create_batch(3)
        url = reverse("anecdote-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_filter_anecdotes_by_type(self, authenticated_client):
        """Test filtering anecdotes by type."""
        AnecdoteFactory(anecdote_type=Anecdote.AnecdoteType.MEMORY)
        AnecdoteFactory(anecdote_type=Anecdote.AnecdoteType.JOKE)

        url = reverse("anecdote-list")
        response = authenticated_client.get(url, {"anecdote_type": "memory"})

        assert response.status_code == status.HTTP_200_OK

    def test_filter_anecdotes_by_person(self, authenticated_client):
        """Test filtering anecdotes by person."""
        person = PersonFactory()
        anecdote = AnecdoteFactory()
        anecdote.persons.add(person)
        AnecdoteFactory()  # Different anecdote

        url = reverse("anecdote-list")
        response = authenticated_client.get(url, {"persons": person.pk})

        assert response.status_code == status.HTTP_200_OK

    def test_search_anecdotes(self, authenticated_client):
        """Test searching anecdotes."""
        AnecdoteFactory(title="Birthday Party", content="Had a great time")
        AnecdoteFactory(title="Work Meeting", content="Discussed project")

        url = reverse("anecdote-list")
        response = authenticated_client.get(url, {"search": "Birthday"})

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Anecdote Create Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteCreateAPI:
    """Tests for Anecdote create endpoint."""

    def test_create_anecdote(self, authenticated_client):
        """Test creating an anecdote."""
        person = PersonFactory()
        url = reverse("anecdote-list")
        data = {
            "title": "Great Memory",
            "content": "We had a wonderful time at the beach.",
            "anecdote_type": "memory",
            "person_ids": [str(person.pk)],  # person_ids is required
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Great Memory"

    def test_create_anecdote_with_persons(self, authenticated_client):
        """Test creating an anecdote with associated persons."""
        person1 = PersonFactory()
        person2 = PersonFactory()

        url = reverse("anecdote-list")
        data = {
            "title": "Group Trip",
            "content": "We went hiking together.",
            "anecdote_type": "memory",
            "person_ids": [str(person1.pk), str(person2.pk)],
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_anecdote_with_tags(self, authenticated_client):
        """Test creating an anecdote with tags."""
        person = PersonFactory()
        tag = TagFactory(name="Fun")

        url = reverse("anecdote-list")
        data = {
            "title": "Fun Event",
            "content": "Such a fun time!",
            "anecdote_type": "memory",
            "person_ids": [str(person.pk)],
            "tag_ids": [str(tag.pk)],
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_anecdote_with_date_location(self, authenticated_client):
        """Test creating an anecdote with date and location."""
        person = PersonFactory()
        url = reverse("anecdote-list")
        data = {
            "title": "Conference Talk",
            "content": "Gave a great presentation.",
            "anecdote_type": "note",
            "date": "2023-06-15",
            "location": "San Francisco",
            "person_ids": [str(person.pk)],
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["date"] == "2023-06-15"
        assert response.data["location"] == "San Francisco"

    def test_create_quote_anecdote(self, authenticated_client):
        """Test creating a quote type anecdote."""
        person = PersonFactory()

        url = reverse("anecdote-list")
        data = {
            "content": "The only way to do great work is to love what you do.",
            "anecdote_type": "quote",
            "person_ids": [str(person.pk)],
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["anecdote_type"] == "quote"


# =============================================================================
# Anecdote Detail Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteDetailAPI:
    """Tests for Anecdote detail endpoint."""

    def test_get_anecdote(self, authenticated_client, anecdote):
        """Test getting an anecdote detail."""
        url = reverse("anecdote-detail", kwargs={"pk": anecdote.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_update_anecdote(self, authenticated_client, anecdote):
        """Test updating an anecdote."""
        url = reverse("anecdote-detail", kwargs={"pk": anecdote.pk})
        data = {
            "title": "Updated Title",
            "content": "Updated content with more details.",
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"

    def test_update_anecdote_add_persons(self, authenticated_client, anecdote):
        """Test adding persons to an existing anecdote."""
        new_person = PersonFactory()
        url = reverse("anecdote-detail", kwargs={"pk": anecdote.pk})
        data = {
            "person_ids": [str(new_person.pk)],
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_delete_anecdote(self, authenticated_client, anecdote):
        """Test deleting an anecdote."""
        url = reverse("anecdote-detail", kwargs={"pk": anecdote.pk})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Anecdote.objects.filter(pk=anecdote.pk).exists()


# =============================================================================
# Anecdote Validation Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteValidationAPI:
    """Tests for Anecdote validation."""

    def test_create_anecdote_missing_content(self, authenticated_client):
        """Test that content is required."""
        person = PersonFactory()
        url = reverse("anecdote-list")
        data = {
            "title": "No Content",
            "anecdote_type": "memory",
            "person_ids": [str(person.pk)],
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_anecdote_invalid_type(self, authenticated_client):
        """Test that invalid anecdote type is rejected."""
        person = PersonFactory()
        url = reverse("anecdote-list")
        data = {
            "content": "Some content",
            "anecdote_type": "invalid_type",
            "person_ids": [str(person.pk)],
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
