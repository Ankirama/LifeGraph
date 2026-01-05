"""
Photo-related views.
"""

import logging

from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.ratelimit import ai_ratelimit

from ..exceptions import AIServiceError
from ..models import Photo
from ..serializers import PhotoSerializer
from ..services import generate_photo_description


logger = logging.getLogger(__name__)


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

    @method_decorator(ai_ratelimit())
    @action(detail=True, methods=["post"])
    def generate_description(self, request, pk=None):
        """Generate AI description for a photo using OpenAI Vision. Rate limited."""
        photo = self.get_object()
        logger.info(f"Generating AI description for photo: {photo.id}")

        # Build full URL for the image
        if hasattr(photo.file, 'url'):
            # Get the full URL including domain
            image_url = request.build_absolute_uri(photo.file.url)
        else:
            return Response(
                {"detail": "Photo file not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get person names for context
        person_names = list(photo.persons.values_list("first_name", flat=True))

        try:
            description = generate_photo_description(image_url, person_names or None)

            # Save the description
            photo.ai_description = description
            photo.save(update_fields=["ai_description"])

            logger.info(f"Successfully generated description for photo {photo.id}")
            return Response({
                "photo_id": str(photo.id),
                "ai_description": description,
                "person_context": person_names,
            })

        except Exception as e:
            logger.error(f"Failed to generate photo description for {photo.id}: {e}")
            raise AIServiceError(detail=f"Failed to generate description: {str(e)}")
