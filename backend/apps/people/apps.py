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

        auditlog.register(Person)
        auditlog.register(Relationship)
        auditlog.register(RelationshipType)
        auditlog.register(Anecdote)
        auditlog.register(Photo)
        auditlog.register(Employment)
        auditlog.register(CustomFieldDefinition)
        auditlog.register(CustomFieldValue)
