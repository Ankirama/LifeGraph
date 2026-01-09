"""
Management command to create a user for LifeGraph.

Since public registration is disabled, this is the only way to create users.
Supports creating users with optional MFA setup.
"""

import getpass
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()


class Command(BaseCommand):
    help = "Create a new user account (public registration is disabled)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Username (required)",
        )
        parser.add_argument(
            "--email",
            type=str,
            help="User email address (required)",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="User password (will prompt if not provided)",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            default="",
            help="User first name",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            default="",
            help="User last name",
        )
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Create a superuser with admin access",
        )
        parser.add_argument(
            "--staff",
            action="store_true",
            help="Grant staff status (can access admin site)",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for input (requires --username, --email and --password)",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        email = options.get("email")
        password = options.get("password")
        first_name = options.get("first_name", "")
        last_name = options.get("last_name", "")
        is_superuser = options.get("superuser", False)
        is_staff = options.get("staff", False) or is_superuser
        no_input = options.get("no_input", False)

        # Get username
        if not username:
            if no_input:
                raise CommandError("--username is required when using --no-input")
            username = input("Username: ").strip()

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f"User with username '{username}' already exists")

        # Get email
        if not email:
            if no_input:
                raise CommandError("--email is required when using --no-input")
            email = input("Email address: ").strip()

        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            raise CommandError(f"Invalid email address: {email}")

        # Check if user with email already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f"User with email '{email}' already exists")

        # Get password
        if not password:
            if no_input:
                raise CommandError("--password is required when using --no-input")

            password = getpass.getpass("Password: ")
            password_confirm = getpass.getpass("Password (again): ")

            if password != password_confirm:
                raise CommandError("Passwords do not match")

        # Validate password strength
        if len(password) < 8:
            raise CommandError("Password must be at least 8 characters long")

        # Get names if not provided and not --no-input
        if not no_input:
            if not first_name:
                first_name = input("First name (optional): ").strip()
            if not last_name:
                last_name = input("Last name (optional): ").strip()

        # Create user
        try:
            if is_superuser:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                if is_staff:
                    user.is_staff = True
                    user.save()

            self.stdout.write(
                self.style.SUCCESS(f"Successfully created user: {email}")
            )

            if is_superuser:
                self.stdout.write(
                    self.style.SUCCESS("  - Superuser privileges granted")
                )
            elif is_staff:
                self.stdout.write(
                    self.style.SUCCESS("  - Staff privileges granted")
                )

            self.stdout.write("")
            self.stdout.write("Next steps:")
            self.stdout.write("  1. Log in at the application")
            self.stdout.write("  2. Go to Settings/Profile to set up MFA")
            self.stdout.write("  3. Scan the QR code with your authenticator app")
            self.stdout.write("")

        except Exception as e:
            raise CommandError(f"Failed to create user: {e}")
