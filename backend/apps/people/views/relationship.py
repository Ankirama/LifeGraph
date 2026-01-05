"""
Relationship-related views.
"""

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Person, Relationship, RelationshipType
from ..serializers import RelationshipSerializer, RelationshipTypeSerializer


class RelationshipTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for RelationshipType CRUD operations."""

    queryset = RelationshipType.objects.all()
    serializer_class = RelationshipTypeSerializer
    search_fields = ["name", "inverse_name"]
    filterset_fields = ["category", "is_symmetric"]
    ordering = ["category", "name"]


class RelationshipViewSet(viewsets.ModelViewSet):
    """ViewSet for Relationship CRUD operations."""

    queryset = Relationship.objects.select_related(
        "person_a",
        "person_b",
        "relationship_type",
    ).all()
    serializer_class = RelationshipSerializer
    filterset_fields = ["person_a", "person_b", "relationship_type"]
    ordering = ["-created_at"]


class RelationshipGraphView(APIView):
    """
    Get relationship graph data optimized for visualization.

    Returns nodes (persons) and edges (relationships) in a format
    suitable for force-directed graph libraries like React Flow, Cytoscape, etc.

    Query params:
    - center_id: Optional UUID to center the graph on a specific person
    - depth: How many degrees of separation to include (1-3, default 2)
    - category: Filter by relationship category (family, professional, social, custom)
    """

    def get(self, request):
        center_id = request.query_params.get("center_id")
        depth = min(int(request.query_params.get("depth", 2)), 3)
        category = request.query_params.get("category")

        # Get all active persons
        persons_qs = Person.objects.filter(is_active=True)

        # Get all relationships with optional category filter
        relationships_qs = Relationship.objects.select_related(
            "person_a", "person_b", "relationship_type"
        ).filter(
            person_a__is_active=True,
            person_b__is_active=True,
        )

        if category:
            relationships_qs = relationships_qs.filter(
                relationship_type__category=category
            )

        # If centering on a person, limit graph scope
        if center_id:
            # Get persons within N degrees of separation
            connected_ids = set([center_id])
            current_layer = set([center_id])

            for _ in range(depth):
                next_layer = set()
                layer_rels = Relationship.objects.filter(
                    Q(person_a_id__in=current_layer) | Q(person_b_id__in=current_layer)
                ).values_list("person_a_id", "person_b_id")

                for a_id, b_id in layer_rels:
                    next_layer.add(str(a_id))
                    next_layer.add(str(b_id))

                next_layer -= connected_ids
                connected_ids |= next_layer
                current_layer = next_layer

                if not current_layer:
                    break

            # Filter to only connected persons
            persons_qs = persons_qs.filter(id__in=connected_ids)
            relationships_qs = relationships_qs.filter(
                person_a_id__in=connected_ids,
                person_b_id__in=connected_ids,
            )

        # Build nodes
        nodes = []
        for person in persons_qs:
            nodes.append({
                "id": str(person.id),
                "label": person.full_name,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "avatar": person.avatar if person.avatar else None,
                "is_owner": person.is_owner,
            })

        # Build edges (only include one direction for symmetric relationships)
        edges = []
        seen_pairs = set()

        for rel in relationships_qs:
            pair_key = tuple(sorted([str(rel.person_a_id), str(rel.person_b_id)]))
            rel_type = rel.relationship_type

            # For symmetric relationships, only include once
            if rel_type.is_symmetric:
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

            edges.append({
                "id": str(rel.id),
                "source": str(rel.person_a_id),
                "target": str(rel.person_b_id),
                "type": rel_type.name,
                "type_name": rel_type.name,
                "inverse_name": rel_type.inverse_name,
                "category": rel_type.category,
                "strength": rel.strength or 3,
                "is_symmetric": rel_type.is_symmetric,
            })

        # Get relationship types for legend
        rel_types = RelationshipType.objects.all()
        type_colors = {
            "family": "#ef4444",      # red
            "professional": "#3b82f6", # blue
            "social": "#22c55e",       # green
            "custom": "#a855f7",       # purple
        }

        relationship_types = []
        for rt in rel_types:
            relationship_types.append({
                "name": rt.name,
                "category": rt.category,
                "color": type_colors.get(rt.category, "#6b7280"),
                "is_symmetric": rt.is_symmetric,
            })

        return Response({
            "nodes": nodes,
            "edges": edges,
            "relationship_types": relationship_types,
            "center_person_id": center_id,
        })
