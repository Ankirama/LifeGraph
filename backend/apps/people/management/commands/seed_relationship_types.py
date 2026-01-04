"""
Management command to seed default relationship types.
"""

from django.core.management.base import BaseCommand

from apps.people.models import RelationshipType


class Command(BaseCommand):
    help = "Seed default relationship types"

    DEFAULT_TYPES = [
        # Family - Symmetric
        {"name": "spouse", "inverse_name": "spouse", "category": "family", "is_symmetric": True},
        {"name": "husband", "inverse_name": "wife", "category": "family", "is_symmetric": False},
        {"name": "wife", "inverse_name": "husband", "category": "family", "is_symmetric": False},
        {"name": "partner", "inverse_name": "partner", "category": "family", "is_symmetric": True},
        {"name": "sibling", "inverse_name": "sibling", "category": "family", "is_symmetric": True},
        {"name": "brother", "inverse_name": "sibling", "category": "family", "is_symmetric": False},
        {"name": "sister", "inverse_name": "sibling", "category": "family", "is_symmetric": False},
        {"name": "cousin", "inverse_name": "cousin", "category": "family", "is_symmetric": True},
        {"name": "in-law", "inverse_name": "in-law", "category": "family", "is_symmetric": True},
        # Family - Asymmetric (generic)
        {"name": "parent", "inverse_name": "child", "category": "family", "is_symmetric": False},
        {"name": "child", "inverse_name": "parent", "category": "family", "is_symmetric": False},
        # Family - Asymmetric (specific)
        {"name": "mother", "inverse_name": "child", "category": "family", "is_symmetric": False},
        {"name": "father", "inverse_name": "child", "category": "family", "is_symmetric": False},
        {"name": "son", "inverse_name": "parent", "category": "family", "is_symmetric": False},
        {"name": "daughter", "inverse_name": "parent", "category": "family", "is_symmetric": False},
        # Grandparents
        {"name": "grandparent", "inverse_name": "grandchild", "category": "family", "is_symmetric": False},
        {"name": "grandchild", "inverse_name": "grandparent", "category": "family", "is_symmetric": False},
        {"name": "grandmother", "inverse_name": "grandchild", "category": "family", "is_symmetric": False},
        {"name": "grandfather", "inverse_name": "grandchild", "category": "family", "is_symmetric": False},
        {"name": "grandson", "inverse_name": "grandparent", "category": "family", "is_symmetric": False},
        {"name": "granddaughter", "inverse_name": "grandparent", "category": "family", "is_symmetric": False},
        # Aunts/Uncles/Nieces/Nephews
        {"name": "uncle", "inverse_name": "nephew/niece", "category": "family", "is_symmetric": False},
        {"name": "aunt", "inverse_name": "nephew/niece", "category": "family", "is_symmetric": False},
        {"name": "nephew", "inverse_name": "uncle/aunt", "category": "family", "is_symmetric": False},
        {"name": "niece", "inverse_name": "uncle/aunt", "category": "family", "is_symmetric": False},
        {"name": "uncle/aunt", "inverse_name": "nephew/niece", "category": "family", "is_symmetric": False},
        {"name": "nephew/niece", "inverse_name": "uncle/aunt", "category": "family", "is_symmetric": False},
        # Social - Symmetric
        {"name": "friend", "inverse_name": "friend", "category": "social", "is_symmetric": True},
        {"name": "close friend", "inverse_name": "close friend", "category": "social", "is_symmetric": True},
        {"name": "acquaintance", "inverse_name": "acquaintance", "category": "social", "is_symmetric": True},
        {"name": "neighbor", "inverse_name": "neighbor", "category": "social", "is_symmetric": True},
        # Professional - Symmetric
        {"name": "colleague", "inverse_name": "colleague", "category": "professional", "is_symmetric": True},
        # Professional - Asymmetric
        {"name": "manager", "inverse_name": "report", "category": "professional", "is_symmetric": False},
        {"name": "report", "inverse_name": "manager", "category": "professional", "is_symmetric": False},
        {"name": "mentor", "inverse_name": "mentee", "category": "professional", "is_symmetric": False},
        {"name": "mentee", "inverse_name": "mentor", "category": "professional", "is_symmetric": False},
        {"name": "client", "inverse_name": "provider", "category": "professional", "is_symmetric": False},
        {"name": "provider", "inverse_name": "client", "category": "professional", "is_symmetric": False},
    ]

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for type_data in self.DEFAULT_TYPES:
            obj, created = RelationshipType.objects.update_or_create(
                name=type_data["name"],
                defaults={
                    "inverse_name": type_data["inverse_name"],
                    "category": type_data["category"],
                    "is_symmetric": type_data["is_symmetric"],
                    "auto_create_inverse": True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created: {type_data['name']}")
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {created_count}, updated {updated_count} relationship types."
            )
        )
