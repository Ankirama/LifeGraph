"""
Integration/Workflow tests that simulate realistic user journeys.
These tests verify that the system works correctly across multiple operations.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.people.models import (
    Anecdote,
    CustomFieldDefinition,
    CustomFieldValue,
    Employment,
    Person,
    Photo,
    Relationship,
    RelationshipType,
)
from tests.factories import (
    AnecdoteFactory,
    CustomFieldDefinitionFactory,
    EmploymentFactory,
    GroupFactory,
    PersonFactory,
    PhotoFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
    TagFactory,
)


# =============================================================================
# Person Lifecycle Workflow Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonLifecycleWorkflow:
    """Test complete person lifecycle: create → enrich → update → delete."""

    def test_full_person_lifecycle(self, authenticated_client):
        """Test creating a person, adding data, updating, and soft deleting."""
        # Step 1: Create a new person via API
        url = reverse("person-list")
        create_data = {
            "first_name": "John",
            "last_name": "Doe",
            "emails": [{"email": "john.doe@example.com", "label": "work"}],
            "phones": [{"phone": "+1234567890", "label": "mobile"}],
            "notes": "Initial notes",
        }
        response = authenticated_client.post(url, create_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        person_id = response.data["id"]

        # Step 2: Verify person was created
        person = Person.objects.get(pk=person_id)
        assert person.first_name == "John"
        assert person.last_name == "Doe"
        assert person.primary_email == "john.doe@example.com"

        # Step 3: Add tags to the person
        tag1 = TagFactory(name="VIP")
        tag2 = TagFactory(name="Developer")
        person.tags.add(tag1, tag2)
        assert person.tags.count() == 2

        # Step 4: Add to a group
        group = GroupFactory(name="Work Contacts")
        person.groups.add(group)
        assert person.groups.count() == 1

        # Step 5: Update person via API
        detail_url = reverse("person-detail", kwargs={"pk": person_id})
        update_data = {
            "first_name": "John",
            "last_name": "Doe",
            "notes": "Updated notes - promoted to senior",
            "nickname": "Johnny",
        }
        response = authenticated_client.patch(detail_url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK

        # Step 6: Verify update
        person.refresh_from_db()
        assert "Updated notes" in person.notes
        assert person.nickname == "Johnny"

        # Step 7: Soft delete via API
        response = authenticated_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Step 8: Verify soft delete (person still exists but inactive)
        person.refresh_from_db()
        assert person.is_active is False

        # Step 9: Verify person doesn't appear in list
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        person_ids = [p["id"] for p in response.data.get("results", response.data)]
        assert str(person_id) not in person_ids

    def test_person_with_employment_lifecycle(self, authenticated_client):
        """Test person with employment history lifecycle."""
        # Create person
        person = PersonFactory(first_name="Alice", last_name="Engineer")

        # Add first employment
        emp1 = EmploymentFactory(
            person=person,
            company="StartupCo",
            title="Junior Developer",
            is_current=False,
        )

        # Add second (current) employment
        emp2 = EmploymentFactory(
            person=person,
            company="TechCorp",
            title="Senior Developer",
            is_current=True,
        )

        # Verify employment history
        assert person.employments.count() == 2
        assert person.employments.filter(is_current=True).count() == 1
        assert person.employments.get(is_current=True).company == "TechCorp"

        # Update current employment
        emp2.title = "Staff Developer"
        emp2.save()

        person.refresh_from_db()
        current_job = person.employments.get(is_current=True)
        assert current_job.title == "Staff Developer"

        # Delete old employment
        emp1.delete()
        assert person.employments.count() == 1

        # Soft delete person - employments should be preserved
        person.is_active = False
        person.save()

        # Employments still exist
        assert Employment.objects.filter(person=person).count() == 1


# =============================================================================
# Relationship Workflow Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipWorkflow:
    """Test creating and managing relationships between persons."""

    def test_create_symmetric_relationship_workflow(self):
        """Test creating a symmetric relationship and verifying inverse."""
        # Create two persons
        alice = PersonFactory(first_name="Alice")
        bob = PersonFactory(first_name="Bob")

        # Create symmetric relationship type
        friend_type = RelationshipTypeFactory(
            name="friend",
            inverse_name="friend",
            is_symmetric=True,
            auto_create_inverse=True,
        )

        # Create relationship Alice → Bob
        relationship = Relationship.objects.create(
            person_a=alice,
            person_b=bob,
            relationship_type=friend_type,
        )

        # Verify inverse was created (Bob → Alice)
        inverse = Relationship.objects.filter(
            person_a=bob,
            person_b=alice,
            relationship_type=friend_type,
        )
        assert inverse.exists()

        # Verify both persons can see the relationship
        assert alice.relationships_as_a.count() == 1
        assert bob.relationships_as_a.count() == 1

        # Delete one relationship - inverse should also be deleted
        relationship.delete()

        # Both should be gone
        assert alice.relationships_as_a.count() == 0
        assert bob.relationships_as_a.count() == 0

    def test_create_asymmetric_relationship_workflow(self):
        """Test creating parent/child asymmetric relationship."""
        parent = PersonFactory(first_name="Parent")
        child = PersonFactory(first_name="Child")

        # Create asymmetric relationship types
        parent_type = RelationshipTypeFactory(
            name="parent",
            inverse_name="child",
            is_symmetric=False,
            auto_create_inverse=True,
        )
        child_type = RelationshipTypeFactory(
            name="child",
            inverse_name="parent",
            is_symmetric=False,
        )

        # Create parent → child relationship
        Relationship.objects.create(
            person_a=parent,
            person_b=child,
            relationship_type=parent_type,
        )

        # Verify parent sees child
        parent_rels = parent.relationships_as_a.all()
        assert parent_rels.count() >= 1
        assert any(r.person_b == child for r in parent_rels)

        # Verify child sees parent (inverse relationship)
        child_rels = child.relationships_as_a.all()
        assert child_rels.count() >= 1

    def test_complex_relationship_network(self):
        """Test building a complex network of relationships."""
        # Create family members
        grandparent = PersonFactory(first_name="Grandparent")
        parent1 = PersonFactory(first_name="Parent1")
        parent2 = PersonFactory(first_name="Parent2")
        child1 = PersonFactory(first_name="Child1")
        child2 = PersonFactory(first_name="Child2")

        # Create relationship types
        parent_type = RelationshipTypeFactory(name="parent_of", is_symmetric=False)
        spouse_type = RelationshipTypeFactory(
            name="spouse", is_symmetric=True, auto_create_inverse=True
        )
        sibling_type = RelationshipTypeFactory(
            name="sibling", is_symmetric=True, auto_create_inverse=True
        )

        # Build relationships
        # Grandparent → Parent1
        RelationshipFactory(
            person_a=grandparent, person_b=parent1, relationship_type=parent_type
        )

        # Parent1 ↔ Parent2 (spouse)
        RelationshipFactory(
            person_a=parent1, person_b=parent2, relationship_type=spouse_type
        )

        # Parent1 → Child1, Child2
        RelationshipFactory(
            person_a=parent1, person_b=child1, relationship_type=parent_type
        )
        RelationshipFactory(
            person_a=parent1, person_b=child2, relationship_type=parent_type
        )

        # Child1 ↔ Child2 (siblings)
        RelationshipFactory(
            person_a=child1, person_b=child2, relationship_type=sibling_type
        )

        # Verify network
        assert grandparent.relationships_as_a.count() == 1
        assert parent1.relationships_as_a.count() >= 3  # spouse + 2 children
        assert child1.relationships_as_a.count() >= 1  # sibling

        # Delete one person - relationships should be cleaned up
        child2_id = child2.pk
        child2.delete()
        child1.refresh_from_db()

        # Child1's sibling relationship should be gone (check by ID)
        sibling_rels = child1.relationships_as_a.filter(relationship_type=sibling_type)
        assert not sibling_rels.filter(person_b_id=child2_id).exists()


# =============================================================================
# Anecdote Workflow Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteWorkflow:
    """Test creating anecdotes and linking to persons/photos."""

    def test_anecdote_with_multiple_persons(self):
        """Test creating an anecdote involving multiple persons."""
        # Create persons
        alice = PersonFactory(first_name="Alice")
        bob = PersonFactory(first_name="Bob")
        charlie = PersonFactory(first_name="Charlie")

        # Create anecdote about group event
        anecdote = AnecdoteFactory(
            title="Team Offsite 2024",
            content="We all went hiking together.",
            anecdote_type=Anecdote.AnecdoteType.MEMORY,
        )

        # Link to all participants
        anecdote.persons.add(alice, bob, charlie)

        # Verify linkage
        assert anecdote.persons.count() == 3
        assert alice.anecdotes.count() == 1
        assert bob.anecdotes.count() == 1
        assert charlie.anecdotes.count() == 1

        # Remove one person
        anecdote.persons.remove(charlie)
        assert anecdote.persons.count() == 2
        assert charlie.anecdotes.count() == 0

        # Delete anecdote
        anecdote_id = anecdote.pk
        anecdote.delete()

        # Verify persons still exist but anecdote is gone
        assert Person.objects.filter(pk=alice.pk).exists()
        assert not Anecdote.objects.filter(pk=anecdote_id).exists()

    def test_anecdote_with_photos(self):
        """Test creating anecdote with associated photos."""
        person = PersonFactory(first_name="Photographer")

        # Create anecdote
        anecdote = AnecdoteFactory(
            title="Beach Trip",
            anecdote_type=Anecdote.AnecdoteType.MEMORY,
        )
        anecdote.persons.add(person)

        # Add photos to anecdote
        photo1 = PhotoFactory(caption="Sunset", anecdote=anecdote)
        photo2 = PhotoFactory(caption="Beach", anecdote=anecdote)
        photo1.persons.add(person)
        photo2.persons.add(person)

        # Verify photos are linked
        assert anecdote.photos.count() == 2
        assert person.photos.count() == 2

        # Delete anecdote - photos should have anecdote set to null
        anecdote.delete()

        photo1.refresh_from_db()
        photo2.refresh_from_db()
        assert photo1.anecdote is None
        assert photo2.anecdote is None

        # Photos still exist
        assert Photo.objects.filter(pk=photo1.pk).exists()
        assert Photo.objects.filter(pk=photo2.pk).exists()


# =============================================================================
# Custom Fields Workflow Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldsWorkflow:
    """Test custom field definitions and values lifecycle."""

    def test_custom_field_workflow(self):
        """Test creating custom fields and assigning values."""
        # Step 1: Create custom field definition
        field_def = CustomFieldDefinitionFactory(
            name="Favorite Color",
            field_type=CustomFieldDefinition.FieldType.TEXT,
        )

        # Step 2: Create persons
        alice = PersonFactory(first_name="Alice")
        bob = PersonFactory(first_name="Bob")

        # Step 3: Set custom field values
        value1 = CustomFieldValue.objects.create(
            definition=field_def,
            person=alice,
            value="Blue",
        )
        value2 = CustomFieldValue.objects.create(
            definition=field_def,
            person=bob,
            value="Green",
        )

        # Step 4: Verify values
        assert alice.custom_field_values.count() == 1
        assert alice.custom_field_values.first().value == "Blue"
        assert bob.custom_field_values.first().value == "Green"

        # Step 5: Update value
        value1.value = "Red"
        value1.save()
        alice.refresh_from_db()
        assert alice.custom_field_values.first().value == "Red"

        # Step 6: Delete person - values should cascade
        alice.delete()
        assert not CustomFieldValue.objects.filter(pk=value1.pk).exists()

        # Field definition still exists
        assert CustomFieldDefinition.objects.filter(pk=field_def.pk).exists()

        # Bob's value still exists
        assert CustomFieldValue.objects.filter(pk=value2.pk).exists()

    def test_custom_field_definition_deletion(self):
        """Test that deleting field definition cascades to values."""
        field_def = CustomFieldDefinitionFactory(
            name="Skill Level",
            field_type=CustomFieldDefinition.FieldType.NUMBER,
        )

        person = PersonFactory()
        value = CustomFieldValue.objects.create(
            definition=field_def,
            person=person,
            value="95",
        )

        # Delete definition
        field_def.delete()

        # Value should be gone
        assert not CustomFieldValue.objects.filter(pk=value.pk).exists()

        # Person still exists
        assert Person.objects.filter(pk=person.pk).exists()


# =============================================================================
# Tag and Group Workflow Tests
# =============================================================================


@pytest.mark.django_db
class TestTagGroupWorkflow:
    """Test tag and group management workflows."""

    def test_tag_management_workflow(self):
        """Test adding, removing, and managing tags on persons."""
        # Create tags
        vip_tag = TagFactory(name="VIP")
        developer_tag = TagFactory(name="Developer")
        manager_tag = TagFactory(name="Manager")

        # Create persons
        alice = PersonFactory(first_name="Alice")
        bob = PersonFactory(first_name="Bob")

        # Add tags
        alice.tags.add(vip_tag, developer_tag)
        bob.tags.add(developer_tag, manager_tag)

        # Verify
        assert alice.tags.count() == 2
        assert bob.tags.count() == 2

        # Query by tag
        developers = Person.objects.filter(tags=developer_tag)
        assert developers.count() == 2

        vips = Person.objects.filter(tags=vip_tag)
        assert vips.count() == 1
        assert vips.first() == alice

        # Remove tag from person
        alice.tags.remove(vip_tag)
        assert alice.tags.count() == 1

        # Delete tag - persons should still exist
        developer_tag.delete()
        alice.refresh_from_db()
        bob.refresh_from_db()
        assert alice.tags.count() == 0
        assert bob.tags.count() == 1  # still has manager_tag

    def test_group_management_workflow(self):
        """Test group membership workflow."""
        # Create groups
        work_group = GroupFactory(name="Work")
        family_group = GroupFactory(name="Family")

        # Create persons
        alice = PersonFactory(first_name="Alice")
        bob = PersonFactory(first_name="Bob")
        carol = PersonFactory(first_name="Carol")

        # Add to groups
        alice.groups.add(work_group, family_group)  # Alice is in both
        bob.groups.add(work_group)  # Bob is only work
        carol.groups.add(family_group)  # Carol is only family

        # Query by group
        work_members = Person.objects.filter(groups=work_group)
        assert work_members.count() == 2

        family_members = Person.objects.filter(groups=family_group)
        assert family_members.count() == 2

        # Query persons in BOTH groups
        both_groups = Person.objects.filter(groups=work_group).filter(
            groups=family_group
        )
        assert both_groups.count() == 1
        assert both_groups.first() == alice

        # Remove from group
        alice.groups.remove(work_group)
        work_members = Person.objects.filter(groups=work_group)
        assert work_members.count() == 1

        # Delete group - persons should still exist
        work_group.delete()
        bob.refresh_from_db()
        assert bob.groups.count() == 0
        assert Person.objects.filter(pk=bob.pk).exists()


# =============================================================================
# Photo Workflow Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoWorkflow:
    """Test photo management and person tagging workflow."""

    def test_photo_person_tagging_workflow(self):
        """Test tagging and untagging persons in photos."""
        # Create persons
        alice = PersonFactory(first_name="Alice")
        bob = PersonFactory(first_name="Bob")
        charlie = PersonFactory(first_name="Charlie")

        # Create photo
        photo = PhotoFactory(caption="Group Photo")

        # Tag persons in photo
        photo.persons.add(alice, bob)
        assert photo.persons.count() == 2
        assert alice.photos.count() == 1
        assert bob.photos.count() == 1
        assert charlie.photos.count() == 0

        # Add another person
        photo.persons.add(charlie)
        assert photo.persons.count() == 3

        # Remove person from photo
        photo.persons.remove(bob)
        assert photo.persons.count() == 2
        assert bob.photos.count() == 0

        # Delete photo - persons should still exist
        photo.delete()
        assert Person.objects.filter(pk=alice.pk).exists()
        assert Person.objects.filter(pk=bob.pk).exists()
        assert Person.objects.filter(pk=charlie.pk).exists()

    def test_person_deletion_removes_from_photos(self):
        """Test that deleting a person removes them from photo tags."""
        alice = PersonFactory(first_name="Alice")
        bob = PersonFactory(first_name="Bob")

        photo = PhotoFactory(caption="Duo Photo")
        photo.persons.add(alice, bob)
        assert photo.persons.count() == 2

        # Delete alice
        alice.delete()
        photo.refresh_from_db()

        # Photo still exists with only bob
        assert Photo.objects.filter(pk=photo.pk).exists()
        assert photo.persons.count() == 1
        assert photo.persons.first() == bob


# =============================================================================
# Complete Data Cleanup Tests
# =============================================================================


@pytest.mark.django_db
class TestDataCleanupWorkflow:
    """Test cascading deletes and data cleanup."""

    def test_person_deletion_cascades(self):
        """Test that deleting a person cleans up all related data."""
        # Create person with full data
        person = PersonFactory(first_name="FullData")

        # Add employment
        emp = EmploymentFactory(person=person)

        # Add custom field value
        field_def = CustomFieldDefinitionFactory()
        field_value = CustomFieldValue.objects.create(
            definition=field_def,
            person=person,
            value="test",
        )

        # Add to group and tag
        group = GroupFactory()
        tag = TagFactory()
        person.groups.add(group)
        person.tags.add(tag)

        # Create relationships
        other_person = PersonFactory()
        rel_type = RelationshipTypeFactory()
        relationship = RelationshipFactory(
            person_a=person,
            person_b=other_person,
            relationship_type=rel_type,
        )

        # Create anecdote
        anecdote = AnecdoteFactory()
        anecdote.persons.add(person)

        # Create photo
        photo = PhotoFactory()
        photo.persons.add(person)

        # Track IDs
        person_id = person.pk
        emp_id = emp.pk
        field_value_id = field_value.pk
        relationship_id = relationship.pk

        # Delete person
        person.delete()

        # Verify cascades
        assert not Person.objects.filter(pk=person_id).exists()
        assert not Employment.objects.filter(pk=emp_id).exists()
        assert not CustomFieldValue.objects.filter(pk=field_value_id).exists()
        assert not Relationship.objects.filter(pk=relationship_id).exists()

        # But these should still exist (just unlinked)
        assert CustomFieldDefinition.objects.filter(pk=field_def.pk).exists()
        assert Anecdote.objects.filter(pk=anecdote.pk).exists()
        assert Photo.objects.filter(pk=photo.pk).exists()

        # Other person still exists
        assert Person.objects.filter(pk=other_person.pk).exists()

    def test_soft_delete_preserves_relationships_for_audit(self):
        """Test that soft delete keeps relationships for audit purposes."""
        person = PersonFactory(first_name="SoftDelete")
        other_person = PersonFactory()

        rel_type = RelationshipTypeFactory()
        relationship = RelationshipFactory(
            person_a=person,
            person_b=other_person,
            relationship_type=rel_type,
        )

        # Soft delete
        person.is_active = False
        person.save()

        # Relationship still exists (for audit trail)
        assert Relationship.objects.filter(pk=relationship.pk).exists()

        # But person shouldn't appear in active queries
        active_persons = Person.objects.filter(is_active=True)
        assert person not in active_persons
