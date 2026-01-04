"""
People app URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"persons", views.PersonViewSet)
router.register(r"relationship-types", views.RelationshipTypeViewSet)
router.register(r"relationships", views.RelationshipViewSet)
router.register(r"anecdotes", views.AnecdoteViewSet)
router.register(r"custom-fields", views.CustomFieldDefinitionViewSet)
router.register(r"photos", views.PhotoViewSet)
router.register(r"employments", views.EmploymentViewSet)

urlpatterns = [
    # Custom paths must come before router to avoid router matching first
    path("me/", views.MeView.as_view(), name="me"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("search/", views.GlobalSearchView.as_view(), name="global-search"),
    path(
        "relationships/graph/",
        views.RelationshipGraphView.as_view(),
        name="relationship-graph",
    ),
    path("ai/parse-contacts/", views.AIParseContactsView.as_view(), name="ai-parse-contacts"),
    path("ai/bulk-import/", views.AIBulkImportView.as_view(), name="ai-bulk-import"),
    path("ai/parse-updates/", views.AIParseUpdatesView.as_view(), name="ai-parse-updates"),
    path("ai/apply-updates/", views.AIApplyUpdatesView.as_view(), name="ai-apply-updates"),
    path("ai/chat/", views.AIChatView.as_view(), name="ai-chat"),
    path("ai/suggest-relationships/", views.AISuggestRelationshipsView.as_view(), name="ai-suggest-relationships"),
    path("ai/apply-relationship-suggestion/", views.AIApplyRelationshipSuggestionView.as_view(), name="ai-apply-relationship-suggestion"),
    # Router URLs come last
    path("", include(router.urls)),
]
