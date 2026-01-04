"""
People app serializers.
"""

from rest_framework import serializers

from apps.core.serializers import GroupSerializer, TagSerializer

from .models import (
    Anecdote,
    CustomFieldDefinition,
    CustomFieldValue,
    Employment,
    Person,
    Photo,
    Relationship,
    RelationshipType,
)


class CustomFieldValueSerializer(serializers.ModelSerializer):
    """Serializer for custom field values."""

    field_name = serializers.CharField(source="definition.name", read_only=True)
    field_type = serializers.CharField(source="definition.field_type", read_only=True)

    class Meta:
        model = CustomFieldValue
        fields = ["id", "definition", "field_name", "field_type", "value"]
        read_only_fields = ["id", "field_name", "field_type"]


class PersonListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for person lists."""

    full_name = serializers.ReadOnlyField()
    primary_email = serializers.ReadOnlyField()
    primary_phone = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, read_only=True)
    relationship_to_me = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "nickname",
            "avatar",
            "birthday",
            "primary_email",
            "primary_phone",
            "tags",
            "last_contact",
            "relationship_to_me",
            "created_at",
        ]

    def get_relationship_to_me(self, obj):
        """Get the relationship type name from the perspective of 'Me'."""
        # Try to get owner from context cache first
        owner = self.context.get("owner")
        if owner is None:
            try:
                owner = Person.objects.get(is_owner=True)
                # Cache it in context for subsequent calls
                if hasattr(self, "_context"):
                    self._context["owner"] = owner
            except Person.DoesNotExist:
                return None

        # Find relationship between this person and the owner
        # Check both directions
        relationship = Relationship.objects.filter(
            person_a=obj, person_b=owner
        ).select_related("relationship_type").first()

        if relationship:
            # Person is person_a, owner is person_b
            # "Person is [type.name] to Owner"
            return relationship.relationship_type.name

        relationship = Relationship.objects.filter(
            person_a=owner, person_b=obj
        ).select_related("relationship_type").first()

        if relationship:
            # Owner is person_a, person is person_b
            # "Owner is [type.name] to Person" -> "Person is [inverse_name] to Owner"
            return relationship.relationship_type.inverse_name

        return None


class PersonDetailSerializer(serializers.ModelSerializer):
    """Full serializer for person detail view."""

    full_name = serializers.ReadOnlyField()
    primary_email = serializers.ReadOnlyField()
    primary_phone = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)
    custom_fields = CustomFieldValueSerializer(
        source="custom_field_values",
        many=True,
        read_only=True,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags",
        queryset=serializers.CurrentUserDefault(),
        many=True,
        write_only=True,
        required=False,
    )
    group_ids = serializers.PrimaryKeyRelatedField(
        source="groups",
        queryset=serializers.CurrentUserDefault(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Person
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "nickname",
            "avatar",
            "birthday",
            "met_date",
            "met_context",
            "emails",
            "phones",
            "addresses",
            "linkedin_url",
            "discord_id",
            "notes",
            "is_active",
            "is_owner",
            "ai_summary",
            "ai_summary_updated",
            "last_contact",
            "primary_email",
            "primary_phone",
            "tags",
            "groups",
            "tag_ids",
            "group_ids",
            "custom_fields",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "primary_email",
            "primary_phone",
            "is_owner",
            "ai_summary",
            "ai_summary_updated",
            "custom_fields",
            "created_at",
            "updated_at",
        ]


class PersonCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating persons."""

    # Text fields with blank=True but no default need explicit handling
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    nickname = serializers.CharField(required=False, allow_blank=True, default="")
    met_context = serializers.CharField(required=False, allow_blank=True, default="")
    linkedin_url = serializers.CharField(required=False, allow_blank=True, default="")
    discord_id = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        default=list,
    )
    group_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model = Person
        fields = [
            "id",
            "first_name",
            "last_name",
            "nickname",
            "avatar",
            "birthday",
            "met_date",
            "met_context",
            "emails",
            "phones",
            "addresses",
            "linkedin_url",
            "discord_id",
            "notes",
            "is_active",
            "last_contact",
            "tag_ids",
            "group_ids",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        tag_ids = validated_data.pop("tag_ids", [])
        group_ids = validated_data.pop("group_ids", [])
        person = Person.objects.create(**validated_data)
        if tag_ids:
            person.tags.set(tag_ids)
        if group_ids:
            person.groups.set(group_ids)
        return person

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)
        group_ids = validated_data.pop("group_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tag_ids is not None:
            instance.tags.set(tag_ids)
        if group_ids is not None:
            instance.groups.set(group_ids)

        return instance


class RelationshipTypeSerializer(serializers.ModelSerializer):
    """Serializer for relationship types."""

    class Meta:
        model = RelationshipType
        fields = [
            "id",
            "name",
            "inverse_name",
            "category",
            "is_symmetric",
            "auto_create_inverse",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RelationshipSerializer(serializers.ModelSerializer):
    """Serializer for relationships.

    Note on relationship display:
    - relationship_type_name: what person_a is to person_b (e.g., "daughter")
    - relationship_type_inverse_name: what person_b is to person_a (e.g., "parent")

    When displaying on person_a's page, use inverse_name to show what person_b is to them.
    """

    person_a_name = serializers.CharField(source="person_a.full_name", read_only=True)
    person_b_name = serializers.CharField(source="person_b.full_name", read_only=True)
    relationship_type_name = serializers.CharField(
        source="relationship_type.name",
        read_only=True,
    )
    relationship_type_inverse_name = serializers.CharField(
        source="relationship_type.inverse_name",
        read_only=True,
    )

    class Meta:
        model = Relationship
        fields = [
            "id",
            "person_a",
            "person_a_name",
            "person_b",
            "person_b_name",
            "relationship_type",
            "relationship_type_name",
            "relationship_type_inverse_name",
            "started_date",
            "notes",
            "strength",
            "auto_created",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "person_a_name",
            "person_b_name",
            "relationship_type_name",
            "relationship_type_inverse_name",
            "auto_created",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        # Get person_a and person_b - use instance values for update if not in data
        person_a = data.get("person_a")
        person_b = data.get("person_b")

        # For updates, use existing instance values if not being changed
        if self.instance:
            if person_a is None:
                person_a = self.instance.person_a
            if person_b is None:
                person_b = self.instance.person_b

        # Only validate if we have both values
        if person_a and person_b and person_a == person_b:
            raise serializers.ValidationError(
                "A person cannot have a relationship with themselves."
            )
        return data


class AnecdoteSerializer(serializers.ModelSerializer):
    """Serializer for anecdotes."""

    persons = PersonListSerializer(many=True, read_only=True)
    person_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True,
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model = Anecdote
        fields = [
            "id",
            "title",
            "content",
            "date",
            "location",
            "persons",
            "person_ids",
            "anecdote_type",
            "tags",
            "tag_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "persons", "tags", "created_at", "updated_at"]

    def create(self, validated_data):
        person_ids = validated_data.pop("person_ids", [])
        tag_ids = validated_data.pop("tag_ids", [])
        anecdote = Anecdote.objects.create(**validated_data)
        anecdote.persons.set(person_ids)
        if tag_ids:
            anecdote.tags.set(tag_ids)
        return anecdote

    def update(self, instance, validated_data):
        person_ids = validated_data.pop("person_ids", None)
        tag_ids = validated_data.pop("tag_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if person_ids is not None:
            instance.persons.set(person_ids)
        if tag_ids is not None:
            instance.tags.set(tag_ids)

        return instance


class CustomFieldDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for custom field definitions."""

    class Meta:
        model = CustomFieldDefinition
        fields = [
            "id",
            "name",
            "field_type",
            "options",
            "is_required",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PhotoSerializer(serializers.ModelSerializer):
    """Serializer for photos."""

    persons = PersonListSerializer(many=True, read_only=True)
    person_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model = Photo
        fields = [
            "id",
            "file",
            "caption",
            "date_taken",
            "location",
            "location_coords",
            "ai_description",
            "detected_faces",
            "persons",
            "person_ids",
            "anecdote",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "ai_description",
            "detected_faces",
            "persons",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        person_ids = validated_data.pop("person_ids", [])
        photo = Photo.objects.create(**validated_data)
        if person_ids:
            photo.persons.set(person_ids)
        return photo

    def update(self, instance, validated_data):
        person_ids = validated_data.pop("person_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if person_ids is not None:
            instance.persons.set(person_ids)

        return instance


class GraphNodeSerializer(serializers.ModelSerializer):
    """Lightweight serializer for graph nodes (persons)."""

    label = serializers.CharField(source="full_name", read_only=True)

    class Meta:
        model = Person
        fields = ["id", "label", "first_name", "last_name", "avatar"]


class GraphEdgeSerializer(serializers.Serializer):
    """Serializer for graph edges (relationships)."""

    id = serializers.UUIDField()
    source = serializers.UUIDField()
    target = serializers.UUIDField()
    type = serializers.CharField()
    type_name = serializers.CharField()
    inverse_name = serializers.CharField()
    category = serializers.CharField()
    strength = serializers.IntegerField()
    is_symmetric = serializers.BooleanField()


class RelationshipGraphSerializer(serializers.Serializer):
    """Serializer for the full relationship graph data."""

    nodes = GraphNodeSerializer(many=True)
    edges = GraphEdgeSerializer(many=True)
    relationship_types = serializers.ListField(child=serializers.DictField())
    center_person_id = serializers.UUIDField(allow_null=True)


class EmploymentSerializer(serializers.ModelSerializer):
    """Serializer for employment history."""

    person_name = serializers.CharField(source="person.full_name", read_only=True)

    class Meta:
        model = Employment
        fields = [
            "id",
            "person",
            "person_name",
            "company",
            "title",
            "department",
            "start_date",
            "end_date",
            "is_current",
            "location",
            "description",
            "linkedin_synced",
            "linkedin_last_sync",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "person_name",
            "linkedin_synced",
            "linkedin_last_sync",
            "created_at",
            "updated_at",
        ]
