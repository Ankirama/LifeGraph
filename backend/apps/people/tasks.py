"""
Celery tasks for the People app.
"""

import logging
from datetime import date, timedelta

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def regenerate_person_summary(self, person_id: str) -> dict:
    """
    Regenerate AI summary for a specific person.

    Args:
        person_id: UUID of the person to generate summary for

    Returns:
        Dict with status and summary preview
    """
    from .models import Person, Relationship
    from .services import generate_person_summary

    try:
        person = Person.objects.get(id=person_id, is_active=True)
    except Person.DoesNotExist:
        logger.error(f"Person {person_id} not found")
        return {"status": "error", "message": "Person not found"}

    # Get owner for relationship context
    owner = Person.objects.filter(is_owner=True).first()

    # Build person data for summary generation
    profile_data = {
        "full_name": person.full_name,
        "nickname": person.nickname,
        "birthday": person.birthday.isoformat() if person.birthday else None,
        "notes": person.notes,
        "met_date": person.met_date.isoformat() if person.met_date else None,
        "met_context": person.met_context,
    }

    # Get relationship to owner
    if owner:
        rel = Relationship.objects.filter(
            person_a=person, person_b=owner
        ).select_related("relationship_type").first()
        if rel:
            profile_data["relationship_to_owner"] = rel.relationship_type.name

    # Get relationships with other people
    relationships_data = []
    for rel in Relationship.objects.filter(person_a=person).select_related("person_b", "relationship_type")[:10]:
        if rel.person_b != owner:
            relationships_data.append({
                "type": rel.relationship_type.name,
                "person_name": rel.person_b.full_name,
            })

    # Get anecdotes
    anecdotes_data = []
    for anecdote in person.anecdotes.all()[:10]:
        anecdotes_data.append({
            "type": anecdote.anecdote_type,
            "title": anecdote.title,
            "content": anecdote.content,
            "date": anecdote.date.isoformat() if anecdote.date else None,
        })

    # Get employment history
    employments_data = []
    for emp in person.employments.all()[:5]:
        employments_data.append({
            "company": emp.company,
            "title": emp.title,
            "is_current": emp.is_current,
        })

    person_data = {
        "profile": profile_data,
        "relationships": relationships_data,
        "anecdotes": anecdotes_data,
        "employments": employments_data,
    }

    try:
        summary = generate_person_summary(person_data)
        person.ai_summary = summary
        person.save(update_fields=["ai_summary"])

        logger.info(f"Generated summary for {person.full_name}")
        return {
            "status": "success",
            "person_id": str(person.id),
            "person_name": person.full_name,
            "summary_preview": summary[:200] + "..." if len(summary) > 200 else summary,
        }
    except Exception as e:
        logger.error(f"Failed to generate summary for {person.full_name}: {e}")
        self.retry(exc=e)


@shared_task
def regenerate_all_summaries() -> dict:
    """
    Regenerate AI summaries for all active persons.

    Returns:
        Dict with count of processed persons
    """
    from .models import Person

    persons = Person.objects.filter(is_active=True, is_owner=False)
    count = 0

    for person in persons:
        # Queue each person's summary generation as a separate task
        regenerate_person_summary.delay(str(person.id))
        count += 1

    logger.info(f"Queued summary regeneration for {count} persons")
    return {"status": "success", "queued_count": count}


@shared_task
def check_upcoming_birthdays(days_ahead: int = 7) -> dict:
    """
    Check for upcoming birthdays and log them.

    This task can be extended to send notifications.

    Args:
        days_ahead: Number of days to look ahead

    Returns:
        Dict with list of upcoming birthdays
    """
    from .models import Person

    today = date.today()
    upcoming = []

    persons_with_birthday = Person.objects.filter(
        is_active=True,
        is_owner=False,
        birthday__isnull=False
    )

    for person in persons_with_birthday:
        # Calculate this year's birthday
        try:
            birthday_this_year = person.birthday.replace(year=today.year)
        except ValueError:
            # Handle Feb 29 for non-leap years
            birthday_this_year = person.birthday.replace(year=today.year, day=28)

        # If birthday already passed this year, check next year
        if birthday_this_year < today:
            try:
                birthday_this_year = person.birthday.replace(year=today.year + 1)
            except ValueError:
                birthday_this_year = person.birthday.replace(year=today.year + 1, day=28)

        days_until = (birthday_this_year - today).days

        if 0 <= days_until <= days_ahead:
            age = birthday_this_year.year - person.birthday.year
            upcoming.append({
                "person_id": str(person.id),
                "person_name": person.full_name,
                "birthday": person.birthday.isoformat(),
                "days_until": days_until,
                "turning_age": age,
            })

            if days_until == 0:
                logger.info(f"🎂 Today is {person.full_name}'s birthday! They are turning {age}.")
            elif days_until == 1:
                logger.info(f"🎂 Tomorrow is {person.full_name}'s birthday! They will turn {age}.")
            else:
                logger.info(f"🎂 {person.full_name}'s birthday is in {days_until} days (turning {age}).")

    # Sort by days until
    upcoming.sort(key=lambda x: x["days_until"])

    return {
        "status": "success",
        "checked_date": today.isoformat(),
        "days_ahead": days_ahead,
        "upcoming_count": len(upcoming),
        "upcoming_birthdays": upcoming,
    }


@shared_task
def cleanup_old_audit_logs(days_to_keep: int = 90) -> dict:
    """
    Clean up audit log entries older than specified days.

    Args:
        days_to_keep: Number of days of logs to retain

    Returns:
        Dict with count of deleted entries
    """
    from auditlog.models import LogEntry

    cutoff_date = date.today() - timedelta(days=days_to_keep)

    with transaction.atomic():
        deleted_count, _ = LogEntry.objects.filter(
            timestamp__date__lt=cutoff_date
        ).delete()

    logger.info(f"Cleaned up {deleted_count} audit log entries older than {days_to_keep} days")
    return {
        "status": "success",
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
    }


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def sync_linkedin_profile(self, person_id: str) -> dict:
    """
    Sync a single person's LinkedIn profile to update their employment data.

    WARNING: Uses unofficial LinkedIn API. Use sparingly to avoid rate limits.

    Args:
        person_id: UUID of the person to sync

    Returns:
        Dict with sync results
    """
    from .models import Person
    from .services import sync_person_from_linkedin

    try:
        person = Person.objects.get(id=person_id, is_active=True)
    except Person.DoesNotExist:
        logger.error(f"Person {person_id} not found for LinkedIn sync")
        return {"status": "error", "message": "Person not found"}

    if not person.linkedin_url:
        return {"status": "error", "message": "Person has no LinkedIn URL"}

    try:
        result = sync_person_from_linkedin(person)
        logger.info(
            f"LinkedIn sync for {person.full_name}: "
            f"synced {result['synced_count']}, skipped {result['skipped_count']}"
        )
        return {
            "status": "success",
            "person_id": str(person.id),
            "person_name": person.full_name,
            **result,
        }
    except ValueError as e:
        logger.warning(f"LinkedIn sync config error for {person.full_name}: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"LinkedIn sync failed for {person.full_name}: {e}")
        self.retry(exc=e)


@shared_task
def sync_linkedin_profiles(batch_size: int = 10, delay_seconds: int = 30) -> dict:
    """
    Sync LinkedIn profiles for all persons with LinkedIn URLs.

    WARNING: This queues individual sync tasks with delays to avoid rate limiting.
    LinkedIn may block accounts that make too many requests.

    Args:
        batch_size: Maximum number of profiles to sync in this run
        delay_seconds: Delay between each profile sync (to avoid rate limits)

    Returns:
        Dict with sync status
    """
    from .models import Person

    # Get persons with LinkedIn URLs that haven't been synced recently
    persons = Person.objects.filter(
        is_active=True,
        linkedin_url__isnull=False,
    ).exclude(linkedin_url="").order_by("?")[:batch_size]

    queued_count = 0
    for i, person in enumerate(persons):
        # Queue each sync with a delay to avoid rate limiting
        countdown = i * delay_seconds
        sync_linkedin_profile.apply_async(
            args=[str(person.id)],
            countdown=countdown,
        )
        queued_count += 1
        logger.info(f"Queued LinkedIn sync for {person.full_name} (in {countdown}s)")

    logger.info(f"LinkedIn sync: Queued {queued_count} profiles with {delay_seconds}s delays")

    return {
        "status": "success",
        "queued_count": queued_count,
        "delay_between": delay_seconds,
        "estimated_completion_seconds": queued_count * delay_seconds,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def suggest_tags_for_person_task(self, person_id: str) -> dict:
    """
    Generate tag suggestions for a specific person.

    Args:
        person_id: UUID of the person to suggest tags for

    Returns:
        Dict with suggested tags
    """
    from apps.core.models import Tag
    from .models import Person, Relationship
    from .services import suggest_tags_for_person

    try:
        person = Person.objects.get(id=person_id, is_active=True)
    except Person.DoesNotExist:
        logger.error(f"Person {person_id} not found")
        return {"status": "error", "message": "Person not found"}

    # Get owner for relationship context
    owner = Person.objects.filter(is_owner=True).first()

    # Build person data
    profile_data = {
        "full_name": person.full_name,
        "nickname": person.nickname,
        "birthday": person.birthday.isoformat() if person.birthday else None,
        "notes": person.notes,
        "met_date": person.met_date.isoformat() if person.met_date else None,
        "met_context": person.met_context,
    }

    # Get relationship to owner
    if owner:
        rel = Relationship.objects.filter(
            person_a=person, person_b=owner
        ).select_related("relationship_type").first()
        if rel:
            profile_data["relationship_to_owner"] = rel.relationship_type.name

    # Get relationships with other people
    relationships_data = []
    for rel in Relationship.objects.filter(person_a=person).select_related("person_b", "relationship_type")[:10]:
        if rel.person_b != owner:
            relationships_data.append({
                "type": rel.relationship_type.name,
                "person_name": rel.person_b.full_name,
            })

    # Get anecdotes
    anecdotes_data = []
    for anecdote in person.anecdotes.all()[:10]:
        anecdotes_data.append({
            "type": anecdote.anecdote_type,
            "title": anecdote.title,
            "content": anecdote.content,
            "date": anecdote.date.isoformat() if anecdote.date else None,
        })

    # Get employment history
    employments_data = []
    for emp in person.employments.all()[:5]:
        employments_data.append({
            "company": emp.company,
            "title": emp.title,
            "is_current": emp.is_current,
        })

    person_data = {
        "profile": profile_data,
        "relationships": relationships_data,
        "anecdotes": anecdotes_data,
        "employments": employments_data,
    }

    # Get existing tags
    existing_tags = list(Tag.objects.values_list("name", flat=True))

    try:
        suggested_tags = suggest_tags_for_person(person_data, existing_tags)
        logger.info(f"Generated {len(suggested_tags)} tag suggestions for {person.full_name}")
        return {
            "status": "success",
            "person_id": str(person.id),
            "person_name": person.full_name,
            "suggested_tags": suggested_tags,
        }
    except Exception as e:
        logger.error(f"Failed to suggest tags for {person.full_name}: {e}")
        self.retry(exc=e)


@shared_task
def batch_suggest_tags(apply_high_confidence: bool = False, confidence_threshold: float = 0.8) -> dict:
    """
    Batch suggest tags for all active persons without tags.

    Args:
        apply_high_confidence: If True, automatically apply tags with confidence >= threshold
        confidence_threshold: Minimum confidence to auto-apply (default 0.8)

    Returns:
        Dict with count of processed persons
    """
    from apps.core.models import Tag
    from .models import Person

    # Find persons without any tags
    persons_without_tags = Person.objects.filter(
        is_active=True,
        is_owner=False,
        tags__isnull=True
    ).distinct()

    count = 0
    auto_applied = 0

    for person in persons_without_tags:
        # Queue tag suggestion for each person
        result = suggest_tags_for_person_task.delay(str(person.id))

        if apply_high_confidence:
            # Wait for result and apply high-confidence tags
            try:
                task_result = result.get(timeout=60)
                if task_result.get("status") == "success":
                    high_confidence_tags = [
                        t["name"] for t in task_result.get("suggested_tags", [])
                        if t["confidence"] >= confidence_threshold
                    ]
                    for tag_name in high_confidence_tags:
                        tag, created = Tag.objects.get_or_create(
                            name=tag_name.lower(),
                            defaults={"description": "Auto-generated by AI"}
                        )
                        person.tags.add(tag)
                        auto_applied += 1
            except Exception as e:
                logger.warning(f"Could not auto-apply tags for {person.full_name}: {e}")

        count += 1

    logger.info(f"Queued tag suggestion for {count} persons, auto-applied {auto_applied} tags")
    return {
        "status": "success",
        "queued_count": count,
        "auto_applied_count": auto_applied if apply_high_confidence else 0,
    }
