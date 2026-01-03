"""
People app views.
"""

from datetime import date, timedelta

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
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
from .services import (
    chat_with_context,
    generate_person_summary,
    parse_contacts_text,
    parse_updates_text,
)


class PersonFilter(filters.FilterSet):
    """Filter for Person queryset."""

    first_name = filters.CharFilter(lookup_expr="icontains")
    last_name = filters.CharFilter(lookup_expr="icontains")
    name = filters.CharFilter(method="filter_by_name")
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
        fields = ["first_name", "last_name", "name", "tag", "group", "has_birthday", "is_active"]

    def filter_by_name(self, queryset, name, value):
        """Filter by first_name OR last_name containing the value."""
        return queryset.filter(
            Q(first_name__icontains=value) | Q(last_name__icontains=value)
        )


class PersonViewSet(viewsets.ModelViewSet):
    """ViewSet for Person CRUD operations."""

    queryset = Person.objects.prefetch_related("tags", "groups").filter(is_active=True, is_owner=False)
    filterset_class = PersonFilter
    search_fields = ["first_name", "last_name", "nickname", "notes", "met_context"]
    ordering_fields = ["first_name", "last_name", "birthday", "last_contact", "created_at"]
    ordering = ["last_name", "first_name"]

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
        """Get all relationships for a person.

        Only returns relationships where the person is person_a.
        This avoids duplicates when auto_create_inverse is enabled,
        as each relationship pair has a canonical direction.
        """
        person = self.get_object()
        relationships = Relationship.objects.filter(
            person_a=person
        ).select_related("person_b", "relationship_type")

        serializer = RelationshipSerializer(relationships, many=True)
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
        person = self.get_object()

        # Get owner for relationship context
        owner = Person.objects.filter(is_owner=True).first()

        # Build person data for summary generation
        profile_data = {
            "full_name": person.full_name,
            "nickname": person.nickname,
            "birthday": person.birthday.isoformat() if person.birthday else None,
            "notes": person.notes,
            "met_date": person.met_date.isoformat() if person.met_date else None,
            "met_context": person.met_context,
        }

        # Get relationship to owner
        if owner:
            rel = Relationship.objects.filter(
                person_a=person, person_b=owner
            ).select_related("relationship_type").first()
            if rel:
                profile_data["relationship_to_owner"] = rel.relationship_type.name

        # Get relationships with other people
        relationships_data = []
        for rel in Relationship.objects.filter(person_a=person).select_related("person_b", "relationship_type")[:10]:
            if rel.person_b != owner:
                relationships_data.append({
                    "type": rel.relationship_type.name,
                    "person_name": rel.person_b.full_name,
                })

        # Get anecdotes
        anecdotes_data = []
        for anecdote in person.anecdotes.all()[:10]:
            anecdotes_data.append({
                "type": anecdote.anecdote_type,
                "title": anecdote.title,
                "content": anecdote.content,
                "date": anecdote.date.isoformat() if anecdote.date else None,
            })

        # Get employment history
        employments_data = []
        for emp in person.employments.all()[:5]:
            employments_data.append({
                "company": emp.company,
                "title": emp.title,
                "is_current": emp.is_current,
            })

        person_data = {
            "profile": profile_data,
            "relationships": relationships_data,
            "anecdotes": anecdotes_data,
            "employments": employments_data,
        }

        try:
            summary = generate_person_summary(person_data)

            # Save the summary to the person's ai_summary field
            person.ai_summary = summary
            person.save(update_fields=["ai_summary"])

            return Response({
                "summary": summary,
                "person_id": str(person.id),
                "person_name": person.full_name,
            })
        except Exception as e:
            return Response(
                {"detail": f"Failed to generate summary: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    filterset_class = AnecdoteFilter
    search_fields = ["title", "content", "location"]
    ordering_fields = ["date", "created_at", "anecdote_type"]
    ordering = ["-date", "-created_at"]


class CustomFieldDefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet for CustomFieldDefinition CRUD operations."""

    queryset = CustomFieldDefinition.objects.all()
    serializer_class = CustomFieldDefinitionSerializer
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
    filterset_class = EmploymentFilter
    search_fields = ["company", "title", "department", "description"]
    ordering_fields = ["start_date", "end_date", "company", "created_at"]
    ordering = ["-is_current", "-start_date"]


class MeView(APIView):
    """
    Get or create the CRM owner (you).

    GET: Returns the owner record if it exists, 404 otherwise
    POST: Creates the owner record (only one allowed)
    PUT/PATCH: Updates the owner record
    """

    def get(self, request):
        try:
            owner = Person.objects.get(is_owner=True)
            serializer = PersonDetailSerializer(owner)
            return Response(serializer.data)
        except Person.DoesNotExist:
            return Response(
                {"detail": "Owner profile not set up yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request):
        # Check if owner already exists
        if Person.objects.filter(is_owner=True).exists():
            return Response(
                {"detail": "Owner profile already exists. Use PUT to update."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PersonCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            person = serializer.save(is_owner=True)
            return Response(
                PersonDetailSerializer(person).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            owner = Person.objects.get(is_owner=True)
        except Person.DoesNotExist:
            return Response(
                {"detail": "Owner profile not set up yet. Use POST to create."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PersonCreateUpdateSerializer(owner, data=request.data)
        if serializer.is_valid():
            person = serializer.save()
            return Response(PersonDetailSerializer(person).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            owner = Person.objects.get(is_owner=True)
        except Person.DoesNotExist:
            return Response(
                {"detail": "Owner profile not set up yet. Use POST to create."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PersonCreateUpdateSerializer(owner, data=request.data, partial=True)
        if serializer.is_valid():
            person = serializer.save()
            return Response(PersonDetailSerializer(person).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GlobalSearchView(APIView):
    """
    Full-text search across all major models.

    Supports searching across Person, Anecdote, and Employment.
    Uses PostgreSQL's full-text search for relevance ranking.
    """

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
            "first_name", weight="A"
        ) + SearchVector(
            "last_name", weight="A"
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
                Q(search=search_query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(nickname__icontains=query),
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


class AIParseContactsView(APIView):
    """
    Parse natural language text into structured contact data using AI.

    POST: Accepts text describing contacts and returns parsed structured data.
    """

    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response(
                {"detail": "Text is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(text) > 10000:
            return Response(
                {"detail": "Text too long. Maximum 10,000 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = parse_contacts_text(text)
            return Response(result)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"detail": f"AI parsing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIBulkImportView(APIView):
    """
    Bulk import contacts from AI-parsed data.

    POST: Creates persons and relationships from parsed contact data.
    """

    def post(self, request):
        persons_data = request.data.get("persons", [])
        if not persons_data:
            return Response(
                {"detail": "No persons data provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the owner for creating relationships
        try:
            owner = Person.objects.get(is_owner=True)
        except Person.DoesNotExist:
            return Response(
                {"detail": "Owner profile not set up. Please create your profile first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_persons = []
        created_relationships = []
        errors = []

        for idx, person_data in enumerate(persons_data):
            try:
                # Create the person
                person = Person.objects.create(
                    first_name=person_data.get("first_name", ""),
                    last_name=person_data.get("last_name", ""),
                    nickname=person_data.get("nickname", ""),
                    birthday=person_data.get("birthday"),
                    notes=person_data.get("notes", ""),
                )
                created_persons.append(PersonListSerializer(person).data)

                # Create relationship if specified
                relationship_name = person_data.get("relationship_to_owner", "").strip().lower()
                if relationship_name:
                    # Find matching relationship type
                    relationship_type = RelationshipType.objects.filter(
                        Q(name__iexact=relationship_name) | Q(inverse_name__iexact=relationship_name)
                    ).first()

                    if relationship_type:
                        # Determine the correct direction:
                        # If the person is "mother" to owner, then:
                        # - person_a = person (the mother)
                        # - person_b = owner (me)
                        # - relationship_type should have name="mother"
                        if relationship_type.name.lower() == relationship_name:
                            # Direct match: person is [name] to owner
                            rel = Relationship.objects.create(
                                person_a=person,
                                person_b=owner,
                                relationship_type=relationship_type,
                            )
                        else:
                            # Inverse match: owner is [name] to person
                            # So we flip: person_a = owner, person_b = person
                            rel = Relationship.objects.create(
                                person_a=owner,
                                person_b=person,
                                relationship_type=relationship_type,
                            )
                        created_relationships.append(RelationshipSerializer(rel).data)
                    else:
                        errors.append(f"Person {idx + 1}: Relationship type '{relationship_name}' not found")

            except Exception as e:
                errors.append(f"Person {idx + 1}: {str(e)}")

        return Response({
            "created_persons": created_persons,
            "created_relationships": created_relationships,
            "errors": errors,
            "summary": {
                "persons_created": len(created_persons),
                "relationships_created": len(created_relationships),
                "errors_count": len(errors),
            }
        }, status=status.HTTP_201_CREATED if created_persons else status.HTTP_400_BAD_REQUEST)


class AIParseUpdatesView(APIView):
    """
    Parse natural language text into updates for existing contacts using AI.

    POST: Accepts text describing updates/memories and returns parsed structured data.
    """

    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response(
                {"detail": "Text is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(text) > 10000:
            return Response(
                {"detail": "Text too long. Maximum 10,000 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get existing contacts with their relationships to owner
        try:
            owner = Person.objects.get(is_owner=True)
        except Person.DoesNotExist:
            owner = None

        # Build list of existing contacts with relationship info
        existing_contacts = []
        for person in Person.objects.filter(is_active=True, is_owner=False):
            contact_info = {
                "id": str(person.id),
                "full_name": person.full_name,
                "relationship_to_me": None,
            }

            # Get relationship to owner if owner exists
            if owner:
                rel = Relationship.objects.filter(
                    person_a=person, person_b=owner
                ).select_related("relationship_type").first()
                if rel:
                    contact_info["relationship_to_me"] = rel.relationship_type.name

                if not contact_info["relationship_to_me"]:
                    rel = Relationship.objects.filter(
                        person_a=owner, person_b=person
                    ).select_related("relationship_type").first()
                    if rel:
                        contact_info["relationship_to_me"] = rel.relationship_type.inverse_name

            existing_contacts.append(contact_info)

        try:
            result = parse_updates_text(text, existing_contacts)
            return Response(result)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"detail": f"AI parsing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIApplyUpdatesView(APIView):
    """
    Apply AI-parsed updates to existing contacts.

    POST: Applies field updates and creates anecdotes from parsed data.
    """

    def post(self, request):
        updates_data = request.data.get("updates", [])
        if not updates_data:
            return Response(
                {"detail": "No updates data provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_persons = []
        created_anecdotes = []
        errors = []

        for idx, update in enumerate(updates_data):
            person_id = update.get("matched_person_id")
            if not person_id:
                errors.append(f"Update {idx + 1}: No matched person ID")
                continue

            try:
                person = Person.objects.get(id=person_id, is_active=True)
            except Person.DoesNotExist:
                errors.append(f"Update {idx + 1}: Person not found")
                continue

            try:
                # Apply field updates
                field_updates = update.get("field_updates", {})
                fields_changed = []

                if field_updates.get("birthday"):
                    person.birthday = field_updates["birthday"]
                    fields_changed.append("birthday")

                if field_updates.get("nickname"):
                    person.nickname = field_updates["nickname"]
                    fields_changed.append("nickname")

                if field_updates.get("notes_to_append"):
                    if person.notes:
                        person.notes = f"{person.notes}\n\n{field_updates['notes_to_append']}"
                    else:
                        person.notes = field_updates["notes_to_append"]
                    fields_changed.append("notes")

                if fields_changed:
                    person.save()
                    updated_persons.append({
                        "id": str(person.id),
                        "full_name": person.full_name,
                        "fields_updated": fields_changed,
                    })

                # Create anecdotes
                for anecdote_data in update.get("anecdotes", []):
                    anecdote = Anecdote.objects.create(
                        title=anecdote_data.get("title", ""),
                        content=anecdote_data["content"],
                        anecdote_type=anecdote_data.get("anecdote_type", "note"),
                        date=anecdote_data.get("date"),
                        location=anecdote_data.get("location", ""),
                    )
                    anecdote.persons.add(person)
                    created_anecdotes.append({
                        "id": str(anecdote.id),
                        "title": anecdote.title,
                        "content": anecdote.content[:100] + "..." if len(anecdote.content) > 100 else anecdote.content,
                        "person_name": person.full_name,
                    })

            except Exception as e:
                errors.append(f"Update {idx + 1}: {str(e)}")

        return Response({
            "updated_persons": updated_persons,
            "created_anecdotes": created_anecdotes,
            "errors": errors,
            "summary": {
                "persons_updated": len(updated_persons),
                "anecdotes_created": len(created_anecdotes),
                "errors_count": len(errors),
            }
        }, status=status.HTTP_200_OK if (updated_persons or created_anecdotes) else status.HTTP_400_BAD_REQUEST)


class DashboardView(APIView):
    """Dashboard statistics and recent activity."""

    def get(self, request):
        today = date.today()

        # Get counts (exclude owner from person count)
        total_persons = Person.objects.filter(is_active=True, is_owner=False).count()
        total_relationships = Relationship.objects.count()
        total_anecdotes = Anecdote.objects.count()
        total_photos = Photo.objects.count()

        # Upcoming birthdays (next 30 days)
        upcoming_birthdays = []
        persons_with_birthday = Person.objects.filter(
            is_active=True,
            is_owner=False,
            birthday__isnull=False
        )

        for person in persons_with_birthday:
            # Calculate this year's birthday
            try:
                birthday_this_year = person.birthday.replace(year=today.year)
            except ValueError:
                # Handle Feb 29 for non-leap years
                birthday_this_year = person.birthday.replace(year=today.year, day=28)

            # If birthday already passed this year, check next year
            if birthday_this_year < today:
                try:
                    birthday_this_year = person.birthday.replace(year=today.year + 1)
                except ValueError:
                    birthday_this_year = person.birthday.replace(year=today.year + 1, day=28)

            days_until = (birthday_this_year - today).days
            if 0 <= days_until <= 30:
                # Calculate age they'll be turning
                age = birthday_this_year.year - person.birthday.year
                upcoming_birthdays.append({
                    "id": str(person.id),
                    "full_name": person.full_name,
                    "birthday": person.birthday.isoformat(),
                    "days_until": days_until,
                    "turning_age": age,
                    "date": birthday_this_year.isoformat(),
                })

        # Sort by days until
        upcoming_birthdays.sort(key=lambda x: x["days_until"])

        # Recent anecdotes (last 10)
        recent_anecdotes = []
        for anecdote in Anecdote.objects.prefetch_related("persons")[:10]:
            person_names = [p.full_name for p in anecdote.persons.all()[:3]]
            recent_anecdotes.append({
                "id": str(anecdote.id),
                "title": anecdote.title,
                "content": anecdote.content[:150] + "..." if len(anecdote.content) > 150 else anecdote.content,
                "anecdote_type": anecdote.anecdote_type,
                "date": anecdote.date.isoformat() if anecdote.date else None,
                "persons": person_names,
                "created_at": anecdote.created_at.isoformat(),
            })

        # Recently added people (last 10)
        recent_persons = []
        owner = Person.objects.filter(is_owner=True).first()
        for person in Person.objects.filter(is_active=True, is_owner=False).order_by("-created_at")[:10]:
            # Get relationship to owner (what this person IS to me)
            relationship_to_me = None
            if owner:
                # Look for relationship where this person is related TO the owner
                rel = Relationship.objects.filter(
                    person_a=person,
                    person_b=owner
                ).select_related("relationship_type").first()
                if rel:
                    relationship_to_me = rel.relationship_type.name

            recent_persons.append({
                "id": str(person.id),
                "full_name": person.full_name,
                "relationship_to_me": relationship_to_me,
                "created_at": person.created_at.isoformat(),
            })

        # Relationship type distribution
        relationship_stats = list(
            Relationship.objects.values("relationship_type__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        return Response({
            "stats": {
                "total_persons": total_persons,
                "total_relationships": total_relationships,
                "total_anecdotes": total_anecdotes,
                "total_photos": total_photos,
            },
            "upcoming_birthdays": upcoming_birthdays[:10],
            "recent_anecdotes": recent_anecdotes,
            "recent_persons": recent_persons,
            "relationship_distribution": [
                {"name": r["relationship_type__name"], "count": r["count"]}
                for r in relationship_stats
            ],
        })


class AIChatView(APIView):
    """
    AI-powered chat about contacts.

    POST: Answer questions about the user's contacts using AI.
    """

    def post(self, request):
        question = request.data.get("question", "").strip()
        if not question:
            return Response(
                {"detail": "Question is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(question) > 2000:
            return Response(
                {"detail": "Question too long. Maximum 2,000 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get conversation history if provided
        conversation_history = request.data.get("history", [])

        # Build contacts context
        owner = Person.objects.filter(is_owner=True).first()
        context_parts = []

        # Add owner info
        if owner:
            context_parts.append(f"Owner (You): {owner.full_name}")

        # Add all contacts with their relationships and key info
        for person in Person.objects.filter(is_active=True, is_owner=False).prefetch_related("anecdotes", "employments")[:100]:
            person_info = [f"\n### {person.full_name}"]

            # Get relationship to owner
            if owner:
                rel = Relationship.objects.filter(
                    person_a=person, person_b=owner
                ).select_related("relationship_type").first()
                if rel:
                    person_info.append(f"Relationship: {rel.relationship_type.name}")

            if person.birthday:
                person_info.append(f"Birthday: {person.birthday.isoformat()}")

            if person.nickname:
                person_info.append(f"Nickname: {person.nickname}")

            if person.notes:
                person_info.append(f"Notes: {person.notes[:200]}")

            # Current employment
            current_job = person.employments.filter(is_current=True).first()
            if current_job:
                person_info.append(f"Current job: {current_job.title} at {current_job.company}")

            # Recent anecdotes (limit to 3)
            anecdotes = person.anecdotes.all()[:3]
            if anecdotes:
                anecdote_texts = []
                for a in anecdotes:
                    anecdote_texts.append(f"- [{a.anecdote_type}] {a.title or ''}: {a.content[:100]}")
                person_info.append(f"Anecdotes:\n" + "\n".join(anecdote_texts))

            context_parts.append("\n".join(person_info))

        contacts_context = "\n".join(context_parts)
        today_date = date.today().isoformat()

        try:
            response = chat_with_context(
                question=question,
                contacts_context=contacts_context,
                today_date=today_date,
                conversation_history=conversation_history,
            )

            return Response({
                "answer": response,
                "question": question,
            })
        except Exception as e:
            return Response(
                {"detail": f"Chat failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
