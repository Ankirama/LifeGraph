"""
Person-related views.
"""

import logging

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.models import Tag
from apps.core.ratelimit import ai_ratelimit

from ..exceptions import AIServiceError, LinkedInServiceError
from ..models import Person, Relationship
from ..serializers import (
    AnecdoteSerializer,
    EmploymentSerializer,
    PersonCreateUpdateSerializer,
    PersonDetailSerializer,
    PersonListSerializer,
    PhotoSerializer,
    RelationshipSerializer,
)
from ..services import (
    generate_person_summary,
    suggest_tags_for_person,
    sync_person_from_linkedin,
)


logger = logging.getLogger(__name__)


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

    @method_decorator(ai_ratelimit())
    @action(detail=True, methods=["post"])
    def generate_summary(self, request, pk=None):
        """Generate AI summary for a person. Rate limited to prevent abuse."""
        person = self.get_object()
        logger.info(f"Generating AI summary for person: {person.full_name}")

        # Get owner for relationship context
        owner = Person.objects.filter(is_owner=True).first()

        # Build person data for summary generation
        person_data = self._build_person_data(person, owner)

        try:
            summary = generate_person_summary(person_data)

            # Save the summary to the person's ai_summary field
            person.ai_summary = summary
            person.save(update_fields=["ai_summary"])

            logger.info(f"Successfully generated summary for {person.full_name}")
            return Response({
                "summary": summary,
                "person_id": str(person.id),
                "person_name": person.full_name,
            })
        except Exception as e:
            logger.error(f"Failed to generate summary for {person.full_name}: {e}")
            raise AIServiceError(detail=f"Failed to generate summary: {str(e)}")

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

    @method_decorator(ai_ratelimit())
    @action(detail=True, methods=["post"])
    def suggest_tags(self, request, pk=None):
        """Suggest AI-generated tags for a person. Rate limited to prevent abuse."""
        person = self.get_object()
        logger.info(f"Suggesting tags for person: {person.full_name}")

        # Get owner for relationship context
        owner = Person.objects.filter(is_owner=True).first()

        # Build person data for tag suggestion
        person_data = self._build_person_data(person, owner)

        # Get existing tags
        existing_tags = list(Tag.objects.values_list("name", flat=True))

        try:
            suggested_tags = suggest_tags_for_person(person_data, existing_tags)

            logger.info(f"Suggested {len(suggested_tags)} tags for {person.full_name}")
            return Response({
                "suggested_tags": suggested_tags,
                "person_id": str(person.id),
                "person_name": person.full_name,
                "current_tags": list(person.tags.values_list("name", flat=True)),
            })
        except Exception as e:
            logger.error(f"Failed to suggest tags for {person.full_name}: {e}")
            raise AIServiceError(detail=f"Failed to suggest tags: {str(e)}")

    @action(detail=True, methods=["post"])
    def apply_tags(self, request, pk=None):
        """Apply suggested tags to a person.

        Request body:
        {
            "tags": ["tag-name-1", "tag-name-2"],
            "create_missing": true  // Whether to create tags that don't exist
        }
        """
        person = self.get_object()
        tag_names = request.data.get("tags", [])
        create_missing = request.data.get("create_missing", False)

        if not tag_names:
            return Response(
                {"detail": "No tags provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        applied_tags = []
        created_tags = []
        skipped_tags = []

        for tag_name in tag_names:
            tag_name = tag_name.lower().strip().replace(" ", "-")
            tag = Tag.objects.filter(name__iexact=tag_name).first()

            if tag:
                person.tags.add(tag)
                applied_tags.append(tag_name)
            elif create_missing:
                tag = Tag.objects.create(name=tag_name)
                person.tags.add(tag)
                created_tags.append(tag_name)
                applied_tags.append(tag_name)
            else:
                skipped_tags.append(tag_name)

        return Response({
            "applied_tags": applied_tags,
            "created_tags": created_tags,
            "skipped_tags": skipped_tags,
            "person_id": str(person.id),
            "person_name": person.full_name,
            "current_tags": list(person.tags.values_list("name", flat=True)),
        })

    @action(detail=True, methods=["post"])
    def sync_linkedin(self, request, pk=None):
        """Sync employment data from this person's LinkedIn profile.

        WARNING: Uses unofficial LinkedIn API. Use sparingly to avoid rate limits.
        Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables.
        """
        person = self.get_object()

        if not person.linkedin_url:
            return Response(
                {"detail": "Person has no LinkedIn URL configured."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Syncing LinkedIn data for {person.full_name}")

        try:
            result = sync_person_from_linkedin(person)

            if result.get("errors") and not result.get("synced_count"):
                raise LinkedInServiceError(detail=result["errors"][0])

            logger.info(f"LinkedIn sync complete for {person.full_name}: {result.get('synced_count', 0)} synced")
            return Response({
                "status": "success",
                "person_id": str(person.id),
                "person_name": person.full_name,
                "synced_count": result.get("synced_count", 0),
                "skipped_count": result.get("skipped_count", 0),
                "errors": result.get("errors", []),
                "profile": result.get("profile", {}),
            })
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"LinkedIn sync failed for {person.full_name}: {e}")
            raise LinkedInServiceError(detail=f"LinkedIn sync failed: {str(e)}")

    def _build_person_data(self, person, owner=None):
        """Build person data dictionary for AI services."""
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

        return {
            "profile": profile_data,
            "relationships": relationships_data,
            "anecdotes": anecdotes_data,
            "employments": employments_data,
        }
