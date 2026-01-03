"""
Rate limiting utilities for LifeGraph API.

Provides configurable rate limiting decorators for different endpoint types.
Uses django-ratelimit under the hood with Redis backend.
"""

from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit


def get_client_ip(request):
    """
    Extract client IP address from request, handling reverse proxies.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def ratelimit_key(group, request):
    """
    Generate rate limit key based on user or IP.
    Authenticated users get per-user limits, anonymous gets per-IP.
    """
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    return f"ip:{get_client_ip(request)}"


def api_ratelimit(rate=None, key=None, block=True):
    """
    Rate limit decorator for standard API endpoints.

    Args:
        rate: Rate limit string (e.g., "100/m"). Defaults to RATELIMIT_API_DEFAULT.
        key: Custom key function. Defaults to user/IP-based key.
        block: If True, block requests exceeding limit. If False, just flag them.
    """
    if rate is None:
        rate = getattr(settings, "RATELIMIT_API_DEFAULT", "100/m")

    if not getattr(settings, "RATELIMIT_ENABLE", True):
        # Rate limiting disabled - return passthrough decorator
        def passthrough(func):
            return func
        return passthrough

    return ratelimit(key=key or ratelimit_key, rate=rate, block=block)


def ai_ratelimit(rate=None, key=None, block=True):
    """
    Rate limit decorator for AI endpoints (more restrictive).
    AI endpoints are expensive, so we limit them more aggressively.

    Args:
        rate: Rate limit string. Defaults to RATELIMIT_API_AI.
        key: Custom key function.
        block: If True, block requests exceeding limit.
    """
    if rate is None:
        rate = getattr(settings, "RATELIMIT_API_AI", "10/m")

    if not getattr(settings, "RATELIMIT_ENABLE", True):
        def passthrough(func):
            return func
        return passthrough

    return ratelimit(key=key or ratelimit_key, rate=rate, block=block)


def upload_ratelimit(rate=None, key=None, block=True):
    """
    Rate limit decorator for upload endpoints.

    Args:
        rate: Rate limit string. Defaults to RATELIMIT_API_UPLOAD.
        key: Custom key function.
        block: If True, block requests exceeding limit.
    """
    if rate is None:
        rate = getattr(settings, "RATELIMIT_API_UPLOAD", "20/m")

    if not getattr(settings, "RATELIMIT_ENABLE", True):
        def passthrough(func):
            return func
        return passthrough

    return ratelimit(key=key or ratelimit_key, rate=rate, block=block)


def login_ratelimit(rate=None, key=None, block=True):
    """
    Rate limit decorator for login/auth endpoints.
    Per-IP limiting to prevent brute force attacks.

    Args:
        rate: Rate limit string. Defaults to RATELIMIT_LOGIN.
        key: Custom key function. Defaults to IP-based key.
        block: If True, block requests exceeding limit.
    """
    if rate is None:
        rate = getattr(settings, "RATELIMIT_LOGIN", "5/m")

    if not getattr(settings, "RATELIMIT_ENABLE", True):
        def passthrough(func):
            return func
        return passthrough

    # Always use IP for login attempts
    def ip_key(group, request):
        return f"login_ip:{get_client_ip(request)}"

    return ratelimit(key=key or ip_key, rate=rate, block=block)


class RateLimitMixin:
    """
    Mixin for ViewSets to add rate limiting to actions.

    Add to your ViewSet and configure limits:

        class MyViewSet(RateLimitMixin, viewsets.ModelViewSet):
            ratelimit_config = {
                'list': '100/m',
                'create': '20/m',
                'custom_action': '5/m',
            }
    """

    ratelimit_config = {}

    def dispatch(self, request, *args, **kwargs):
        """Check rate limits before dispatching."""
        if not getattr(settings, "RATELIMIT_ENABLE", True):
            return super().dispatch(request, *args, **kwargs)

        action = getattr(self, "action", None)
        if action and action in self.ratelimit_config:
            # Apply rate limit check manually
            from django_ratelimit.core import is_ratelimited

            rate = self.ratelimit_config[action]
            key = ratelimit_key(f"viewset:{self.__class__.__name__}:{action}", request)

            ratelimited = is_ratelimited(
                request=request,
                group=f"{self.__class__.__name__}:{action}",
                key=lambda g, r: key,
                rate=rate,
                increment=True,
            )

            if ratelimited:
                return JsonResponse(
                    {
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded for {action}. Please try again later.",
                        "action": action,
                    },
                    status=429,
                )

        return super().dispatch(request, *args, **kwargs)
