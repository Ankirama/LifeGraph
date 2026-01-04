from django.apps import AppConfig


class PeopleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.people"
    verbose_name = "People"

    def ready(self):
        # Import signals
        from . import signals  # noqa: F401

        # Register models with auditlog
        from auditlog.registry import auditlog

        from .models import (
            Anecdote,
            CustomFieldDefinition,
            CustomFieldValue,
            Employment,
            Person,
            Photo,
            Relationship,
            RelationshipType,
        )

        # Register models with auditlog, excluding encrypted fields that
        # cause serialization issues with the diff mechanism
        auditlog.register(
            Person,
            exclude_fields=["met_context", "emails", "phones", "addresses", "notes"],
        )
        auditlog.register(
            Relationship,
            exclude_fields=["notes"],
        )
        auditlog.register(RelationshipType)
        auditlog.register(
            Anecdote,
            exclude_fields=["content"],
        )
        auditlog.register(Photo)
        auditlog.register(
            Employment,
            exclude_fields=["description"],
        )
        auditlog.register(CustomFieldDefinition)
        auditlog.register(
            CustomFieldValue,
            exclude_fields=["value"],
        )
