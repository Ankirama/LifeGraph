"""
Core app views.
"""

from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Group, Tag
from .serializers import GroupSerializer, TagSerializer


def ratelimited_error(request, exception):
    """
    Custom error view for rate limited requests.
    Returns a JSON response with rate limit information.
    """
    return JsonResponse(
        {
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down and try again later.",
            "retry_after": getattr(exception, "retry_after", 60),
        },
        status=429,
    )


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for Tag CRUD operations."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet for Group CRUD operations."""

    queryset = Group.objects.select_related("parent").all()
    serializer_class = GroupSerializer
    search_fields = ["name", "description"]
    filterset_fields = ["parent"]
    ordering_fields = ["name", "created_at"]


class GlobalSearchView(APIView):
    """
    Global search across persons and anecdotes.

    Note: The full implementation is in apps.people.views.GlobalSearchView
    which uses PostgreSQL full-text search. This view is kept for potential
    future use as an alternative/fallback search endpoint.
    """

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {"error": "Query must be at least 2 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = {
            "persons": [],
            "anecdotes": [],
            "employments": [],
            "query": query,
        }
        return Response(results)


class HealthCheckView(APIView):
    """Health check endpoint for monitoring."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "healthy", "service": "lifegraph-api"})
