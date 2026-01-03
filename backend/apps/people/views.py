"""
People app views.
"""

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Anecdote,
    CustomFieldDefinition,
    Employment,
    Person,
    Photo,
    Relationship,
    RelationshipType,
)
from .serializers import (
    AnecdoteSerializer,
    CustomFieldDefinitionSerializer,
    EmploymentSerializer,
    PersonCreateUpdateSerializer,
    PersonDetailSerializer,
    PersonListSerializer,
    PhotoSerializer,
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

    @action(detail=True, methods=["get"])
    def photos(self, request, pk=None):
        """Get all photos for a person."""
        person = self.get_object()
        photos = person.photos.prefetch_related("persons").select_related("anecdote").all()
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def employments(self, request, pk=None):
        """Get employment history for a person."""
        person = self.get_object()
        employments = person.employments.all()
        serializer = EmploymentSerializer(employments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """Get audit history for a person."""
        person = self.get_object()
        content_type = ContentType.objects.get_for_model(Person)
        entries = LogEntry.objects.filter(
            content_type=content_type,
            object_pk=str(person.pk),
        ).order_by("-timestamp")[:50]

        history = []
        for entry in entries:
            history.append({
                "id": entry.pk,
                "action": entry.get_action_display(),
                "timestamp": entry.timestamp.isoformat(),
                "actor": entry.actor.username if entry.actor else None,
                "changes": entry.changes_dict,
            })

        return Response(history)


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


class PhotoFilter(filters.FilterSet):
    """Filter for Photo queryset."""

    person = filters.UUIDFilter(field_name="persons__id")
    anecdote = filters.UUIDFilter(field_name="anecdote__id")
    date_from = filters.DateFilter(field_name="date_taken", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date_taken", lookup_expr="lte")
    has_location = filters.BooleanFilter(
        field_name="location",
        lookup_expr="exact",
        exclude=True,
        method="filter_has_location",
    )

    class Meta:
        model = Photo
        fields = ["person", "anecdote", "date_from", "date_to", "has_location"]

    def filter_has_location(self, queryset, name, value):
        if value:
            return queryset.exclude(location="")
        return queryset.filter(location="")


class PhotoViewSet(viewsets.ModelViewSet):
    """ViewSet for Photo CRUD operations."""

    queryset = Photo.objects.prefetch_related("persons").select_related("anecdote").all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = PhotoFilter
    search_fields = ["caption", "location", "ai_description"]
    ordering_fields = ["date_taken", "created_at"]
    ordering = ["-date_taken", "-created_at"]

    @action(detail=True, methods=["post"])
    def generate_description(self, request, pk=None):
        """Generate AI description for a photo."""
        photo = self.get_object()
        return Response(
            {"message": "AI description generation not yet implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class EmploymentFilter(filters.FilterSet):
    """Filter for Employment queryset."""

    person = filters.UUIDFilter(field_name="person__id")
    company = filters.CharFilter(lookup_expr="icontains")
    is_current = filters.BooleanFilter()
    start_after = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    end_before = filters.DateFilter(field_name="end_date", lookup_expr="lte")

    class Meta:
        model = Employment
        fields = ["person", "company", "is_current", "start_after", "end_before"]


class EmploymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Employment CRUD operations."""

    queryset = Employment.objects.select_related("person").all()
    serializer_class = EmploymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = EmploymentFilter
    search_fields = ["company", "title", "department", "description"]
    ordering_fields = ["start_date", "end_date", "company", "created_at"]
    ordering = ["-is_current", "-start_date"]


class GlobalSearchView(APIView):
    """
    Full-text search across all major models.

    Supports searching across Person, Anecdote, and Employment.
    Uses PostgreSQL's full-text search for relevance ranking.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response({
                "persons": [],
                "anecdotes": [],
                "employments": [],
            })

        # Use PostgreSQL full-text search
        search_query = SearchQuery(query, search_type="websearch")

        # Search persons
        person_vector = SearchVector(
            "name", weight="A"
        ) + SearchVector(
            "nickname", weight="A"
        ) + SearchVector(
            "notes", weight="B"
        ) + SearchVector(
            "met_context", weight="C"
        )

        persons = (
            Person.objects.annotate(
                search=person_vector,
                rank=SearchRank(person_vector, search_query),
            )
            .filter(
                Q(search=search_query) | Q(name__icontains=query) | Q(nickname__icontains=query),
                is_active=True,
            )
            .order_by("-rank")[:20]
        )

        person_results = PersonListSerializer(persons, many=True).data

        # Search anecdotes
        anecdote_vector = SearchVector(
            "title", weight="A"
        ) + SearchVector(
            "content", weight="B"
        ) + SearchVector(
            "location", weight="C"
        )

        anecdotes = (
            Anecdote.objects.annotate(
                search=anecdote_vector,
                rank=SearchRank(anecdote_vector, search_query),
            )
            .filter(
                Q(search=search_query) | Q(title__icontains=query) | Q(content__icontains=query)
            )
            .prefetch_related("persons", "tags")
            .order_by("-rank")[:20]
        )

        anecdote_results = AnecdoteSerializer(anecdotes, many=True).data

        # Search employments
        employment_vector = SearchVector(
            "company", weight="A"
        ) + SearchVector(
            "title", weight="A"
        ) + SearchVector(
            "department", weight="B"
        ) + SearchVector(
            "description", weight="C"
        )

        employments = (
            Employment.objects.annotate(
                search=employment_vector,
                rank=SearchRank(employment_vector, search_query),
            )
            .filter(
                Q(search=search_query) | Q(company__icontains=query) | Q(title__icontains=query)
            )
            .select_related("person")
            .order_by("-rank")[:20]
        )

        employment_results = EmploymentSerializer(employments, many=True).data

        return Response({
            "persons": person_results,
            "anecdotes": anecdote_results,
            "employments": employment_results,
            "query": query,
        })
