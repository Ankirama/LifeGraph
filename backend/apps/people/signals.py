"""
Signals for auto-creating inverse relationships.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import Relationship, RelationshipType


@receiver(post_save, sender=Relationship)
def create_inverse_relationship(sender, instance, created, **kwargs):
    """
    Auto-create inverse relationship when a new relationship is created.
    """
    if not created or instance.auto_created:
        return

    relationship_type = instance.relationship_type
    if not relationship_type.auto_create_inverse:
        return

    # Find or determine the inverse relationship type
    if relationship_type.is_symmetric:
        inverse_type = relationship_type
    else:
        # Look for a relationship type with matching inverse name
        inverse_type = RelationshipType.objects.filter(
            name=relationship_type.inverse_name
        ).first()
        if not inverse_type:
            # If no inverse type exists, don't create inverse relationship
            return

    # Check if inverse already exists
    inverse_exists = Relationship.objects.filter(
        person_a=instance.person_b,
        person_b=instance.person_a,
        relationship_type=inverse_type,
    ).exists()

    if not inverse_exists:
        Relationship.objects.create(
            person_a=instance.person_b,
            person_b=instance.person_a,
            relationship_type=inverse_type,
            started_date=instance.started_date,
            notes=instance.notes,
            strength=instance.strength,
            auto_created=True,
        )


@receiver(pre_delete, sender=Relationship)
def delete_inverse_relationship(sender, instance, **kwargs):
    """
    Delete the inverse relationship when a relationship is deleted.
    """
    relationship_type = instance.relationship_type

    if relationship_type.is_symmetric:
        inverse_type = relationship_type
    else:
        inverse_type = RelationshipType.objects.filter(
            name=relationship_type.inverse_name
        ).first()
        if not inverse_type:
            return

    # Delete the inverse
    Relationship.objects.filter(
        person_a=instance.person_b,
        person_b=instance.person_a,
        relationship_type=inverse_type,
    ).delete()
