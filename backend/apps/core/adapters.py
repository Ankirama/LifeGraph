"""
Custom allauth adapters for LifeGraph.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponseForbidden


class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    """
    Account adapter that prevents new user registration.

    Users can only be created via the management command:
        python manage.py create_user --email user@example.com --password secret
    """

    def is_open_for_signup(self, request):
        """Disable signup for all users."""
        return False

    def respond_user_inactive(self, request, user):
        """Handle inactive users."""
        raise ImmediateHttpResponse(
            HttpResponseForbidden("This account is inactive.")
        )
