"""
Tests for core app serializers.

Tests TagSerializer, GroupSerializer.
"""

import pytest

from apps.core.models import Group, Tag
from apps.core.serializers import GroupSerializer, TagSerializer
from tests.factories import GroupFactory, TagFactory


# =============================================================================
# TagSerializer Tests
# =============================================================================


@pytest.mark.django_db
class TestTagSerializer:
    """Tests for TagSerializer."""

    def test_serializes_tag(self):
        """TagSerializer correctly serializes a tag."""
        tag = TagFactory(name="Friend", color="#ff0000", description="Close friends")
        serializer = TagSerializer(tag)
        data = serializer.data

        assert data["id"] == str(tag.id)
        assert data["name"] == "Friend"
        assert data["color"] == "#ff0000"
        assert data["description"] == "Close friends"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_tag(self):
        """TagSerializer can create a tag."""
        data = {
            "name": "New Tag",
            "color": "#00ff00",
            "description": "A new tag",
        }
        serializer = TagSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        tag = serializer.save()

        assert tag.name == "New Tag"
        assert tag.color == "#00ff00"
        assert tag.description == "A new tag"

    def test_create_tag_minimal(self):
        """TagSerializer can create a tag with minimal data."""
        data = {"name": "Minimal Tag"}
        serializer = TagSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        tag = serializer.save()

        assert tag.name == "Minimal Tag"

    def test_update_tag(self):
        """TagSerializer can update a tag."""
        tag = TagFactory(name="Original Name")
        data = {"name": "Updated Name", "color": "#ffffff"}
        serializer = TagSerializer(tag, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated_tag = serializer.save()

        assert updated_tag.name == "Updated Name"
        assert updated_tag.color == "#ffffff"

    def test_read_only_fields(self):
        """TagSerializer has correct read-only fields."""
        tag = TagFactory()
        data = {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "Test",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
        }
        serializer = TagSerializer(tag, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        # Read-only fields should not change
        assert str(updated.id) == str(tag.id)
        assert updated.name == "Test"
        # created_at should remain original

    def test_validates_required_name(self):
        """TagSerializer validates that name is required."""
        data = {"color": "#ff0000"}
        serializer = TagSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors


# =============================================================================
# GroupSerializer Tests
# =============================================================================


@pytest.mark.django_db
class TestGroupSerializer:
    """Tests for GroupSerializer."""

    def test_serializes_group(self):
        """GroupSerializer correctly serializes a group."""
        group = GroupFactory(name="Work", description="Work contacts", color="#0000ff")
        serializer = GroupSerializer(group)
        data = serializer.data

        assert data["id"] == str(group.id)
        assert data["name"] == "Work"
        assert data["description"] == "Work contacts"
        assert data["color"] == "#0000ff"
        assert data["parent"] is None
        assert "full_path" in data
        assert "children_count" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_serializes_full_path(self):
        """GroupSerializer includes full_path property."""
        parent = GroupFactory(name="Company")
        child = GroupFactory(name="Engineering", parent=parent)
        grandchild = GroupFactory(name="Backend", parent=child)

        serializer = GroupSerializer(grandchild)
        assert serializer.data["full_path"] == "Company > Engineering > Backend"

    def test_serializes_children_count(self):
        """GroupSerializer includes children_count."""
        parent = GroupFactory(name="Parent")
        GroupFactory(parent=parent)
        GroupFactory(parent=parent)
        GroupFactory(parent=parent)

        serializer = GroupSerializer(parent)
        assert serializer.data["children_count"] == 3

    def test_serializes_children_count_zero(self):
        """GroupSerializer returns 0 for groups with no children."""
        group = GroupFactory(name="Leaf")
        serializer = GroupSerializer(group)
        assert serializer.data["children_count"] == 0

    def test_create_group(self):
        """GroupSerializer can create a group."""
        data = {
            "name": "New Group",
            "description": "A new group",
            "color": "#ff00ff",
        }
        serializer = GroupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        group = serializer.save()

        assert group.name == "New Group"
        assert group.description == "A new group"
        assert group.color == "#ff00ff"

    def test_create_group_with_parent(self):
        """GroupSerializer can create a group with a parent."""
        parent = GroupFactory(name="Parent")
        data = {
            "name": "Child Group",
            "parent": str(parent.id),
        }
        serializer = GroupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        group = serializer.save()

        assert group.name == "Child Group"
        assert group.parent == parent

    def test_update_group(self):
        """GroupSerializer can update a group."""
        group = GroupFactory(name="Original")
        data = {"name": "Updated", "description": "New description"}
        serializer = GroupSerializer(group, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        assert updated.name == "Updated"
        assert updated.description == "New description"

    def test_update_group_parent(self):
        """GroupSerializer can update group's parent."""
        group = GroupFactory(name="Child")
        new_parent = GroupFactory(name="New Parent")
        data = {"parent": str(new_parent.id)}
        serializer = GroupSerializer(group, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        assert updated.parent == new_parent

    def test_read_only_fields(self):
        """GroupSerializer has correct read-only fields."""
        group = GroupFactory()
        data = {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "Test",
            "full_path": "Fake / Path",
            "children_count": 999,
        }
        serializer = GroupSerializer(group, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        # Read-only fields should not change
        assert str(updated.id) == str(group.id)
        assert updated.name == "Test"
        # full_path and children_count are computed, not stored

    def test_validates_required_name(self):
        """GroupSerializer validates that name is required."""
        data = {"description": "Test"}
        serializer = GroupSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_serializes_parent_as_uuid(self):
        """GroupSerializer serializes parent as UUID."""
        parent = GroupFactory(name="Parent")
        child = GroupFactory(name="Child", parent=parent)

        serializer = GroupSerializer(child)
        # Parent field might be returned as UUID object or string
        assert str(serializer.data["parent"]) == str(parent.id)
