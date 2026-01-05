"""
People app views - organized into modules for maintainability.

All views are re-exported here for backward compatibility.
"""

# Person views
from .person import PersonFilter, PersonViewSet

# Relationship views
from .relationship import RelationshipGraphView, RelationshipTypeViewSet, RelationshipViewSet

# Anecdote views
from .anecdote import AnecdoteFilter, AnecdoteViewSet

# Photo views
from .photo import PhotoFilter, PhotoViewSet

# Employment views
from .employment import EmploymentFilter, EmploymentViewSet

# Custom field views
from .custom_field import CustomFieldDefinitionViewSet

# Dashboard and search views
from .dashboard import DashboardView, GlobalSearchView, MeView

# AI views
from .ai import (
    AIApplyRelationshipSuggestionView,
    AIApplyUpdatesView,
    AIBulkImportView,
    AIChatView,
    AIParseContactsView,
    AIParseUpdatesView,
    AISmartSearchView,
    AISuggestRelationshipsView,
)

# Export views
from .export import ExportDataView, ExportPreviewView


__all__ = [
    # Person
    "PersonFilter",
    "PersonViewSet",
    # Relationship
    "RelationshipTypeViewSet",
    "RelationshipViewSet",
    "RelationshipGraphView",
    # Anecdote
    "AnecdoteFilter",
    "AnecdoteViewSet",
    # Photo
    "PhotoFilter",
    "PhotoViewSet",
    # Employment
    "EmploymentFilter",
    "EmploymentViewSet",
    # Custom Field
    "CustomFieldDefinitionViewSet",
    # Dashboard
    "MeView",
    "DashboardView",
    "GlobalSearchView",
    # AI
    "AIParseContactsView",
    "AIBulkImportView",
    "AIParseUpdatesView",
    "AIApplyUpdatesView",
    "AIChatView",
    "AISuggestRelationshipsView",
    "AIApplyRelationshipSuggestionView",
    "AISmartSearchView",
    # Export
    "ExportDataView",
    "ExportPreviewView",
]
