"""
Management command to generate a Fernet encryption key.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a new Fernet encryption key for field-level encryption"

    def add_arguments(self, parser):
        parser.add_argument(
            "--validate",
            action="store_true",
            help="Validate current encryption configuration",
        )

    def handle(self, *args, **options):
        if options["validate"]:
            self._validate()
        else:
            self._generate()

    def _generate(self):
        """Generate a new Fernet key."""
        from cryptography.fernet import Fernet

        key = Fernet.generate_key().decode()

        self.stdout.write(self.style.SUCCESS("\n🔐 New Fernet Encryption Key:\n"))
        self.stdout.write(f"   {key}\n")
        self.stdout.write(
            self.style.WARNING(
                "\n⚠️  IMPORTANT:\n"
                "   1. Add this to your .env file as: FERNET_KEYS=" + key + "\n"
                "   2. BACK UP THIS KEY! Data cannot be recovered without it.\n"
                "   3. For key rotation, add new key before old key: NEW_KEY,OLD_KEY\n"
            )
        )

    def _validate(self):
        """Validate current encryption configuration."""
        from apps.core.encryption import validate_encryption_config

        is_valid, message = validate_encryption_config()

        if is_valid:
            self.stdout.write(self.style.SUCCESS(f"✅ {message}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ {message}"))
            self.stdout.write(
                self.style.WARNING(
                    "\nGenerate a key with: python manage.py generate_encryption_key"
                )
            )
