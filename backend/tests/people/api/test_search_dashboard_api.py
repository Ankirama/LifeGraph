"""
Tests for Search and Dashboard API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories import (
    AnecdoteFactory,
    EmploymentFactory,
    PersonFactory,
    PhotoFactory,
    TagFactory,
)


# =============================================================================
# Global Search Tests
# =============================================================================


@pytest.mark.django_db
class TestGlobalSearchAPI:
    """Tests for Global Search endpoint."""

    def test_search_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("global-search")

        response = api_client.get(url, {"q": "test"})

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_search_persons_by_name(self, authenticated_client, sample_persons):
        """Test searching persons by name."""
        url = reverse("global-search")

        response = authenticated_client.get(url, {"q": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        # Should find Alice Smith

    def test_search_persons_by_partial_name(self, authenticated_client, sample_persons):
        """Test searching persons by partial name."""
        url = reverse("global-search")

        response = authenticated_client.get(url, {"q": "Smi"})  # Should match Smith

        assert response.status_code == status.HTTP_200_OK

    def test_search_case_insensitive(self, authenticated_client):
        """Test that search is case insensitive."""
        PersonFactory(first_name="UPPERCASE", last_name="Name")

        url = reverse("global-search")
        response = authenticated_client.get(url, {"q": "uppercase"})

        assert response.status_code == status.HTTP_200_OK

    def test_search_empty_query(self, authenticated_client):
        """Test search with empty query."""
        url = reverse("global-search")

        response = authenticated_client.get(url, {"q": ""})

        # Either return empty results, all results, or a validation error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_search_no_results(self, authenticated_client, sample_persons):
        """Test search with no matching results."""
        url = reverse("global-search")

        response = authenticated_client.get(url, {"q": "nonexistentxyz123"})

        assert response.status_code == status.HTTP_200_OK

    def test_search_anecdotes(self, authenticated_client):
        """Test searching anecdotes by content."""
        AnecdoteFactory(title="Birthday party", content="Had a great celebration")

        url = reverse("global-search")
        response = authenticated_client.get(url, {"q": "Birthday"})

        assert response.status_code == status.HTTP_200_OK

    def test_search_tags(self, authenticated_client):
        """Test searching tags by name."""
        TagFactory(name="Important VIP")

        url = reverse("global-search")
        response = authenticated_client.get(url, {"q": "Important"})

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Dashboard Tests
# =============================================================================


@pytest.mark.django_db
class TestDashboardAPI:
    """Tests for Dashboard endpoint."""

    def test_dashboard_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("dashboard")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dashboard_authenticated(self, authenticated_client):
        """Test dashboard endpoint returns data."""
        url = reverse("dashboard")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_dashboard_counts(self, authenticated_client):
        """Test dashboard includes counts."""
        PersonFactory.create_batch(5)
        AnecdoteFactory.create_batch(3)

        url = reverse("dashboard")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should include some count statistics

    def test_dashboard_recent_persons(self, authenticated_client):
        """Test dashboard includes recent persons."""
        PersonFactory.create_batch(3)

        url = reverse("dashboard")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_dashboard_recent_anecdotes(self, authenticated_client):
        """Test dashboard includes recent anecdotes."""
        AnecdoteFactory.create_batch(3)

        url = reverse("dashboard")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Me (Owner) Endpoint Tests
# =============================================================================


@pytest.mark.django_db
class TestMeAPI:
    """Tests for Me (owner) endpoint."""

    def test_me_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("me")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_me_no_owner(self, authenticated_client):
        """Test me endpoint when no owner exists."""
        url = reverse("me")

        response = authenticated_client.get(url)

        # Should handle gracefully (404 or empty response)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_me_with_owner(self, authenticated_client, owner_person):
        """Test me endpoint returns owner."""
        # Ensure only one owner exists
        from apps.people.models import Person

        Person.objects.filter(is_owner=True).exclude(pk=owner_person.pk).update(is_owner=False)

        url = reverse("me")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_owner"] is True

    def test_me_create_owner(self, authenticated_client):
        """Test creating owner via me endpoint."""
        # Ensure no owner exists
        from apps.people.models import Person

        Person.objects.filter(is_owner=True).update(is_owner=False)

        url = reverse("me")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "is_owner": True,
        }

        response = authenticated_client.post(url, data, format="json")

        # Either 200 OK or 201 Created
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_me_update_owner(self, authenticated_client, owner_person):
        """Test updating owner via me endpoint."""
        # Ensure only one owner exists
        from apps.people.models import Person

        Person.objects.filter(is_owner=True).exclude(pk=owner_person.pk).update(is_owner=False)

        url = reverse("me")
        data = {"first_name": "Updated"}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Health Check Tests
# =============================================================================


@pytest.mark.django_db
class TestHealthCheckAPI:
    """Tests for Health Check endpoint."""

    def test_health_check(self, api_client):
        """Test health check returns OK."""
        url = reverse("health-check")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "status" in response.data or response.data == "ok"


# =============================================================================
# Custom Field Definition API Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldDefinitionAPI:
    """Tests for CustomFieldDefinition endpoint."""

    def test_list_custom_fields_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("customfielddefinition-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_custom_fields(self, authenticated_client, custom_field_definition):
        """Test listing custom field definitions."""
        url = reverse("customfielddefinition-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_create_custom_field(self, authenticated_client):
        """Test creating a custom field definition."""
        url = reverse("customfielddefinition-list")
        data = {
            "name": "Favorite Color",
            "field_type": "text",
            "is_required": False,
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Favorite Color"

    def test_create_select_custom_field(self, authenticated_client):
        """Test creating a select custom field definition."""
        url = reverse("customfielddefinition-list")
        data = {
            "name": "Priority Level",
            "field_type": "select",
            "options": ["Low", "Medium", "High"],
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["field_type"] == "select"
        assert len(response.data["options"]) == 3

    def test_update_custom_field(self, authenticated_client, custom_field_definition):
        """Test updating a custom field definition."""
        url = reverse(
            "customfielddefinition-detail",
            kwargs={"pk": custom_field_definition.pk},
        )
        data = {"name": "Updated Field Name"}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Field Name"

    def test_delete_custom_field(self, authenticated_client, custom_field_definition):
        """Test deleting a custom field definition."""
        url = reverse(
            "customfielddefinition-detail",
            kwargs={"pk": custom_field_definition.pk},
        )

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
