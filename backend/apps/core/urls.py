"""
Core app URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .mfa import (
    MFAConfirmView,
    MFADisableView,
    MFASetupView,
    MFAStatusView,
    MFAVerifyView,
)

router = DefaultRouter()
router.register(r"tags", views.TagViewSet)
router.register(r"groups", views.GroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("search/", views.GlobalSearchView.as_view(), name="global-search"),
    path("health/", views.HealthCheckView.as_view(), name="health-check"),
    # MFA endpoints
    path("auth/mfa/status/", MFAStatusView.as_view(), name="mfa-status"),
    path("auth/mfa/setup/", MFASetupView.as_view(), name="mfa-setup"),
    path("auth/mfa/confirm/", MFAConfirmView.as_view(), name="mfa-confirm"),
    path("auth/mfa/verify/", MFAVerifyView.as_view(), name="mfa-verify"),
    path("auth/mfa/disable/", MFADisableView.as_view(), name="mfa-disable"),
    # Auth status endpoint
    path("auth/status/", views.AuthStatusView.as_view(), name="auth-status"),
]
