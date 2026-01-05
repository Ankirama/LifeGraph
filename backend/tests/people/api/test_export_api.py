"""Tests for the export API endpoints."""

import json

import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories import (
    AnecdoteFactory,
    EmploymentFactory,
    GroupFactory,
    PersonFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
    TagFactory,
)


@pytest.fixture
def sample_data():
    """Create sample data for export tests."""
    # Create tags and groups
    tag1 = TagFactory(name="friend")
    tag2 = TagFactory(name="colleague")
    group1 = GroupFactory(name="Family")
    group2 = GroupFactory(name="Work")

    # Create persons
    owner = PersonFactory(first_name="Test", last_name="Owner", is_owner=True)
    person1 = PersonFactory(first_name="John", last_name="Doe", is_owner=False)
    person2 = PersonFactory(first_name="Jane", last_name="Smith", is_owner=False)

    # Add tags and groups
    person1.tags.add(tag1)
    person2.tags.add(tag2)
    person1.groups.add(group1)
    person2.groups.add(group2)

    # Create employments
    EmploymentFactory(person=person1, company="Acme Inc", title="Engineer", is_current=True)
    EmploymentFactory(person=person2, company="Tech Corp", title="Manager", is_current=True)

    # Create relationship type and relationship
    rel_type = RelationshipTypeFactory(name="friend", inverse_name="friend")
    RelationshipFactory(person_a=person1, person_b=person2, relationship_type=rel_type)

    # Create anecdotes
    anecdote = AnecdoteFactory(title="Test Anecdote", content="Test content")
    anecdote.persons.add(person1, person2)

    return {
        "owner": owner,
        "persons": [person1, person2],
        "tags": [tag1, tag2],
        "groups": [group1, group2],
        "anecdote": anecdote,
        "rel_type": rel_type,
    }


@pytest.mark.django_db
class TestExportPreviewAPI:
    """Tests for export preview endpoint."""

    def test_preview_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("export-preview")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_preview_full_export(self, authenticated_client, sample_data):
        """Test preview for full export shows all counts."""
        url = reverse("export-preview")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["export_type"] == "full"
        assert "counts" in response.data
        assert response.data["counts"]["persons"] >= 2
        assert response.data["counts"]["tags"] >= 2
        assert response.data["counts"]["groups"] >= 2
        assert response.data["counts"]["anecdotes"] >= 1
        assert "total_items" in response.data
        assert "available_formats" in response.data

    def test_preview_entity_type(self, authenticated_client, sample_data):
        """Test preview for specific entity type."""
        url = reverse("export-preview")
        response = authenticated_client.get(url, {"entity": "persons"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["entity_type"] == "persons"
        assert response.data["count"] >= 2
        assert "json" in response.data["available_formats"]
        assert "csv" in response.data["available_formats"]

    def test_preview_invalid_entity(self, authenticated_client):
        """Test preview with invalid entity type returns error."""
        url = reverse("export-preview")
        response = authenticated_client.get(url, {"entity": "invalid"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestExportDataAPI:
    """Tests for export data download endpoint."""

    def test_export_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("export-data")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_full_json(self, authenticated_client, sample_data):
        """Test full JSON export contains all data."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "json"})

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        assert "attachment" in response["Content-Disposition"]
        assert ".json" in response["Content-Disposition"]

        # Parse and validate content
        content = json.loads(response.content)
        assert "export_version" in content
        assert "exported_at" in content
        assert "data" in content
        assert "counts" in content

        # Verify data sections
        assert "persons" in content["data"]
        assert "relationships" in content["data"]
        assert "anecdotes" in content["data"]
        assert "tags" in content["data"]
        assert "groups" in content["data"]

    def test_export_entity_json(self, authenticated_client, sample_data):
        """Test exporting specific entity as JSON."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "json", "entity": "persons"})

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"

        content = json.loads(response.content)
        assert content["entity_type"] == "persons"
        assert "data" in content
        assert len(content["data"]) >= 2

        # Verify person data structure
        person = content["data"][0]
        assert "id" in person
        assert "first_name" in person
        assert "last_name" in person

    def test_export_persons_csv(self, authenticated_client, sample_data):
        """Test exporting persons as CSV."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "csv", "entity": "persons"})

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        assert ".csv" in response["Content-Disposition"]

        # Parse CSV content
        content = response.content.decode("utf-8")
        lines = content.strip().split("\n")

        # Verify header
        header = lines[0]
        assert "id" in header
        assert "first_name" in header
        assert "last_name" in header
        assert "tags" in header

        # Verify data rows
        assert len(lines) >= 3  # Header + at least 2 data rows

    def test_export_relationships_csv(self, authenticated_client, sample_data):
        """Test exporting relationships as CSV."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "csv", "entity": "relationships"})

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

        content = response.content.decode("utf-8")
        lines = content.strip().split("\n")

        # Verify header
        header = lines[0]
        assert "person_a" in header
        assert "person_b" in header
        assert "relationship_type" in header

    def test_export_anecdotes_csv(self, authenticated_client, sample_data):
        """Test exporting anecdotes as CSV."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "csv", "entity": "anecdotes"})

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

        content = response.content.decode("utf-8")
        lines = content.strip().split("\n")

        # Verify header
        header = lines[0]
        assert "title" in header
        assert "content" in header
        assert "persons" in header

    def test_export_csv_requires_entity(self, authenticated_client):
        """Test that CSV export requires entity parameter."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "csv"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "entity" in response.data["detail"].lower()

    def test_export_csv_unsupported_entity(self, authenticated_client):
        """Test that CSV export fails for unsupported entity types."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "csv", "entity": "photos"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not supported" in response.data["detail"].lower()

    def test_export_invalid_format(self, authenticated_client):
        """Test that invalid format returns error."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "xml"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid format" in response.data["detail"].lower()

    def test_export_invalid_entity(self, authenticated_client):
        """Test that invalid entity type returns error."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "json", "entity": "invalid"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestExportDataIntegrity:
    """Tests for export data integrity and completeness."""

    def test_person_export_includes_employments(self, authenticated_client, sample_data):
        """Test that person export includes employment data."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "json", "entity": "persons"})

        content = json.loads(response.content)
        persons_with_employment = [p for p in content["data"] if p.get("employments")]

        assert len(persons_with_employment) >= 2
        emp = persons_with_employment[0]["employments"][0]
        assert "company" in emp
        assert "title" in emp
        assert "is_current" in emp

    def test_person_export_includes_tags_and_groups(self, authenticated_client, sample_data):
        """Test that person export includes tags and groups."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "json", "entity": "persons"})

        content = json.loads(response.content)

        # Find persons with tags
        persons_with_tags = [p for p in content["data"] if p.get("tags")]
        assert len(persons_with_tags) >= 1

        # Find persons with groups
        persons_with_groups = [p for p in content["data"] if p.get("groups")]
        assert len(persons_with_groups) >= 1

    def test_anecdote_export_includes_persons(self, authenticated_client, sample_data):
        """Test that anecdote export includes associated persons."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "json", "entity": "anecdotes"})

        content = json.loads(response.content)

        # Find anecdotes with persons
        anecdotes_with_persons = [a for a in content["data"] if a.get("persons")]
        assert len(anecdotes_with_persons) >= 1

        anecdote = anecdotes_with_persons[0]
        assert len(anecdote["persons"]) >= 2
        assert len(anecdote["person_ids"]) >= 2

    def test_relationship_export_includes_type_info(self, authenticated_client, sample_data):
        """Test that relationship export includes type information."""
        url = reverse("export-data")
        response = authenticated_client.get(url, {"export_format": "json", "entity": "relationships"})

        content = json.loads(response.content)

        if content["data"]:
            rel = content["data"][0]
            assert "relationship_type" in rel
            assert "relationship_type_inverse" in rel
            assert "person_a" in rel
            assert "person_b" in rel
            assert "person_a_id" in rel
            assert "person_b_id" in rel
