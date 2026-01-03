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

    primary_email = serializers.ReadOnlyField()
    primary_phone = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Person
        fields = [
            "id",
            "name",
            "nickname",
            "avatar",
            "birthday",
            "primary_email",
            "primary_phone",
            "tags",
            "last_contact",
            "created_at",
        ]


class PersonDetailSerializer(serializers.ModelSerializer):
    """Full serializer for person detail view."""

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
            "name",
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
            "primary_email",
            "primary_phone",
            "ai_summary",
            "ai_summary_updated",
            "custom_fields",
            "created_at",
            "updated_at",
        ]


class PersonCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating persons."""

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
            "name",
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
    """Serializer for relationships."""

    person_a_name = serializers.CharField(source="person_a.name", read_only=True)
    person_b_name = serializers.CharField(source="person_b.name", read_only=True)
    relationship_type_name = serializers.CharField(
        source="relationship_type.name",
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
            "auto_created",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        if data.get("person_a") == data.get("person_b"):
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


class EmploymentSerializer(serializers.ModelSerializer):
    """Serializer for employment history."""

    person_name = serializers.CharField(source="person.name", read_only=True)

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
