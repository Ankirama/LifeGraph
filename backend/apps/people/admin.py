"""
People app admin configuration.
"""

from django.contrib import admin

from .models import (
    Anecdote,
    CustomFieldDefinition,
    CustomFieldValue,
    Person,
    Relationship,
    RelationshipType,
)


class CustomFieldValueInline(admin.TabularInline):
    model = CustomFieldValue
    extra = 0


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["name", "nickname", "birthday", "is_active", "last_contact", "created_at"]
    list_filter = ["is_active", "groups", "tags"]
    search_fields = ["name", "nickname", "notes", "met_context"]
    filter_horizontal = ["groups", "tags"]
    inlines = [CustomFieldValueInline]
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
