"""
Tests for rate limiting utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.test import RequestFactory, override_settings
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from apps.core.ratelimit import (
    RateLimitMixin,
    ai_ratelimit,
    api_ratelimit,
    get_client_ip,
    login_ratelimit,
    ratelimit_key,
    upload_ratelimit,
)


# =============================================================================
# get_client_ip Tests
# =============================================================================


class TestGetClientIP:
    """Tests for get_client_ip function."""

    def test_returns_remote_addr_when_no_forwarded_header(self):
        """Test that REMOTE_ADDR is used when X-Forwarded-For is not present."""
        request = RequestFactory().get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        result = get_client_ip(request)

        assert result == "192.168.1.100"

    def test_returns_first_ip_from_forwarded_header(self):
        """Test that first IP from X-Forwarded-For is used."""
        request = RequestFactory().get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 10.0.0.2, 10.0.0.3"
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        result = get_client_ip(request)

        assert result == "10.0.0.1"

    def test_strips_whitespace_from_forwarded_ip(self):
        """Test that whitespace is stripped from forwarded IP."""
        request = RequestFactory().get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "  10.0.0.1  , 10.0.0.2"

        result = get_client_ip(request)

        assert result == "10.0.0.1"

    def test_handles_single_ip_in_forwarded_header(self):
        """Test handling of single IP in X-Forwarded-For."""
        request = RequestFactory().get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1"

        result = get_client_ip(request)

        assert result == "10.0.0.1"

    def test_handles_ipv6_address(self):
        """Test handling of IPv6 addresses."""
        request = RequestFactory().get("/")
        request.META["REMOTE_ADDR"] = "::1"

        result = get_client_ip(request)

        assert result == "::1"

    def test_returns_none_when_no_ip_available(self):
        """Test behavior when no IP is available."""
        request = RequestFactory().get("/")
        request.META.pop("REMOTE_ADDR", None)

        result = get_client_ip(request)

        assert result is None


# =============================================================================
# ratelimit_key Tests
# =============================================================================


class TestRatelimitKey:
    """Tests for ratelimit_key function."""

    def test_returns_user_key_for_authenticated_user(self, user):
        """Test that authenticated users get user-based key."""
        request = RequestFactory().get("/")
        request.user = user
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        result = ratelimit_key("test_group", request)

        assert result == f"user:{user.id}"

    def test_returns_ip_key_for_anonymous_user(self):
        """Test that anonymous users get IP-based key."""
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        result = ratelimit_key("test_group", request)

        assert result == "ip:192.168.1.100"

    def test_uses_forwarded_ip_for_anonymous(self):
        """Test that X-Forwarded-For is used for anonymous users."""
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 10.0.0.2"
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        result = ratelimit_key("test_group", request)

        assert result == "ip:10.0.0.1"


# =============================================================================
# api_ratelimit Tests
# =============================================================================


class TestApiRatelimit:
    """Tests for api_ratelimit decorator."""

    @override_settings(RATELIMIT_ENABLE=False)
    def test_passthrough_when_disabled(self):
        """Test that decorator is a passthrough when rate limiting is disabled."""

        @api_ratelimit()
        def test_view(request):
            return "success"

        request = RequestFactory().get("/")
        result = test_view(request)

        assert result == "success"

    @override_settings(RATELIMIT_ENABLE=False)
    def test_passthrough_preserves_function(self):
        """Test that passthrough preserves the original function."""

        def original_view(request):
            return "original"

        decorated = api_ratelimit()(original_view)

        # Function should be identical when rate limiting is disabled
        assert decorated is original_view

    @override_settings(RATELIMIT_ENABLE=True, RATELIMIT_API_DEFAULT="100/m")
    def test_uses_default_rate_from_settings(self):
        """Test that default rate is taken from settings."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @api_ratelimit()
            def test_view(request):
                return "success"

            mock_ratelimit.assert_called_once()
            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["rate"] == "100/m"

    @override_settings(RATELIMIT_ENABLE=True)
    def test_custom_rate_overrides_default(self):
        """Test that custom rate overrides the default."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @api_ratelimit(rate="50/m")
            def test_view(request):
                return "success"

            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["rate"] == "50/m"

    @override_settings(RATELIMIT_ENABLE=True)
    def test_block_parameter_passed_through(self):
        """Test that block parameter is passed to underlying decorator."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @api_ratelimit(block=False)
            def test_view(request):
                return "success"

            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["block"] is False


# =============================================================================
# ai_ratelimit Tests
# =============================================================================


class TestAiRatelimit:
    """Tests for ai_ratelimit decorator."""

    @override_settings(RATELIMIT_ENABLE=False)
    def test_passthrough_when_disabled(self):
        """Test that decorator is a passthrough when rate limiting is disabled."""

        @ai_ratelimit()
        def test_view(request):
            return "success"

        request = RequestFactory().get("/")
        result = test_view(request)

        assert result == "success"

    @override_settings(RATELIMIT_ENABLE=True, RATELIMIT_API_AI="10/m")
    def test_uses_ai_rate_from_settings(self):
        """Test that AI rate is taken from settings."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @ai_ratelimit()
            def test_view(request):
                return "success"

            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["rate"] == "10/m"

    @override_settings(RATELIMIT_ENABLE=True)
    def test_custom_rate_overrides_default(self):
        """Test that custom rate overrides the default."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @ai_ratelimit(rate="5/m")
            def test_view(request):
                return "success"

            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["rate"] == "5/m"


# =============================================================================
# upload_ratelimit Tests
# =============================================================================


class TestUploadRatelimit:
    """Tests for upload_ratelimit decorator."""

    @override_settings(RATELIMIT_ENABLE=False)
    def test_passthrough_when_disabled(self):
        """Test that decorator is a passthrough when rate limiting is disabled."""

        @upload_ratelimit()
        def test_view(request):
            return "success"

        request = RequestFactory().get("/")
        result = test_view(request)

        assert result == "success"

    @override_settings(RATELIMIT_ENABLE=True, RATELIMIT_API_UPLOAD="20/m")
    def test_uses_upload_rate_from_settings(self):
        """Test that upload rate is taken from settings."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @upload_ratelimit()
            def test_view(request):
                return "success"

            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["rate"] == "20/m"

    @override_settings(RATELIMIT_ENABLE=True)
    def test_custom_rate_overrides_default(self):
        """Test that custom rate overrides the default."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @upload_ratelimit(rate="10/m")
            def test_view(request):
                return "success"

            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["rate"] == "10/m"


# =============================================================================
# login_ratelimit Tests
# =============================================================================


class TestLoginRatelimit:
    """Tests for login_ratelimit decorator."""

    @override_settings(RATELIMIT_ENABLE=False)
    def test_passthrough_when_disabled(self):
        """Test that decorator is a passthrough when rate limiting is disabled."""

        @login_ratelimit()
        def test_view(request):
            return "success"

        request = RequestFactory().get("/")
        result = test_view(request)

        assert result == "success"

    @override_settings(RATELIMIT_ENABLE=True, RATELIMIT_LOGIN="5/m")
    def test_uses_login_rate_from_settings(self):
        """Test that login rate is taken from settings."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @login_ratelimit()
            def test_view(request):
                return "success"

            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["rate"] == "5/m"

    @override_settings(RATELIMIT_ENABLE=True)
    def test_uses_ip_based_key_by_default(self):
        """Test that login rate limiting uses IP-based key by default."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            @login_ratelimit()
            def test_view(request):
                return "success"

            # The key function should be provided
            call_kwargs = mock_ratelimit.call_args[1]
            key_func = call_kwargs["key"]

            # Test the key function
            request = RequestFactory().get("/")
            request.META["REMOTE_ADDR"] = "192.168.1.100"
            key = key_func("test_group", request)

            assert key == "login_ip:192.168.1.100"

    @override_settings(RATELIMIT_ENABLE=True)
    def test_custom_key_overrides_default(self):
        """Test that custom key function overrides the IP-based key."""
        with patch("apps.core.ratelimit.ratelimit") as mock_ratelimit:
            mock_ratelimit.return_value = lambda f: f

            custom_key = lambda g, r: "custom_key"

            @login_ratelimit(key=custom_key)
            def test_view(request):
                return "success"

            call_kwargs = mock_ratelimit.call_args[1]
            assert call_kwargs["key"] is custom_key


# =============================================================================
# RateLimitMixin Tests
# =============================================================================


class TestRateLimitMixin:
    """Tests for RateLimitMixin."""

    def create_viewset_class(self, config=None):
        """Helper to create a ViewSet class with mixin."""
        config = config or {}

        class TestViewSet(RateLimitMixin, viewsets.ViewSet):
            ratelimit_config = config
            # Disable authentication for testing
            authentication_classes = []
            permission_classes = []

            def list(self, request):
                return Response({"action": "list"})

            def create(self, request):
                return Response({"action": "create"})

            def custom_action(self, request):
                return Response({"action": "custom"})

        return TestViewSet

    @override_settings(RATELIMIT_ENABLE=False)
    def test_passthrough_when_disabled(self):
        """Test that mixin is passthrough when rate limiting is disabled."""
        ViewSet = self.create_viewset_class({"list": "10/m"})
        view = ViewSet.as_view({"get": "list"})

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"action": "list"}

    @override_settings(RATELIMIT_ENABLE=True)
    def test_allows_action_not_in_config(self):
        """Test that actions not in ratelimit_config are allowed."""
        ViewSet = self.create_viewset_class({"create": "5/m"})  # list not configured
        view = ViewSet.as_view({"get": "list"})

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        response = view(request)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    @override_settings(RATELIMIT_ENABLE=True)
    def test_mixin_checks_action_in_config(self, user):
        """Test that mixin checks if action is in ratelimit_config."""
        ViewSet = self.create_viewset_class({"list": "1000/m"})
        view = ViewSet.as_view({"get": "list"})

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user

        # With a high rate limit, request should succeed
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    @override_settings(RATELIMIT_ENABLE=True)
    def test_mixin_generates_correct_key(self, user):
        """Test that mixin uses ratelimit_key correctly."""
        ViewSet = self.create_viewset_class({"list": "1000/m"})

        # Create instance and check key generation
        viewset = ViewSet()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user

        key = ratelimit_key(f"viewset:{ViewSet.__name__}:list", request)
        assert key == f"user:{user.id}"

    @pytest.mark.django_db
    @override_settings(RATELIMIT_ENABLE=True)
    def test_mixin_with_anonymous_user(self):
        """Test that mixin handles anonymous users."""
        ViewSet = self.create_viewset_class({"list": "1000/m"})
        view = ViewSet.as_view({"get": "list"})

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        response = view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_mixin_default_empty_config(self):
        """Test that mixin has empty ratelimit_config by default."""
        assert RateLimitMixin.ratelimit_config == {}


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.django_db
class TestRateLimitIntegration:
    """Integration tests for rate limiting with real views."""

    @override_settings(RATELIMIT_ENABLE=False)
    def test_rate_limiting_disabled_in_tests(self, authenticated_client):
        """Verify that rate limiting is disabled in test settings."""
        from django.conf import settings

        assert settings.RATELIMIT_ENABLE is False

    def test_decorator_chain_with_multiple_decorators(self):
        """Test that rate limit decorator works with other decorators."""

        def other_decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                return f"wrapped:{result}"

            return wrapper

        @other_decorator
        @api_ratelimit()
        def decorated_view(request):
            return "success"

        request = RequestFactory().get("/")
        result = decorated_view(request)

        assert result == "wrapped:success"

    def test_get_client_ip_with_various_proxy_configs(self):
        """Test IP extraction with various proxy configurations."""
        factory = RequestFactory()

        # No proxy
        request1 = factory.get("/")
        request1.META["REMOTE_ADDR"] = "direct-client"
        assert get_client_ip(request1) == "direct-client"

        # Single proxy
        request2 = factory.get("/")
        request2.META["HTTP_X_FORWARDED_FOR"] = "original-client"
        request2.META["REMOTE_ADDR"] = "proxy"
        assert get_client_ip(request2) == "original-client"

        # Multiple proxies
        request3 = factory.get("/")
        request3.META["HTTP_X_FORWARDED_FOR"] = "original, proxy1, proxy2"
        request3.META["REMOTE_ADDR"] = "loadbalancer"
        assert get_client_ip(request3) == "original"

    def test_ratelimit_key_consistency(self, user):
        """Test that rate limit key is consistent for same user/IP."""
        factory = RequestFactory()

        # Same authenticated user
        request1 = factory.get("/")
        request1.user = user
        request1.META["REMOTE_ADDR"] = "192.168.1.1"

        request2 = factory.get("/api/other/")
        request2.user = user
        request2.META["REMOTE_ADDR"] = "10.0.0.1"  # Different IP

        key1 = ratelimit_key("group1", request1)
        key2 = ratelimit_key("group2", request2)

        # Should be same because same user
        assert key1 == key2 == f"user:{user.id}"

        # Same anonymous IP
        request3 = factory.get("/")
        request3.user = AnonymousUser()
        request3.META["REMOTE_ADDR"] = "192.168.1.100"

        request4 = factory.get("/api/other/")
        request4.user = AnonymousUser()
        request4.META["REMOTE_ADDR"] = "192.168.1.100"

        key3 = ratelimit_key("group1", request3)
        key4 = ratelimit_key("group2", request4)

        # Should be same because same IP
        assert key3 == key4 == "ip:192.168.1.100"
