"""
Tests for core app views.

Tests TagViewSet, GroupViewSet, GlobalSearchView, HealthCheckView.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories import GroupFactory, TagFactory


# =============================================================================
# HealthCheckView Tests
# =============================================================================


@pytest.mark.django_db
class TestHealthCheckView:
    """Tests for the health check endpoint."""

    def test_health_check_returns_healthy(self, api_client):
        """Health check returns healthy status."""
        response = api_client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert response.data["service"] == "lifegraph-api"

    def test_health_check_no_auth_required(self, api_client):
        """Health check doesn't require authentication."""
        response = api_client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TagViewSet Tests
# =============================================================================


@pytest.mark.django_db
class TestTagViewSet:
    """Tests for Tag CRUD operations."""

    def test_list_tags(self, authenticated_client):
        """List all tags."""
        TagFactory.create_batch(3)
        response = authenticated_client.get("/api/v1/tags/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_tags_empty(self, authenticated_client):
        """List tags returns empty when no tags exist."""
        response = authenticated_client.get("/api/v1/tags/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_create_tag(self, authenticated_client):
        """Create a new tag."""
        data = {
            "name": "Test Tag",
            "color": "#ff0000",
            "description": "A test tag",
        }
        response = authenticated_client.post("/api/v1/tags/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Tag"
        assert response.data["color"] == "#ff0000"

    def test_create_tag_minimal(self, authenticated_client):
        """Create a tag with minimal data (only required fields)."""
        data = {"name": "Minimal Tag"}
        response = authenticated_client.post("/api/v1/tags/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Minimal Tag"

    def test_create_tag_duplicate_name_fails(self, authenticated_client):
        """Creating a tag with duplicate name fails."""
        TagFactory(name="Existing Tag")
        data = {"name": "Existing Tag"}
        response = authenticated_client.post("/api/v1/tags/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_tag(self, authenticated_client, tag):
        """Retrieve a single tag."""
        response = authenticated_client.get(f"/api/v1/tags/{tag.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(tag.id)
        assert response.data["name"] == tag.name

    def test_retrieve_nonexistent_tag(self, authenticated_client):
        """Retrieve nonexistent tag returns 404."""
        response = authenticated_client.get("/api/v1/tags/00000000-0000-0000-0000-000000000000/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_tag(self, authenticated_client, tag):
        """Update a tag."""
        data = {"name": "Updated Tag Name", "color": "#00ff00"}
        response = authenticated_client.patch(f"/api/v1/tags/{tag.id}/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Tag Name"
        assert response.data["color"] == "#00ff00"

    def test_delete_tag(self, authenticated_client, tag):
        """Delete a tag."""
        response = authenticated_client.delete(f"/api/v1/tags/{tag.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        response = authenticated_client.get(f"/api/v1/tags/{tag.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_tags(self, authenticated_client):
        """Search tags by name."""
        TagFactory(name="Work Colleague")
        TagFactory(name="Friend")
        TagFactory(name="Family Member")

        response = authenticated_client.get("/api/v1/tags/?search=friend")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Friend"

    def test_ordering_tags(self, authenticated_client):
        """Tags can be ordered by name."""
        TagFactory(name="Zebra")
        TagFactory(name="Apple")
        TagFactory(name="Mango")

        response = authenticated_client.get("/api/v1/tags/?ordering=name")
        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data["results"]]
        assert names == ["Apple", "Mango", "Zebra"]


# =============================================================================
# GroupViewSet Tests
# =============================================================================


@pytest.mark.django_db
class TestGroupViewSet:
    """Tests for Group CRUD operations."""

    def test_list_groups(self, authenticated_client):
        """List all groups."""
        GroupFactory.create_batch(3)
        response = authenticated_client.get("/api/v1/groups/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_groups_empty(self, authenticated_client):
        """List groups returns empty when no groups exist."""
        response = authenticated_client.get("/api/v1/groups/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_create_group(self, authenticated_client):
        """Create a new group."""
        data = {
            "name": "Test Group",
            "description": "A test group",
            "color": "#0000ff",
        }
        response = authenticated_client.post("/api/v1/groups/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Group"

    def test_create_group_with_parent(self, authenticated_client, group):
        """Create a group with a parent group."""
        data = {
            "name": "Child Group",
            "parent": str(group.id),
        }
        response = authenticated_client.post("/api/v1/groups/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        # Parent field is returned as UUID object, compare strings
        assert str(response.data["parent"]) == str(group.id)

    def test_create_group_allows_duplicate_names(self, authenticated_client):
        """Creating groups with same name is allowed (unlike tags)."""
        GroupFactory(name="Existing Group")
        data = {"name": "Existing Group"}
        response = authenticated_client.post("/api/v1/groups/", data, format="json")
        # Groups don't have unique constraint on name
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_group(self, authenticated_client, group):
        """Retrieve a single group."""
        response = authenticated_client.get(f"/api/v1/groups/{group.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(group.id)
        assert response.data["name"] == group.name

    def test_retrieve_group_includes_full_path(self, authenticated_client):
        """Retrieve group includes full_path field."""
        parent = GroupFactory(name="Parent")
        child = GroupFactory(name="Child", parent=parent)

        response = authenticated_client.get(f"/api/v1/groups/{child.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_path"] == "Parent > Child"

    def test_retrieve_group_includes_children_count(self, authenticated_client):
        """Retrieve group includes children_count field."""
        parent = GroupFactory(name="Parent")
        GroupFactory(name="Child1", parent=parent)
        GroupFactory(name="Child2", parent=parent)

        response = authenticated_client.get(f"/api/v1/groups/{parent.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["children_count"] == 2

    def test_update_group(self, authenticated_client, group):
        """Update a group."""
        data = {"name": "Updated Group Name"}
        response = authenticated_client.patch(f"/api/v1/groups/{group.id}/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Group Name"

    def test_delete_group(self, authenticated_client, group):
        """Delete a group."""
        response = authenticated_client.delete(f"/api/v1/groups/{group.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_groups_by_parent(self, authenticated_client):
        """Filter groups by parent."""
        parent = GroupFactory(name="Parent")
        child1 = GroupFactory(name="Child1", parent=parent)
        child2 = GroupFactory(name="Child2", parent=parent)
        GroupFactory(name="Other")

        response = authenticated_client.get(f"/api/v1/groups/?parent={parent.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        result_ids = [r["id"] for r in response.data["results"]]
        assert str(child1.id) in result_ids
        assert str(child2.id) in result_ids

    def test_search_groups(self, authenticated_client):
        """Search groups by name."""
        GroupFactory(name="Work Team")
        GroupFactory(name="Family")
        GroupFactory(name="Friends Group")

        response = authenticated_client.get("/api/v1/groups/?search=family")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Family"


# =============================================================================
# GlobalSearchView Tests
# =============================================================================


@pytest.mark.django_db
class TestGlobalSearchView:
    """Tests for the global search endpoint (placeholder version)."""

    def test_search_requires_query(self, authenticated_client):
        """Search without query returns error."""
        response = authenticated_client.get("/api/v1/search/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Query must be at least 2 characters" in response.data["error"]

    def test_search_query_too_short(self, authenticated_client):
        """Search with single character returns error."""
        response = authenticated_client.get("/api/v1/search/?q=a")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Query must be at least 2 characters" in response.data["error"]

    def test_search_returns_structure(self, authenticated_client):
        """Search returns correct response structure."""
        response = authenticated_client.get("/api/v1/search/?q=test")
        assert response.status_code == status.HTTP_200_OK
        assert "persons" in response.data
        assert "anecdotes" in response.data
        assert "employments" in response.data
        assert response.data["query"] == "test"

    def test_search_empty_query_returns_error(self, authenticated_client):
        """Search with empty query returns error."""
        response = authenticated_client.get("/api/v1/search/?q=")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_whitespace_only_returns_error(self, authenticated_client):
        """Search with whitespace-only query returns error."""
        response = authenticated_client.get("/api/v1/search/?q=   ")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Rate Limited Error View Tests
# =============================================================================


@pytest.mark.django_db
class TestRateLimitedErrorView:
    """Tests for the rate limit error handler."""

    def test_ratelimited_error_returns_json(self):
        """Rate limited error returns JSON response."""
        import json
        from apps.core.views import ratelimited_error

        class MockException:
            retry_after = 120

        response = ratelimited_error(None, MockException())
        assert response.status_code == 429
        data = json.loads(response.content)
        assert data["error"] == "rate_limit_exceeded"
        assert data["retry_after"] == 120

    def test_ratelimited_error_default_retry_after(self):
        """Rate limited error uses default retry_after when not provided."""
        import json
        from apps.core.views import ratelimited_error

        class MockException:
            pass

        response = ratelimited_error(None, MockException())
        assert response.status_code == 429
        data = json.loads(response.content)
        assert data["retry_after"] == 60  # default
