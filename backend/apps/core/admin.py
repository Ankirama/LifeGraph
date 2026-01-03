"""
Core app admin configuration.
"""

from django.contrib import admin

from .models import Group, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["name"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "color", "created_at"]
    list_filter = ["parent"]
    search_fields = ["name", "description"]
    ordering = ["name"]
