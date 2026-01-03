"""
Management command to set up periodic Celery tasks.
"""

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Set up default periodic Celery tasks"

    def handle(self, *args, **options):
        self.stdout.write("Setting up periodic tasks...")

        # Create schedules
        daily_morning, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="8",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )

        weekly_sunday, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="3",
            day_of_week="0",  # Sunday
            day_of_month="*",
            month_of_year="*",
        )

        monthly_first, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="2",
            day_of_week="*",
            day_of_month="1",
            month_of_year="*",
        )

        # Daily birthday check at 8 AM
        task, created = PeriodicTask.objects.update_or_create(
            name="Check upcoming birthdays",
            defaults={
                "crontab": daily_morning,
                "task": "apps.people.tasks.check_upcoming_birthdays",
                "kwargs": '{"days_ahead": 7}',
                "enabled": True,
            },
        )
        status = "Created" if created else "Updated"
        self.stdout.write(f"  {status}: Check upcoming birthdays (daily at 8 AM)")

        # Weekly LinkedIn sync (placeholder) on Sunday at 3 AM
        task, created = PeriodicTask.objects.update_or_create(
            name="Sync LinkedIn profiles",
            defaults={
                "crontab": weekly_sunday,
                "task": "apps.people.tasks.sync_linkedin_profiles",
                "enabled": False,  # Disabled until LinkedIn integration is ready
            },
        )
        status = "Created" if created else "Updated"
        self.stdout.write(f"  {status}: Sync LinkedIn profiles (weekly, disabled)")

        # Monthly audit log cleanup on 1st at 2 AM
        task, created = PeriodicTask.objects.update_or_create(
            name="Cleanup old audit logs",
            defaults={
                "crontab": monthly_first,
                "task": "apps.people.tasks.cleanup_old_audit_logs",
                "kwargs": '{"days_to_keep": 90}',
                "enabled": True,
            },
        )
        status = "Created" if created else "Updated"
        self.stdout.write(f"  {status}: Cleanup old audit logs (monthly)")

        self.stdout.write(self.style.SUCCESS("Periodic tasks set up successfully!"))
        self.stdout.write("\nTo view/manage tasks, use Django admin or run:")
        self.stdout.write("  python manage.py shell")
        self.stdout.write("  >>> from django_celery_beat.models import PeriodicTask")
        self.stdout.write("  >>> PeriodicTask.objects.all()")
