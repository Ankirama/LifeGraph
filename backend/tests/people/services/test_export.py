"""
Tests for the export service.

Tests all export functions for JSON and CSV formats.
"""

import csv
import io
import json
from datetime import date, datetime
from uuid import UUID

import pytest
from freezegun import freeze_time

from apps.core.models import Group, Tag
from apps.people.models import (
    Anecdote,
    Employment,
    Person,
    Photo,
    Relationship,
    RelationshipType,
)
from apps.people.services.export import (
    JSONEncoder,
    export_all_json,
    export_anecdotes,
    export_anecdotes_csv,
    export_entity_csv,
    export_entity_json,
    export_groups,
    export_persons,
    export_persons_csv,
    export_photos,
    export_relationship_types,
    export_relationships,
    export_relationships_csv,
    export_tags,
)
from tests.factories import (
    AnecdoteFactory,
    ChildGroupFactory,
    EmploymentFactory,
    GroupFactory,
    PastEmploymentFactory,
    PersonFactory,
    PhotoFactory,
    PhotoWithAIFactory,
    PhotoWithCoordsFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
    SymmetricRelationshipTypeFactory,
    TagFactory,
)


# =============================================================================
# JSONEncoder Tests
# =============================================================================


class TestJSONEncoder:
    """Tests for the custom JSON encoder."""

    def test_encode_uuid(self):
        """Test that UUIDs are encoded as strings."""
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        result = json.dumps({"id": test_uuid}, cls=JSONEncoder)
        parsed = json.loads(result)
        assert parsed["id"] == "12345678-1234-5678-1234-567812345678"

    def test_encode_datetime(self):
        """Test that datetimes are encoded as ISO format strings."""
        test_datetime = datetime(2024, 6, 15, 10, 30, 45)
        result = json.dumps({"timestamp": test_datetime}, cls=JSONEncoder)
        parsed = json.loads(result)
        assert parsed["timestamp"] == "2024-06-15T10:30:45"

    def test_encode_date(self):
        """Test that dates are encoded as ISO format strings."""
        test_date = date(2024, 6, 15)
        result = json.dumps({"date": test_date}, cls=JSONEncoder)
        parsed = json.loads(result)
        assert parsed["date"] == "2024-06-15"

    def test_encode_standard_types(self):
        """Test that standard types are encoded normally."""
        data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }
        result = json.dumps(data, cls=JSONEncoder)
        parsed = json.loads(result)
        assert parsed == data


# =============================================================================
# export_persons Tests
# =============================================================================


@pytest.mark.django_db
class TestExportPersons:
    """Tests for export_persons function."""

    def test_export_empty_database(self):
        """Test export when no persons exist."""
        result = export_persons()
        assert result == []

    def test_export_single_person(self):
        """Test export of a single person."""
        person = PersonFactory(
            first_name="John",
            last_name="Doe",
            birthday=date(1990, 5, 15),
        )

        result = export_persons()

        assert len(result) == 1
        assert result[0]["first_name"] == "John"
        assert result[0]["last_name"] == "Doe"
        assert result[0]["birthday"] == "1990-05-15"
        assert result[0]["id"] == str(person.id)

    def test_export_multiple_persons(self):
        """Test export of multiple persons."""
        PersonFactory.create_batch(5)

        result = export_persons()

        assert len(result) == 5

    def test_include_related_true(self):
        """Test that related data is included when include_related=True."""
        tag = TagFactory(name="Friend")
        group = GroupFactory(name="Work")
        person = PersonFactory()
        person.tags.add(tag)
        person.groups.add(group)
        EmploymentFactory(person=person, company="Acme Inc", title="Engineer")

        result = export_persons(include_related=True)

        assert len(result) == 1
        assert "Friend" in result[0]["tags"]
        assert "Work" in result[0]["groups"]
        assert len(result[0]["employments"]) == 1
        assert result[0]["employments"][0]["company"] == "Acme Inc"

    def test_include_related_false(self):
        """Test that related data is excluded when include_related=False."""
        tag = TagFactory(name="Friend")
        person = PersonFactory()
        person.tags.add(tag)
        EmploymentFactory(person=person)

        result = export_persons(include_related=False)

        assert len(result) == 1
        assert "tags" not in result[0]
        assert "groups" not in result[0]
        assert "employments" not in result[0]

    def test_person_with_tags_groups(self):
        """Test export includes multiple tags and groups."""
        tags = [TagFactory(name=f"Tag{i}") for i in range(3)]
        groups = [GroupFactory(name=f"Group{i}") for i in range(2)]
        person = PersonFactory()
        person.tags.set(tags)
        person.groups.set(groups)

        result = export_persons(include_related=True)

        assert len(result[0]["tags"]) == 3
        assert len(result[0]["groups"]) == 2

    def test_person_with_multiple_employments(self):
        """Test export includes all employment records."""
        person = PersonFactory()
        EmploymentFactory(person=person, company="Company A", is_current=True)
        PastEmploymentFactory(person=person, company="Company B")

        result = export_persons(include_related=True)

        assert len(result[0]["employments"]) == 2
        companies = [e["company"] for e in result[0]["employments"]]
        assert "Company A" in companies
        assert "Company B" in companies

    def test_handles_null_dates(self):
        """Test export handles null date fields."""
        person = PersonFactory(
            birthday=None,
            met_date=None,
            last_contact=None,
        )

        result = export_persons()

        assert result[0]["birthday"] is None
        assert result[0]["met_date"] is None
        assert result[0]["last_contact"] is None

    def test_export_encrypted_fields(self):
        """Test that encrypted fields are properly exported."""
        person = PersonFactory(
            emails=[{"email": "test@example.com", "label": "work"}],
            phones=[{"phone": "+1234567890", "label": "mobile"}],
            addresses=[{"address": "123 Main St", "label": "home"}],
            notes="Sensitive notes here",
            met_context="Met at conference",
        )

        result = export_persons()

        assert result[0]["emails"] == [{"email": "test@example.com", "label": "work"}]
        assert result[0]["phones"] == [{"phone": "+1234567890", "label": "mobile"}]
        assert result[0]["addresses"] == [{"address": "123 Main St", "label": "home"}]
        assert result[0]["notes"] == "Sensitive notes here"
        assert result[0]["met_context"] == "Met at conference"


# =============================================================================
# export_relationships Tests
# =============================================================================


@pytest.mark.django_db
class TestExportRelationships:
    """Tests for export_relationships function."""

    def test_export_empty(self):
        """Test export when no relationships exist."""
        result = export_relationships()
        assert result == []

    def test_export_single_relationship(self):
        """Test export of a single relationship."""
        person_a = PersonFactory(first_name="Alice", last_name="Smith")
        person_b = PersonFactory(first_name="Bob", last_name="Jones")
        # Use auto_create_inverse=False to avoid creating duplicate relationship
        rel_type = RelationshipTypeFactory(
            name="Friend",
            inverse_name="Friend",
            auto_create_inverse=False,
        )
        relationship = RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rel_type,
            started_date=date(2020, 1, 15),
            notes="Met at work",
            strength=4,
        )

        result = export_relationships()

        assert len(result) == 1
        assert result[0]["person_a"] == "Alice Smith"
        assert result[0]["person_b"] == "Bob Jones"
        assert result[0]["relationship_type"] == "Friend"
        assert result[0]["started_date"] == "2020-01-15"
        assert result[0]["notes"] == "Met at work"
        assert result[0]["strength"] == 4

    def test_export_symmetric_relationship(self):
        """Test export of symmetric relationship."""
        rel_type = SymmetricRelationshipTypeFactory(name="Spouse", auto_create_inverse=False)
        relationship = RelationshipFactory(relationship_type=rel_type)

        result = export_relationships()

        assert len(result) == 1
        assert result[0]["relationship_type"] == "Spouse"

    def test_export_includes_person_ids(self):
        """Test that person IDs are included in export."""
        person_a = PersonFactory()
        person_b = PersonFactory()
        rel_type = RelationshipTypeFactory(auto_create_inverse=False)
        RelationshipFactory(person_a=person_a, person_b=person_b, relationship_type=rel_type)

        result = export_relationships()

        # Find the relationship we created
        rel = next(r for r in result if r["person_a_id"] == str(person_a.id))
        assert rel["person_a_id"] == str(person_a.id)
        assert rel["person_b_id"] == str(person_b.id)

    def test_export_includes_type_info(self):
        """Test that relationship type info is included."""
        rel_type = RelationshipTypeFactory(
            name="Parent",
            inverse_name="Child",
            auto_create_inverse=False,
        )
        RelationshipFactory(relationship_type=rel_type)

        result = export_relationships()

        # Find relationship with our type
        rel = next(r for r in result if r["relationship_type"] == "Parent")
        assert rel["relationship_type"] == "Parent"
        assert rel["relationship_type_inverse"] == "Child"

    def test_handles_null_started_date(self):
        """Test export handles null started_date."""
        rel_type = RelationshipTypeFactory(auto_create_inverse=False)
        relationship = RelationshipFactory(started_date=None, relationship_type=rel_type)

        result = export_relationships()

        rel = next(r for r in result if r["id"] == str(relationship.id))
        assert rel["started_date"] is None

    def test_includes_auto_created_flag(self):
        """Test that auto_created flag is exported."""
        # Create a symmetric relationship type that auto-creates inverse
        # Symmetric types create inverse with the same type
        rel_type = SymmetricRelationshipTypeFactory(
            name="TestAutoColleague",
            auto_create_inverse=True,
        )
        person_a = PersonFactory()
        person_b = PersonFactory()
        RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rel_type,
            auto_created=False,
        )

        result = export_relationships()

        # The factory creates one with auto_created=False
        # and the model signal creates the inverse with auto_created=True
        auto_created_values = [r["auto_created"] for r in result]
        assert True in auto_created_values
        assert False in auto_created_values


# =============================================================================
# export_anecdotes Tests
# =============================================================================


@pytest.mark.django_db
class TestExportAnecdotes:
    """Tests for export_anecdotes function."""

    def test_export_empty(self):
        """Test export when no anecdotes exist."""
        result = export_anecdotes()
        assert result == []

    def test_export_single_anecdote(self):
        """Test export of a single anecdote."""
        anecdote = AnecdoteFactory(
            title="Funny Story",
            content="Once upon a time...",
            date=date(2023, 7, 20),
            location="New York",
            anecdote_type="memory",
        )

        result = export_anecdotes()

        assert len(result) == 1
        assert result[0]["title"] == "Funny Story"
        assert result[0]["content"] == "Once upon a time..."
        assert result[0]["date"] == "2023-07-20"
        assert result[0]["location"] == "New York"
        assert result[0]["anecdote_type"] == "memory"

    def test_export_with_persons(self):
        """Test export includes associated persons."""
        person1 = PersonFactory(first_name="Alice", last_name="Smith")
        person2 = PersonFactory(first_name="Bob", last_name="Jones")
        anecdote = AnecdoteFactory()
        anecdote.persons.add(person1, person2)

        result = export_anecdotes()

        assert "Alice Smith" in result[0]["persons"]
        assert "Bob Jones" in result[0]["persons"]
        assert str(person1.id) in result[0]["person_ids"]
        assert str(person2.id) in result[0]["person_ids"]

    def test_export_with_tags(self):
        """Test export includes tags."""
        tag1 = TagFactory(name="Funny")
        tag2 = TagFactory(name="Work")
        anecdote = AnecdoteFactory()
        anecdote.tags.add(tag1, tag2)

        result = export_anecdotes()

        assert "Funny" in result[0]["tags"]
        assert "Work" in result[0]["tags"]

    def test_different_anecdote_types(self):
        """Test export of different anecdote types."""
        AnecdoteFactory(anecdote_type="memory")
        AnecdoteFactory(anecdote_type="joke")
        AnecdoteFactory(anecdote_type="quote")
        AnecdoteFactory(anecdote_type="note")

        result = export_anecdotes()

        types = [a["anecdote_type"] for a in result]
        assert "memory" in types
        assert "joke" in types
        assert "quote" in types
        assert "note" in types

    def test_handles_null_location(self):
        """Test export handles null location."""
        AnecdoteFactory(location="")

        result = export_anecdotes()

        assert result[0]["location"] == ""

    def test_handles_null_date(self):
        """Test export handles null date."""
        AnecdoteFactory(date=None)

        result = export_anecdotes()

        assert result[0]["date"] is None


# =============================================================================
# export_photos Tests
# =============================================================================


@pytest.mark.django_db
class TestExportPhotos:
    """Tests for export_photos function."""

    def test_export_empty(self):
        """Test export when no photos exist."""
        result = export_photos()
        assert result == []

    def test_export_single_photo(self):
        """Test export of a single photo."""
        photo = PhotoFactory(
            caption="Birthday party",
            location="Home",
        )

        result = export_photos()

        assert len(result) == 1
        assert result[0]["caption"] == "Birthday party"
        assert result[0]["location"] == "Home"
        assert result[0]["file_path"] is not None

    def test_export_with_coords(self):
        """Test export of photo with location coordinates."""
        photo = PhotoWithCoordsFactory()

        result = export_photos()

        assert result[0]["location_coords"] == {"lat": 40.7128, "lng": -74.0060}

    def test_export_with_ai_description(self):
        """Test export of photo with AI description."""
        photo = PhotoWithAIFactory()

        result = export_photos()

        assert result[0]["ai_description"] != ""
        assert len(result[0]["detected_faces"]) > 0

    def test_export_with_persons(self):
        """Test export includes tagged persons."""
        person = PersonFactory(first_name="Jane", last_name="Doe")
        photo = PhotoFactory()
        photo.persons.add(person)

        result = export_photos()

        assert "Jane Doe" in result[0]["persons"]
        assert str(person.id) in result[0]["person_ids"]

    def test_export_with_anecdote(self):
        """Test export includes linked anecdote."""
        anecdote = AnecdoteFactory()
        photo = PhotoFactory(anecdote=anecdote)

        result = export_photos()

        assert result[0]["anecdote_id"] == str(anecdote.id)

    def test_handles_null_anecdote(self):
        """Test export handles null anecdote."""
        PhotoFactory(anecdote=None)

        result = export_photos()

        assert result[0]["anecdote_id"] is None


# =============================================================================
# export_tags Tests
# =============================================================================


@pytest.mark.django_db
class TestExportTags:
    """Tests for export_tags function."""

    def test_export_empty(self):
        """Test export when no tags exist."""
        result = export_tags()
        assert result == []

    def test_export_single_tag(self):
        """Test export of a single tag."""
        tag = TagFactory(
            name="Important",
            color="#ff0000",
            description="High priority items",
        )

        result = export_tags()

        assert len(result) == 1
        assert result[0]["name"] == "Important"
        assert result[0]["color"] == "#ff0000"
        assert result[0]["description"] == "High priority items"

    def test_export_multiple_tags(self):
        """Test export of multiple tags."""
        TagFactory.create_batch(5)

        result = export_tags()

        assert len(result) == 5


# =============================================================================
# export_groups Tests
# =============================================================================


@pytest.mark.django_db
class TestExportGroups:
    """Tests for export_groups function."""

    def test_export_empty(self):
        """Test export when no groups exist."""
        result = export_groups()
        assert result == []

    def test_export_flat_groups(self):
        """Test export of groups without hierarchy."""
        group = GroupFactory(
            name="Team A",
            description="Development team",
            color="#00ff00",
        )

        result = export_groups()

        assert len(result) == 1
        assert result[0]["name"] == "Team A"
        assert result[0]["description"] == "Development team"
        assert result[0]["parent"] is None
        assert result[0]["parent_id"] is None

    def test_export_hierarchical_groups(self):
        """Test export of groups with parent-child relationships."""
        parent = GroupFactory(name="Engineering")
        child = ChildGroupFactory(name="Frontend", parent=parent)

        result = export_groups()

        # Find the child group in results
        child_result = next(g for g in result if g["name"] == "Frontend")
        assert child_result["parent"] == "Engineering"
        assert child_result["parent_id"] == str(parent.id)

    def test_export_multiple_groups(self):
        """Test export of multiple groups."""
        GroupFactory.create_batch(3)

        result = export_groups()

        assert len(result) == 3


# =============================================================================
# export_relationship_types Tests
# =============================================================================


@pytest.mark.django_db
class TestExportRelationshipTypes:
    """Tests for export_relationship_types function.

    Note: The database may have seeded relationship types from the
    seed_relationship_types management command. Tests account for this.
    """

    def test_export_returns_list(self):
        """Test export returns a list (may have seeded data)."""
        result = export_relationship_types()
        assert isinstance(result, list)

    def test_export_single_type(self):
        """Test export includes a created relationship type."""
        # Get initial count
        initial_count = len(export_relationship_types())

        rel_type = RelationshipTypeFactory(
            name="TestMentor",
            inverse_name="TestMentee",
            category="professional",
            is_symmetric=False,
            auto_create_inverse=True,
        )

        result = export_relationship_types()

        # Should have one more than before
        assert len(result) == initial_count + 1

        # Find the type we created
        exported = next(r for r in result if r["name"] == "TestMentor")
        assert exported["inverse_name"] == "TestMentee"
        assert exported["category"] == "professional"
        assert exported["is_symmetric"] is False
        assert exported["auto_create_inverse"] is True

    def test_export_symmetric_type(self):
        """Test export of symmetric relationship type."""
        rel_type = SymmetricRelationshipTypeFactory(name="TestColleague")

        result = export_relationship_types()

        # Find our symmetric type
        exported = next(r for r in result if r["name"] == "TestColleague")
        assert exported["is_symmetric"] is True

    def test_export_multiple_types(self):
        """Test export includes all created types."""
        initial_count = len(export_relationship_types())

        # Create 4 new types
        for i in range(4):
            RelationshipTypeFactory(name=f"TestBatchType{i}")

        result = export_relationship_types()

        assert len(result) == initial_count + 4

    def test_export_type_structure(self):
        """Test that exported types have correct structure."""
        result = export_relationship_types()

        # If there are any types, check structure
        if result:
            first = result[0]
            assert "id" in first
            assert "name" in first
            assert "inverse_name" in first
            assert "category" in first
            assert "is_symmetric" in first
            assert "auto_create_inverse" in first
            assert "created_at" in first


# =============================================================================
# export_all_json Tests
# =============================================================================


@pytest.mark.django_db
class TestExportAllJson:
    """Tests for export_all_json function."""

    @freeze_time("2024-06-15 10:30:00")
    def test_full_export_structure(self):
        """Test that export has correct structure."""
        PersonFactory()
        TagFactory()

        result = export_all_json()
        data = json.loads(result)

        assert "export_version" in data
        assert "exported_at" in data
        assert "data" in data
        assert "counts" in data

        # Check all data sections exist
        assert "persons" in data["data"]
        assert "relationships" in data["data"]
        assert "relationship_types" in data["data"]
        assert "anecdotes" in data["data"]
        assert "photos" in data["data"]
        assert "tags" in data["data"]
        assert "groups" in data["data"]

    @freeze_time("2024-06-15 10:30:00")
    def test_export_version_metadata(self):
        """Test export version and timestamp."""
        result = export_all_json()
        data = json.loads(result)

        assert data["export_version"] == "1.0"
        assert data["exported_at"] == "2024-06-15T10:30:00"

    def test_counts_accuracy(self):
        """Test that counts match actual data."""
        # Get initial counts (database may have seeded data)
        initial = json.loads(export_all_json())
        initial_rel_types = initial["counts"]["relationship_types"]

        PersonFactory.create_batch(3)
        TagFactory.create_batch(2)
        RelationshipTypeFactory(name="TestCountType")

        result = export_all_json()
        data = json.loads(result)

        assert data["counts"]["persons"] == 3
        assert data["counts"]["tags"] == 2
        assert data["counts"]["relationship_types"] == initial_rel_types + 1
        assert len(data["data"]["persons"]) == 3
        assert len(data["data"]["tags"]) == 2

    def test_empty_database(self):
        """Test export with empty database."""
        result = export_all_json()
        data = json.loads(result)

        assert data["counts"]["persons"] == 0
        assert data["counts"]["relationships"] == 0
        assert data["data"]["persons"] == []
        assert data["data"]["relationships"] == []

    def test_json_is_valid(self):
        """Test that output is valid JSON."""
        PersonFactory()

        result = export_all_json()

        # Should not raise
        data = json.loads(result)
        assert isinstance(data, dict)


# =============================================================================
# export_entity_json Tests
# =============================================================================


@pytest.mark.django_db
class TestExportEntityJson:
    """Tests for export_entity_json function."""

    def test_valid_entity_types(self):
        """Test export of all valid entity types."""
        PersonFactory()
        RelationshipFactory()
        AnecdoteFactory()
        PhotoFactory()
        TagFactory()
        GroupFactory()

        valid_types = [
            "persons",
            "relationships",
            "relationship_types",
            "anecdotes",
            "photos",
            "tags",
            "groups",
        ]

        for entity_type in valid_types:
            result = export_entity_json(entity_type)
            data = json.loads(result)
            assert "data" in data
            assert "entity_type" in data
            assert data["entity_type"] == entity_type

    def test_invalid_entity_raises(self):
        """Test that invalid entity type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown entity type"):
            export_entity_json("invalid_type")

    @freeze_time("2024-06-15 10:30:00")
    def test_metadata_included(self):
        """Test that metadata is included in export."""
        PersonFactory()

        result = export_entity_json("persons")
        data = json.loads(result)

        assert data["export_version"] == "1.0"
        assert data["exported_at"] == "2024-06-15T10:30:00"
        assert data["entity_type"] == "persons"
        assert "count" in data

    def test_count_matches_data(self):
        """Test that count matches data length."""
        PersonFactory.create_batch(5)

        result = export_entity_json("persons")
        data = json.loads(result)

        assert data["count"] == 5
        assert len(data["data"]) == 5


# =============================================================================
# export_persons_csv Tests
# =============================================================================


@pytest.mark.django_db
class TestExportPersonsCsv:
    """Tests for export_persons_csv function."""

    def test_export_empty(self):
        """Test CSV export with no persons."""
        result = export_persons_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        # Should have header row only
        assert len(rows) == 1
        assert "first_name" in rows[0]

    def test_export_single_person(self):
        """Test CSV export of a single person."""
        person = PersonFactory(
            first_name="John",
            last_name="Doe",
            emails=[{"email": "john@example.com", "label": "work"}],
            phones=[{"phone": "+1234567890", "label": "mobile"}],
        )

        result = export_persons_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 2  # Header + 1 person

        # Find column indices
        headers = rows[0]
        first_name_idx = headers.index("first_name")
        last_name_idx = headers.index("last_name")
        primary_email_idx = headers.index("primary_email")
        primary_phone_idx = headers.index("primary_phone")

        assert rows[1][first_name_idx] == "John"
        assert rows[1][last_name_idx] == "Doe"
        assert rows[1][primary_email_idx] == "john@example.com"
        assert rows[1][primary_phone_idx] == "+1234567890"

    def test_export_with_current_employment(self):
        """Test CSV includes current employment."""
        person = PersonFactory()
        EmploymentFactory(
            person=person,
            company="Acme Corp",
            title="Developer",
            is_current=True,
        )

        result = export_persons_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        headers = rows[0]
        company_idx = headers.index("current_company")
        title_idx = headers.index("current_title")

        assert rows[1][company_idx] == "Acme Corp"
        assert rows[1][title_idx] == "Developer"

    def test_export_with_tags_groups(self):
        """Test CSV includes pipe-separated tags and groups."""
        tag1 = TagFactory(name="Friend")
        tag2 = TagFactory(name="Colleague")
        group = GroupFactory(name="Work")
        person = PersonFactory()
        person.tags.add(tag1, tag2)
        person.groups.add(group)

        result = export_persons_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        headers = rows[0]
        tags_idx = headers.index("tags")
        groups_idx = headers.index("groups")

        # Tags should be pipe-separated
        tags = rows[1][tags_idx].split("|")
        assert len(tags) == 2
        assert rows[1][groups_idx] == "Work"


# =============================================================================
# export_relationships_csv Tests
# =============================================================================


@pytest.mark.django_db
class TestExportRelationshipsCsv:
    """Tests for export_relationships_csv function."""

    def test_export_empty(self):
        """Test CSV export with no relationships."""
        result = export_relationships_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1  # Header only

    def test_export_single_relationship(self):
        """Test CSV export of a single relationship."""
        person_a = PersonFactory(first_name="Alice", last_name="Smith")
        person_b = PersonFactory(first_name="Bob", last_name="Jones")
        # Use auto_create_inverse=False to avoid creating duplicate relationship
        rel_type = RelationshipTypeFactory(
            name="CsvFriend",
            inverse_name="CsvFriend",
            auto_create_inverse=False,
        )
        RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rel_type,
            strength=5,
        )

        result = export_relationships_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 2

        headers = rows[0]
        person_a_idx = headers.index("person_a")
        person_b_idx = headers.index("person_b")
        type_idx = headers.index("relationship_type")
        strength_idx = headers.index("strength")

        assert rows[1][person_a_idx] == "Alice Smith"
        assert rows[1][person_b_idx] == "Bob Jones"
        assert rows[1][type_idx] == "CsvFriend"
        assert rows[1][strength_idx] == "5"

    def test_export_handles_empty_notes(self):
        """Test CSV handles empty notes field."""
        RelationshipFactory(notes="")

        result = export_relationships_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        headers = rows[0]
        notes_idx = headers.index("notes")
        assert rows[1][notes_idx] == ""


# =============================================================================
# export_anecdotes_csv Tests
# =============================================================================


@pytest.mark.django_db
class TestExportAnecdotesCsv:
    """Tests for export_anecdotes_csv function."""

    def test_export_empty(self):
        """Test CSV export with no anecdotes."""
        result = export_anecdotes_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1  # Header only

    def test_export_single_anecdote(self):
        """Test CSV export of a single anecdote."""
        person = PersonFactory(first_name="Jane", last_name="Doe")
        tag = TagFactory(name="Funny")
        anecdote = AnecdoteFactory(
            title="A Great Day",
            content="Something happened...",
            anecdote_type="memory",
        )
        anecdote.persons.add(person)
        anecdote.tags.add(tag)

        result = export_anecdotes_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 2

        headers = rows[0]
        title_idx = headers.index("title")
        persons_idx = headers.index("persons")
        tags_idx = headers.index("tags")
        type_idx = headers.index("anecdote_type")

        assert rows[1][title_idx] == "A Great Day"
        assert "Jane Doe" in rows[1][persons_idx]
        assert rows[1][tags_idx] == "Funny"
        assert rows[1][type_idx] == "memory"

    def test_export_multiple_persons_pipe_separated(self):
        """Test CSV exports multiple persons with pipe separator."""
        person1 = PersonFactory(first_name="Alice", last_name="A")
        person2 = PersonFactory(first_name="Bob", last_name="B")
        anecdote = AnecdoteFactory()
        anecdote.persons.add(person1, person2)

        result = export_anecdotes_csv()
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        headers = rows[0]
        persons_idx = headers.index("persons")
        persons = rows[1][persons_idx].split("|")
        assert len(persons) == 2


# =============================================================================
# export_entity_csv Tests
# =============================================================================


@pytest.mark.django_db
class TestExportEntityCsv:
    """Tests for export_entity_csv function."""

    def test_valid_entities(self):
        """Test CSV export for all valid entity types."""
        PersonFactory()
        RelationshipFactory()
        AnecdoteFactory()

        # These should not raise
        export_entity_csv("persons")
        export_entity_csv("relationships")
        export_entity_csv("anecdotes")

    def test_unsupported_entity_raises(self):
        """Test that unsupported entity type raises ValueError."""
        with pytest.raises(ValueError, match="CSV export not supported"):
            export_entity_csv("photos")

        with pytest.raises(ValueError, match="CSV export not supported"):
            export_entity_csv("tags")

        with pytest.raises(ValueError, match="CSV export not supported"):
            export_entity_csv("groups")

    def test_invalid_entity_raises(self):
        """Test that invalid entity type raises ValueError."""
        with pytest.raises(ValueError, match="CSV export not supported"):
            export_entity_csv("invalid_type")

    def test_returns_valid_csv(self):
        """Test that returned string is valid CSV."""
        PersonFactory()

        result = export_entity_csv("persons")
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) >= 1  # At least header
        assert len(rows[0]) > 0  # Header has columns
