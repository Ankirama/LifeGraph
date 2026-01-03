"""
People app admin configuration.
"""

from django.contrib import admin

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


class CustomFieldValueInline(admin.TabularInline):
    model = CustomFieldValue
    extra = 0


class EmploymentInline(admin.TabularInline):
    model = Employment
    extra = 0
    fields = ["company", "title", "is_current", "start_date", "end_date"]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["name", "nickname", "birthday", "is_active", "last_contact", "created_at"]
    list_filter = ["is_active", "groups", "tags"]
    search_fields = ["name", "nickname", "notes", "met_context"]
    filter_horizontal = ["groups", "tags"]
    inlines = [CustomFieldValueInline, EmploymentInline]
    readonly_fields = ["ai_summary", "ai_summary_updated", "created_at", "updated_at"]
    fieldsets = (
        ("Identity", {
            "fields": ("name", "nickname", "avatar", "is_active")
        }),
        ("Dates", {
            "fields": ("birthday", "met_date", "met_context", "last_contact")
        }),
        ("Contact", {
            "fields": ("emails", "phones", "addresses"),
            "classes": ("collapse",)
        }),
        ("Social", {
            "fields": ("linkedin_url", "discord_id"),
            "classes": ("collapse",)
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
        ("AI", {
            "fields": ("ai_summary", "ai_summary_updated"),
            "classes": ("collapse",)
        }),
        ("Organization", {
            "fields": ("groups", "tags")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(RelationshipType)
class RelationshipTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "inverse_name", "category", "is_symmetric", "auto_create_inverse"]
    list_filter = ["category", "is_symmetric"]
    search_fields = ["name", "inverse_name"]


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ["person_a", "relationship_type", "person_b", "auto_created", "created_at"]
    list_filter = ["relationship_type", "auto_created"]
    search_fields = ["person_a__name", "person_b__name"]
    raw_id_fields = ["person_a", "person_b"]


@admin.register(Anecdote)
class AnecdoteAdmin(admin.ModelAdmin):
    list_display = ["title", "anecdote_type", "date", "created_at"]
    list_filter = ["anecdote_type", "tags"]
    search_fields = ["title", "content", "location"]
    filter_horizontal = ["persons", "tags"]


@admin.register(CustomFieldDefinition)
class CustomFieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ["name", "field_type", "is_required", "order"]
    list_filter = ["field_type", "is_required"]
    search_fields = ["name"]


@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(admin.ModelAdmin):
    list_display = ["person", "definition", "value"]
    list_filter = ["definition"]
    search_fields = ["person__name"]
    raw_id_fields = ["person"]


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ["id", "caption", "date_taken", "location", "created_at"]
    list_filter = ["date_taken"]
    search_fields = ["caption", "location", "ai_description"]
    filter_horizontal = ["persons"]
    raw_id_fields = ["anecdote"]
    readonly_fields = ["ai_description", "detected_faces", "created_at", "updated_at"]
    fieldsets = (
        (None, {
            "fields": ("file", "caption")
        }),
        ("Metadata", {
            "fields": ("date_taken", "location", "location_coords")
        }),
        ("AI", {
            "fields": ("ai_description", "detected_faces"),
            "classes": ("collapse",)
        }),
        ("Associations", {
            "fields": ("persons", "anecdote")
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Employment)
class EmploymentAdmin(admin.ModelAdmin):
    list_display = ["person", "title", "company", "is_current", "start_date", "end_date"]
    list_filter = ["is_current", "linkedin_synced"]
    search_fields = ["person__name", "company", "title", "department"]
    raw_id_fields = ["person"]
    readonly_fields = ["linkedin_synced", "linkedin_last_sync", "created_at", "updated_at"]
    fieldsets = (
        (None, {
            "fields": ("person",)
        }),
        ("Position", {
            "fields": ("company", "title", "department", "location")
        }),
        ("Dates", {
            "fields": ("start_date", "end_date", "is_current")
        }),
        ("Details", {
            "fields": ("description",)
        }),
        ("LinkedIn", {
            "fields": ("linkedin_synced", "linkedin_last_sync"),
            "classes": ("collapse",)
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
