"""
Tests for core models: Tag and Group.
"""

import pytest

from apps.core.models import Group, Tag
from tests.factories import ChildGroupFactory, GroupFactory, TagFactory


# =============================================================================
# Tag Model Tests
# =============================================================================


@pytest.mark.django_db
class TestTagModel:
    """Tests for the Tag model."""

    def test_create_tag(self):
        """Test creating a basic tag."""
        tag = TagFactory(name="Test Tag", color="#ff0000", description="A test tag")

        assert tag.name == "Test Tag"
        assert tag.color == "#ff0000"
        assert tag.description == "A test tag"
        assert tag.pk is not None

    def test_tag_str_representation(self):
        """Test the string representation of a tag."""
        tag = TagFactory(name="My Tag")

        assert str(tag) == "My Tag"

    def test_tag_unique_name(self):
        """Test that tag names must be unique."""
        TagFactory(name="Unique Tag")

        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Tag.objects.create(name="Unique Tag")

    def test_tag_default_color(self):
        """Test that tags have a default color."""
        tag = Tag.objects.create(name="Color Test")

        assert tag.color == "#6366f1"

    def test_tag_ordering(self):
        """Test that tags are ordered by name."""
        TagFactory(name="Zebra")
        TagFactory(name="Apple")
        TagFactory(name="Mango")

        tags = list(Tag.objects.all())

        assert tags[0].name == "Apple"
        assert tags[1].name == "Mango"
        assert tags[2].name == "Zebra"

    def test_tag_description_optional(self):
        """Test that tag description is optional."""
        tag = Tag.objects.create(name="No Description")

        assert tag.description == ""

    def test_tag_timestamps(self):
        """Test that tags have created_at and updated_at timestamps."""
        tag = TagFactory()

        assert tag.created_at is not None
        assert tag.updated_at is not None

    def test_tag_get_or_create(self):
        """Test factory uses get_or_create for tags."""
        tag1 = TagFactory(name="Same Tag")
        tag2 = TagFactory(name="Same Tag")

        assert tag1.pk == tag2.pk


# =============================================================================
# Group Model Tests
# =============================================================================


@pytest.mark.django_db
class TestGroupModel:
    """Tests for the Group model."""

    def test_create_group(self):
        """Test creating a basic group."""
        group = GroupFactory(
            name="Test Group",
            description="A test group",
            color="#00ff00",
        )

        assert group.name == "Test Group"
        assert group.description == "A test group"
        assert group.color == "#00ff00"
        assert group.parent is None
        assert group.pk is not None

    def test_group_str_representation(self):
        """Test the string representation of a group."""
        group = GroupFactory(name="My Group")

        assert str(group) == "My Group"

    def test_group_with_parent_str(self):
        """Test string representation includes parent."""
        parent = GroupFactory(name="Parent")
        child = ChildGroupFactory(name="Child", parent=parent)

        assert str(child) == "Parent > Child"

    def test_group_full_path_single(self):
        """Test full_path property for single group."""
        group = GroupFactory(name="Single Group")

        assert group.full_path == "Single Group"

    def test_group_full_path_nested(self):
        """Test full_path property for nested groups."""
        grandparent = GroupFactory(name="Grandparent")
        parent = ChildGroupFactory(name="Parent", parent=grandparent)
        child = ChildGroupFactory(name="Child", parent=parent)

        assert child.full_path == "Grandparent > Parent > Child"

    def test_group_default_color(self):
        """Test that groups have a default color."""
        group = Group.objects.create(name="Color Test")

        assert group.color == "#8b5cf6"

    def test_group_unique_name_per_parent(self):
        """Test that group names must be unique within same parent."""
        parent = GroupFactory(name="Parent")
        ChildGroupFactory(name="Duplicate", parent=parent)

        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Group.objects.create(name="Duplicate", parent=parent)

    def test_group_same_name_different_parent(self):
        """Test that same name is allowed with different parents."""
        parent1 = GroupFactory(name="Parent 1")
        parent2 = GroupFactory(name="Parent 2")

        group1 = ChildGroupFactory(name="Same Name", parent=parent1)
        group2 = ChildGroupFactory(name="Same Name", parent=parent2)

        assert group1.name == group2.name
        assert group1.pk != group2.pk

    def test_group_ordering(self):
        """Test that groups are ordered by name."""
        GroupFactory(name="Zebra Group")
        GroupFactory(name="Apple Group")
        GroupFactory(name="Mango Group")

        groups = list(Group.objects.filter(parent=None))

        assert groups[0].name == "Apple Group"
        assert groups[1].name == "Mango Group"
        assert groups[2].name == "Zebra Group"

    def test_group_children_relationship(self):
        """Test the children relationship."""
        parent = GroupFactory(name="Parent")
        child1 = ChildGroupFactory(name="Child 1", parent=parent)
        child2 = ChildGroupFactory(name="Child 2", parent=parent)

        children = list(parent.children.all())

        assert len(children) == 2
        assert child1 in children
        assert child2 in children

    def test_group_cascade_delete(self):
        """Test that deleting parent cascades to children."""
        parent = GroupFactory(name="Parent")
        child = ChildGroupFactory(name="Child", parent=parent)
        child_id = child.pk

        parent.delete()

        assert not Group.objects.filter(pk=child_id).exists()

    def test_group_timestamps(self):
        """Test that groups have created_at and updated_at timestamps."""
        group = GroupFactory()

        assert group.created_at is not None
        assert group.updated_at is not None


# =============================================================================
# Tag-Person Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestTagPersonRelationship:
    """Tests for Tag-Person many-to-many relationship."""

    def test_add_tags_to_person(self):
        """Test adding tags to a person."""
        from tests.factories import PersonFactory

        person = PersonFactory()
        tag1 = TagFactory(name="Friend")
        tag2 = TagFactory(name="Colleague")

        person.tags.add(tag1, tag2)

        assert person.tags.count() == 2
        assert tag1 in person.tags.all()
        assert tag2 in person.tags.all()

    def test_get_persons_by_tag(self):
        """Test getting persons associated with a tag."""
        from tests.factories import PersonFactory

        tag = TagFactory(name="VIP")
        person1 = PersonFactory()
        person2 = PersonFactory()
        person3 = PersonFactory()

        person1.tags.add(tag)
        person2.tags.add(tag)

        tagged_persons = list(tag.persons.all())

        assert len(tagged_persons) == 2
        assert person1 in tagged_persons
        assert person2 in tagged_persons
        assert person3 not in tagged_persons

    def test_remove_tag_from_person(self):
        """Test removing a tag from a person."""
        from tests.factories import PersonFactory

        person = PersonFactory()
        tag = TagFactory(name="Temporary")
        person.tags.add(tag)

        person.tags.remove(tag)

        assert tag not in person.tags.all()


# =============================================================================
# Group-Person Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestGroupPersonRelationship:
    """Tests for Group-Person many-to-many relationship."""

    def test_add_person_to_groups(self):
        """Test adding a person to groups."""
        from tests.factories import PersonFactory

        person = PersonFactory()
        group1 = GroupFactory(name="Family")
        group2 = GroupFactory(name="Work")

        person.groups.add(group1, group2)

        assert person.groups.count() == 2
        assert group1 in person.groups.all()
        assert group2 in person.groups.all()

    def test_get_persons_in_group(self):
        """Test getting persons in a group."""
        from tests.factories import PersonFactory

        group = GroupFactory(name="Friends")
        person1 = PersonFactory()
        person2 = PersonFactory()
        person3 = PersonFactory()

        person1.groups.add(group)
        person2.groups.add(group)

        group_members = list(group.persons.all())

        assert len(group_members) == 2
        assert person1 in group_members
        assert person2 in group_members
        assert person3 not in group_members

    def test_person_in_nested_groups(self):
        """Test person can be in nested group hierarchy."""
        from tests.factories import PersonFactory

        parent = GroupFactory(name="Company")
        child = ChildGroupFactory(name="Engineering", parent=parent)
        grandchild = ChildGroupFactory(name="Backend Team", parent=child)

        person = PersonFactory()
        person.groups.add(grandchild)

        assert grandchild in person.groups.all()
        # Note: Person is only in the groups they're explicitly added to
        assert parent not in person.groups.all()
