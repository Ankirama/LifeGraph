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

urlpatterns = [
    path("", include(router.urls)),
]
