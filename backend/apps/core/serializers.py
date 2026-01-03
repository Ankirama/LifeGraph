"""
Core app serializers.
"""

from rest_framework import serializers

from .models import Group, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    class Meta:
        model = Tag
        fields = ["id", "name", "color", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Group model."""

    full_path = serializers.ReadOnlyField()
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "description",
            "parent",
            "color",
            "full_path",
            "children_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "full_path", "children_count", "created_at", "updated_at"]

    def get_children_count(self, obj) -> int:
        return obj.children.count()
