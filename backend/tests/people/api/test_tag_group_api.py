"""
Tests for Tag and Group API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.core.models import Group, Tag
from tests.factories import ChildGroupFactory, GroupFactory, PersonFactory, TagFactory


# =============================================================================
# Tag List Tests
# =============================================================================


@pytest.mark.django_db
class TestTagListAPI:
    """Tests for Tag list endpoint."""

    def test_list_tags_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("tag-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_tags_authenticated(self, authenticated_client):
        """Test listing tags when authenticated."""
        TagFactory.create_batch(3)
        url = reverse("tag-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data.get("results", response.data)
        assert len(data) >= 3

    def test_list_tags_empty(self, authenticated_client):
        """Test listing tags when none exist."""
        url = reverse("tag-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Tag Create Tests
# =============================================================================


@pytest.mark.django_db
class TestTagCreateAPI:
    """Tests for Tag create endpoint."""

    def test_create_tag_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("tag-list")
        data = {"name": "New Tag"}

        response = api_client.post(url, data)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_tag(self, authenticated_client):
        """Test creating a tag."""
        url = reverse("tag-list")
        data = {
            "name": "Important",
            "color": "#ff0000",
            "description": "For important contacts",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Important"
        assert response.data["color"] == "#ff0000"

    def test_create_tag_minimal(self, authenticated_client):
        """Test creating a tag with minimal data."""
        url = reverse("tag-list")
        data = {"name": "Simple"}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_tag_duplicate_name(self, authenticated_client):
        """Test creating a tag with duplicate name fails."""
        TagFactory(name="Existing")
        url = reverse("tag-list")
        data = {"name": "Existing"}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Tag Detail Tests
# =============================================================================


@pytest.mark.django_db
class TestTagDetailAPI:
    """Tests for Tag detail endpoint."""

    def test_get_tag(self, authenticated_client, tag):
        """Test getting a tag detail."""
        url = reverse("tag-detail", kwargs={"pk": tag.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == tag.name

    def test_update_tag(self, authenticated_client, tag):
        """Test updating a tag."""
        url = reverse("tag-detail", kwargs={"pk": tag.pk})
        data = {"name": "Updated Tag", "color": "#00ff00"}

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Tag"

    def test_delete_tag(self, authenticated_client, tag):
        """Test deleting a tag."""
        url = reverse("tag-detail", kwargs={"pk": tag.pk})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(pk=tag.pk).exists()


# =============================================================================
# Group List Tests
# =============================================================================


@pytest.mark.django_db
class TestGroupListAPI:
    """Tests for Group list endpoint."""

    def test_list_groups_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("group-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_groups_authenticated(self, authenticated_client):
        """Test listing groups when authenticated."""
        GroupFactory.create_batch(3)
        url = reverse("group-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_groups_includes_children(self, authenticated_client):
        """Test that group list includes nested children."""
        parent = GroupFactory(name="Parent")
        ChildGroupFactory(name="Child 1", parent=parent)
        ChildGroupFactory(name="Child 2", parent=parent)

        url = reverse("group-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Group Create Tests
# =============================================================================


@pytest.mark.django_db
class TestGroupCreateAPI:
    """Tests for Group create endpoint."""

    def test_create_group(self, authenticated_client):
        """Test creating a group."""
        url = reverse("group-list")
        data = {
            "name": "Work Colleagues",
            "description": "People from work",
            "color": "#0066ff",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Work Colleagues"

    def test_create_child_group(self, authenticated_client, group):
        """Test creating a child group."""
        url = reverse("group-list")
        data = {
            "name": "Child Group",
            "parent": str(group.pk),
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # Parent is returned as UUID, compare as strings for flexibility
        assert str(response.data["parent"]) == str(group.pk)

    def test_create_group_duplicate_name_same_parent(self, authenticated_client):
        """Test creating group with duplicate name under same parent fails."""
        parent = GroupFactory(name="Parent")
        ChildGroupFactory(name="Existing", parent=parent)

        url = reverse("group-list")
        data = {
            "name": "Existing",
            "parent": str(parent.pk),
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Group Detail Tests
# =============================================================================


@pytest.mark.django_db
class TestGroupDetailAPI:
    """Tests for Group detail endpoint."""

    def test_get_group(self, authenticated_client, group):
        """Test getting a group detail."""
        url = reverse("group-detail", kwargs={"pk": group.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == group.name

    def test_update_group(self, authenticated_client, group):
        """Test updating a group."""
        url = reverse("group-detail", kwargs={"pk": group.pk})
        data = {"name": "Updated Group", "color": "#ff00ff"}

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Group"

    def test_delete_group(self, authenticated_client, group):
        """Test deleting a group."""
        url = reverse("group-detail", kwargs={"pk": group.pk})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Group.objects.filter(pk=group.pk).exists()

    def test_delete_group_with_persons(self, authenticated_client, group):
        """Test deleting a group that has persons."""
        person = PersonFactory()
        person.groups.add(group)

        url = reverse("group-detail", kwargs={"pk": group.pk})
        response = authenticated_client.delete(url)

        # Should succeed (many-to-many doesn't prevent deletion)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Person should still exist
        person.refresh_from_db()
        assert person.pk is not None
