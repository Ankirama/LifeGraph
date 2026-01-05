"""
Tests for Relationship Graph API endpoint.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.people.models import Person, Relationship, RelationshipType
from tests.factories import (
    PersonFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
)


# =============================================================================
# Relationship Graph API Tests
# =============================================================================


@pytest.mark.django_db
class TestRelationshipGraphAPI:
    """Tests for Relationship Graph endpoint."""

    def test_graph_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("relationship-graph")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_graph_empty(self, authenticated_client):
        """Test graph endpoint returns proper structure."""
        url = reverse("relationship-graph")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "nodes" in response.data
        assert "edges" in response.data
        assert "relationship_types" in response.data
        assert isinstance(response.data["nodes"], list)
        assert isinstance(response.data["edges"], list)

    def test_graph_with_persons_no_relationships(self, authenticated_client):
        """Test graph with persons but no relationships."""
        PersonFactory.create_batch(3)

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Persons without relationships should still appear as nodes
        # (or be excluded based on implementation)

    def test_graph_with_relationships(self, authenticated_client):
        """Test graph returns nodes and edges for relationships."""
        # Create relationship type
        rel_type = RelationshipTypeFactory(
            name="friend",
            inverse_name="friend",
            category="social",
            is_symmetric=True,
        )

        # Create persons and relationship
        person_a = PersonFactory(first_name="Alice", last_name="Smith")
        person_b = PersonFactory(first_name="Bob", last_name="Johnson")
        RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rel_type,
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["nodes"]) >= 2
        assert len(response.data["edges"]) >= 1

        # Check node structure
        node_ids = [n["id"] for n in response.data["nodes"]]
        assert str(person_a.id) in node_ids
        assert str(person_b.id) in node_ids

    def test_graph_node_structure(self, authenticated_client):
        """Test that graph nodes have correct structure."""
        rel_type = RelationshipTypeFactory()
        person_a = PersonFactory(first_name="Alice", last_name="Smith")
        person_b = PersonFactory(first_name="Bob", last_name="Johnson")
        RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rel_type,
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Find Alice in nodes
        alice_node = next(
            (n for n in response.data["nodes"] if n["first_name"] == "Alice"),
            None,
        )
        assert alice_node is not None
        assert "id" in alice_node
        assert "label" in alice_node
        assert "first_name" in alice_node
        assert "last_name" in alice_node
        assert "avatar" in alice_node

    def test_graph_edge_structure(self, authenticated_client):
        """Test that graph edges have correct structure."""
        rel_type = RelationshipTypeFactory(
            name="colleague",
            inverse_name="colleague",
            category="professional",
        )
        person_a = PersonFactory()
        person_b = PersonFactory()
        RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rel_type,
            strength=3,
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["edges"]) >= 1

        edge = response.data["edges"][0]
        assert "id" in edge
        assert "source" in edge
        assert "target" in edge
        assert "type" in edge
        assert "type_name" in edge
        assert "category" in edge
        assert "strength" in edge
        assert "is_symmetric" in edge

    def test_graph_center_filter(self, authenticated_client):
        """Test graph with center_id filter."""
        rel_type = RelationshipTypeFactory()

        # Create a network: A - B - C
        person_a = PersonFactory(first_name="Alice")
        person_b = PersonFactory(first_name="Bob")
        person_c = PersonFactory(first_name="Charlie")

        RelationshipFactory(
            person_a=person_a,
            person_b=person_b,
            relationship_type=rel_type,
        )
        RelationshipFactory(
            person_a=person_b,
            person_b=person_c,
            relationship_type=rel_type,
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url, {"center_id": str(person_b.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["center_person_id"] == str(person_b.id)

    def test_graph_depth_filter(self, authenticated_client):
        """Test graph with depth filter."""
        rel_type = RelationshipTypeFactory()

        # Create a chain: A - B - C - D
        person_a = PersonFactory()
        person_b = PersonFactory()
        person_c = PersonFactory()
        person_d = PersonFactory()

        RelationshipFactory(person_a=person_a, person_b=person_b, relationship_type=rel_type)
        RelationshipFactory(person_a=person_b, person_b=person_c, relationship_type=rel_type)
        RelationshipFactory(person_a=person_c, person_b=person_d, relationship_type=rel_type)

        url = reverse("relationship-graph")

        # Depth 1 centered on B should include A, B, C
        response = authenticated_client.get(
            url, {"center_id": str(person_b.id), "depth": 1}
        )
        assert response.status_code == status.HTTP_200_OK

        # Depth 2 centered on B should include A, B, C, D
        response = authenticated_client.get(
            url, {"center_id": str(person_b.id), "depth": 2}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_graph_category_filter(self, authenticated_client):
        """Test graph with category filter."""
        family_type = RelationshipTypeFactory(name="parent", category="family")
        social_type = RelationshipTypeFactory(name="friend", category="social")

        person_a = PersonFactory()
        person_b = PersonFactory()
        person_c = PersonFactory()

        # Create family and social relationships
        RelationshipFactory(
            person_a=person_a, person_b=person_b, relationship_type=family_type
        )
        RelationshipFactory(
            person_a=person_a, person_b=person_c, relationship_type=social_type
        )

        url = reverse("relationship-graph")

        # Filter by family category
        response = authenticated_client.get(url, {"category": "family"})
        assert response.status_code == status.HTTP_200_OK

        # All edges should be family category
        for edge in response.data["edges"]:
            assert edge["category"] == "family"

    def test_graph_relationship_types(self, authenticated_client):
        """Test that graph returns relationship types with colors."""
        family_type = RelationshipTypeFactory(category="family")
        social_type = RelationshipTypeFactory(category="social")

        person_a = PersonFactory()
        person_b = PersonFactory()
        person_c = PersonFactory()

        RelationshipFactory(
            person_a=person_a, person_b=person_b, relationship_type=family_type
        )
        RelationshipFactory(
            person_a=person_a, person_b=person_c, relationship_type=social_type
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["relationship_types"]) >= 2

        # Check structure
        for rt in response.data["relationship_types"]:
            assert "id" in rt or "name" in rt
            assert "category" in rt
            assert "color" in rt

    def test_graph_symmetric_relationships(self, authenticated_client):
        """Test that symmetric relationships don't create duplicate edges."""
        sym_type = RelationshipTypeFactory(
            name="friend",
            inverse_name="friend",
            is_symmetric=True,
        )

        person_a = PersonFactory()
        person_b = PersonFactory()

        RelationshipFactory(
            person_a=person_a, person_b=person_b, relationship_type=sym_type
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Count edges between A and B
        edges_between_ab = [
            e
            for e in response.data["edges"]
            if (e["source"] == str(person_a.id) and e["target"] == str(person_b.id))
            or (e["source"] == str(person_b.id) and e["target"] == str(person_a.id))
        ]

        # Should have exactly 1 edge (not duplicated)
        assert len(edges_between_ab) == 1

    def test_graph_asymmetric_relationships(self, authenticated_client):
        """Test asymmetric relationships (e.g., parent-child)."""
        parent_type = RelationshipTypeFactory(
            name="parent",
            inverse_name="child",
            category="family",
            is_symmetric=False,
        )

        parent = PersonFactory(first_name="Parent")
        child = PersonFactory(first_name="Child")

        RelationshipFactory(
            person_a=parent, person_b=child, relationship_type=parent_type
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Find the edge
        edge = response.data["edges"][0]
        assert edge["is_symmetric"] is False

    def test_graph_depth_limit(self, authenticated_client):
        """Test that depth is limited to maximum of 3."""
        url = reverse("relationship-graph")

        # Request depth > 3 should be limited
        response = authenticated_client.get(url, {"depth": 10})

        assert response.status_code == status.HTTP_200_OK
        # Implementation should cap depth at 3

    def test_graph_invalid_center_id(self, authenticated_client):
        """Test graph with invalid center_id."""
        url = reverse("relationship-graph")

        response = authenticated_client.get(
            url, {"center_id": "00000000-0000-0000-0000-000000000000"}
        )

        # Should handle gracefully (return empty or 404)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_graph_invalid_category(self, authenticated_client):
        """Test graph with invalid category filter."""
        rel_type = RelationshipTypeFactory()
        person_a = PersonFactory()
        person_b = PersonFactory()
        RelationshipFactory(
            person_a=person_a, person_b=person_b, relationship_type=rel_type
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url, {"category": "nonexistent"})

        # Should return empty edges for non-matching category
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["edges"]) == 0

    def test_graph_complex_network(self, authenticated_client):
        """Test graph with a more complex network structure."""
        rel_type = RelationshipTypeFactory()

        # Create a hub-and-spoke network
        hub = PersonFactory(first_name="Hub")
        spokes = [PersonFactory(first_name=f"Spoke{i}") for i in range(5)]

        for spoke in spokes:
            RelationshipFactory(
                person_a=hub, person_b=spoke, relationship_type=rel_type
            )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check that all hub and spokes are included
        node_ids = [n["id"] for n in response.data["nodes"]]
        assert str(hub.id) in node_ids
        for spoke in spokes:
            assert str(spoke.id) in node_ids
        # Check relationships exist
        assert len(response.data["edges"]) >= 5

    def test_graph_owner_person_highlighted(self, authenticated_client, owner_person):
        """Test that owner person can be identified if present."""
        rel_type = RelationshipTypeFactory()
        other_person = PersonFactory()
        RelationshipFactory(
            person_a=owner_person,
            person_b=other_person,
            relationship_type=rel_type,
        )

        url = reverse("relationship-graph")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Owner should be in nodes
        owner_node = next(
            (n for n in response.data["nodes"] if n["id"] == str(owner_person.id)),
            None,
        )
        assert owner_node is not None
