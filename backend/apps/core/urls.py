"""
Core app URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"tags", views.TagViewSet)
router.register(r"groups", views.GroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("search/", views.GlobalSearchView.as_view(), name="global-search"),
    path("health/", views.HealthCheckView.as_view(), name="health-check"),
]
