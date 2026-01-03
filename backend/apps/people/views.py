"""
People app views.
"""

from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Anecdote,
    CustomFieldDefinition,
    Person,
    Relationship,
    RelationshipType,
)
from .serializers import (
    AnecdoteSerializer,
    CustomFieldDefinitionSerializer,
    PersonCreateUpdateSerializer,
    PersonDetailSerializer,
    PersonListSerializer,
    RelationshipSerializer,
    RelationshipTypeSerializer,
)


class PersonFilter(filters.FilterSet):
    """Filter for Person queryset."""

    name = filters.CharFilter(lookup_expr="icontains")
    tag = filters.UUIDFilter(field_name="tags__id")
    group = filters.UUIDFilter(field_name="groups__id")
    has_birthday = filters.BooleanFilter(
        field_name="birthday",
        lookup_expr="isnull",
        exclude=True,
    )
    is_active = filters.BooleanFilter()

    class Meta:
        model = Person
        fields = ["name", "tag", "group", "has_birthday", "is_active"]


class PersonViewSet(viewsets.ModelViewSet):
    """ViewSet for Person CRUD operations."""

    queryset = Person.objects.prefetch_related("tags", "groups").filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filterset_class = PersonFilter
    search_fields = ["name", "nickname", "notes", "met_context"]
    ordering_fields = ["name", "birthday", "last_contact", "created_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return PersonListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return PersonCreateUpdateSerializer
        return PersonDetailSerializer

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=["get"])
    def relationships(self, request, pk=None):
        """Get all relationships for a person."""
        person = self.get_object()
        relationships_as_a = Relationship.objects.filter(
            person_a=person
        ).select_related("person_b", "relationship_type")
        relationships_as_b = Relationship.objects.filter(
            person_b=person
        ).select_related("person_a", "relationship_type")

        # Combine and serialize
        all_relationships = list(relationships_as_a) + list(relationships_as_b)
        serializer = RelationshipSerializer(all_relationships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def anecdotes(self, request, pk=None):
        """Get all anecdotes for a person."""
        person = self.get_object()
        anecdotes = person.anecdotes.prefetch_related("tags", "persons").all()
        serializer = AnecdoteSerializer(anecdotes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def generate_summary(self, request, pk=None):
        """Generate AI summary for a person."""
        # TODO: Implement AI summary generation
        person = self.get_object()
        return Response(
            {"message": "AI summary generation not yet implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class RelationshipTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for RelationshipType CRUD operations."""

    queryset = RelationshipType.objects.all()
    serializer_class = RelationshipTypeSerializer
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    filterset_fields = ["person_a", "person_b", "relationship_type"]
    ordering = ["-created_at"]


class AnecdoteFilter(filters.FilterSet):
    """Filter for Anecdote queryset."""

    person = filters.UUIDFilter(field_name="persons__id")
    tag = filters.UUIDFilter(field_name="tags__id")
    anecdote_type = filters.ChoiceFilter(choices=Anecdote.AnecdoteType.choices)
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Anecdote
        fields = ["person", "tag", "anecdote_type", "date_from", "date_to"]


class AnecdoteViewSet(viewsets.ModelViewSet):
    """ViewSet for Anecdote CRUD operations."""

    queryset = Anecdote.objects.prefetch_related("persons", "tags").all()
    serializer_class = AnecdoteSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = AnecdoteFilter
    search_fields = ["title", "content", "location"]
    ordering_fields = ["date", "created_at", "anecdote_type"]
    ordering = ["-date", "-created_at"]


class CustomFieldDefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet for CustomFieldDefinition CRUD operations."""

    queryset = CustomFieldDefinition.objects.all()
    serializer_class = CustomFieldDefinitionSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["order", "name"]
