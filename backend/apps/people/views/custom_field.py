"""
Custom field views.
"""

from rest_framework import viewsets

from ..models import CustomFieldDefinition
from ..serializers import CustomFieldDefinitionSerializer


class CustomFieldDefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet for CustomFieldDefinition CRUD operations."""

    queryset = CustomFieldDefinition.objects.all()
    serializer_class = CustomFieldDefinitionSerializer
    ordering = ["order", "name"]
