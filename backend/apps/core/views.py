"""
Core app views.
"""

from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Group, Tag
from .serializers import GroupSerializer, TagSerializer


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
    """Global search across persons and anecdotes."""

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {"error": "Query must be at least 2 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: Implement search across persons and anecdotes
        results = {
            "persons": [],
            "anecdotes": [],
            "query": query,
        }
        return Response(results)


class HealthCheckView(APIView):
    """Health check endpoint for monitoring."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "healthy", "service": "lifegraph-api"})
