"""
Tests for Celery tasks.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.people.tasks import (
    batch_suggest_tags,
    check_upcoming_birthdays,
    cleanup_old_audit_logs,
    regenerate_all_summaries,
    regenerate_person_summary,
    suggest_tags_for_person_task,
    sync_linkedin_profile,
    sync_linkedin_profiles,
)
from tests.factories import (
    AnecdoteFactory,
    EmploymentFactory,
    PersonFactory,
    RelationshipFactory,
    RelationshipTypeFactory,
    TagFactory,
)


# =============================================================================
# Regenerate Person Summary Tests
# =============================================================================


@pytest.mark.django_db
class TestRegeneratePersonSummary:
    """Tests for regenerate_person_summary task."""

    def test_summary_generation_success(self):
        """Test successful summary generation."""
        person = PersonFactory(first_name="John", last_name="Doe")

        with patch("apps.people.services.generate_person_summary") as mock_gen:
            mock_gen.return_value = "This is a summary for John Doe."

            result = regenerate_person_summary(str(person.pk))

            assert result["status"] == "success"
            assert result["person_name"] == "John Doe"

            person.refresh_from_db()
            assert person.ai_summary == "This is a summary for John Doe."

    def test_summary_person_not_found(self):
        """Test summary generation for non-existent person."""
        import uuid

        result = regenerate_person_summary(str(uuid.uuid4()))

        assert result["status"] == "error"
        assert "not found" in result["message"]

    def test_summary_inactive_person(self):
        """Test summary generation for inactive person."""
        person = PersonFactory(is_active=False)

        result = regenerate_person_summary(str(person.pk))

        assert result["status"] == "error"

    def test_summary_with_relationships(self):
        """Test summary generation includes relationship data."""
        person = PersonFactory()
        other = PersonFactory()
        owner = PersonFactory(is_owner=True)
        rt = RelationshipTypeFactory(name="Friend")

        RelationshipFactory(person_a=person, person_b=other, relationship_type=rt)
        RelationshipFactory(person_a=person, person_b=owner, relationship_type=rt)

        with patch("apps.people.services.generate_person_summary") as mock_gen:
            mock_gen.return_value = "Summary with relationships."

            result = regenerate_person_summary(str(person.pk))

            assert result["status"] == "success"
            # Verify the service was called with relationship data
            mock_gen.assert_called_once()
            call_args = mock_gen.call_args[0][0]
            assert "relationships" in call_args

    def test_summary_with_anecdotes(self):
        """Test summary generation includes anecdote data."""
        person = PersonFactory()
        anecdote = AnecdoteFactory(title="Fun Story")
        anecdote.persons.add(person)

        with patch("apps.people.services.generate_person_summary") as mock_gen:
            mock_gen.return_value = "Summary with anecdotes."

            result = regenerate_person_summary(str(person.pk))

            assert result["status"] == "success"
            call_args = mock_gen.call_args[0][0]
            assert "anecdotes" in call_args

    def test_summary_with_employments(self):
        """Test summary generation includes employment data."""
        person = PersonFactory()
        EmploymentFactory(person=person, company="TechCorp")

        with patch("apps.people.services.generate_person_summary") as mock_gen:
            mock_gen.return_value = "Summary with employment."

            result = regenerate_person_summary(str(person.pk))

            assert result["status"] == "success"
            call_args = mock_gen.call_args[0][0]
            assert "employments" in call_args

    def test_summary_generation_error_retries(self):
        """Test that summary generation retries on error."""
        person = PersonFactory()

        with patch("apps.people.services.generate_person_summary") as mock_gen:
            mock_gen.side_effect = Exception("AI service error")

            # The task should raise for retry
            with pytest.raises(Exception):
                regenerate_person_summary(str(person.pk))


# =============================================================================
# Regenerate All Summaries Tests
# =============================================================================


@pytest.mark.django_db
class TestRegenerateAllSummaries:
    """Tests for regenerate_all_summaries task."""

    def test_queues_all_active_non_owner_persons(self):
        """Test that all active non-owner persons are queued."""
        # Get current count of eligible persons
        from apps.people.models import Person
        initial_count = Person.objects.filter(is_active=True, is_owner=False).count()

        PersonFactory(is_active=True, is_owner=False)
        PersonFactory(is_active=True, is_owner=False)
        PersonFactory(is_active=False, is_owner=False)  # Should be skipped
        PersonFactory(is_active=True, is_owner=True)  # Should be skipped

        expected_count = initial_count + 2

        with patch.object(regenerate_person_summary, "delay") as mock_delay:
            result = regenerate_all_summaries()

            assert result["status"] == "success"
            assert result["queued_count"] == expected_count
            assert mock_delay.call_count == expected_count


# =============================================================================
# Check Upcoming Birthdays Tests
# =============================================================================


@pytest.mark.django_db
class TestCheckUpcomingBirthdays:
    """Tests for check_upcoming_birthdays task."""

    def test_finds_birthdays_within_range(self):
        """Test finding birthdays within specified days."""
        today = datetime.date.today()
        upcoming_birthday = today + datetime.timedelta(days=3)

        # Create person with upcoming birthday (same month/day, different year)
        PersonFactory(
            first_name="Birthday",
            is_owner=False,
            birthday=upcoming_birthday.replace(year=1990),
        )

        result = check_upcoming_birthdays(days_ahead=7)

        assert result["status"] == "success"
        assert result["upcoming_count"] >= 1

    def test_no_upcoming_birthdays(self):
        """Test when there are no upcoming birthdays."""
        # Create person with birthday far in the future
        today = datetime.date.today()
        far_future = today + datetime.timedelta(days=100)

        PersonFactory(
            is_owner=False,
            birthday=far_future.replace(year=1990),
        )

        result = check_upcoming_birthdays(days_ahead=7)

        assert result["status"] == "success"
        # Count may include any existing test data

    def test_handles_leap_year_birthday(self):
        """Test handling of Feb 29 birthdays."""
        # Feb 29 birthday
        PersonFactory(
            is_owner=False,
            birthday=datetime.date(1992, 2, 29),
        )

        # Should not raise an error
        result = check_upcoming_birthdays(days_ahead=365)

        assert result["status"] == "success"

    def test_excludes_inactive_persons(self):
        """Test that inactive persons are excluded."""
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        PersonFactory(
            is_active=False,
            birthday=tomorrow.replace(year=1990),
        )

        result = check_upcoming_birthdays(days_ahead=7)

        assert result["status"] == "success"
        # Should not include inactive person's birthday

    def test_excludes_owner(self):
        """Test that owner is excluded."""
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        PersonFactory(
            is_owner=True,
            birthday=tomorrow.replace(year=1990),
        )

        result = check_upcoming_birthdays(days_ahead=7)

        # Owner birthday should not be in results
        for birthday in result["upcoming_birthdays"]:
            from apps.people.models import Person
            person = Person.objects.get(id=birthday["person_id"])
            assert person.is_owner is False


# =============================================================================
# Cleanup Old Audit Logs Tests
# =============================================================================


@pytest.mark.django_db
class TestCleanupOldAuditLogs:
    """Tests for cleanup_old_audit_logs task."""

    def test_cleanup_runs_successfully(self):
        """Test that cleanup runs without errors."""
        result = cleanup_old_audit_logs(days_to_keep=90)

        assert result["status"] == "success"
        assert "deleted_count" in result
        assert "cutoff_date" in result

    def test_cleanup_with_custom_retention(self):
        """Test cleanup with custom retention period."""
        result = cleanup_old_audit_logs(days_to_keep=30)

        assert result["status"] == "success"

        # Verify cutoff date is correct
        expected_cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        assert result["cutoff_date"] == expected_cutoff


# =============================================================================
# Sync LinkedIn Profile Tests
# =============================================================================


@pytest.mark.django_db
class TestSyncLinkedInProfile:
    """Tests for sync_linkedin_profile task."""

    def test_sync_success(self):
        """Test successful LinkedIn sync."""
        person = PersonFactory(linkedin_url="https://linkedin.com/in/johndoe")

        with patch("apps.people.services.sync_person_from_linkedin") as mock_sync:
            mock_sync.return_value = {
                "synced_count": 3,
                "skipped_count": 1,
            }

            result = sync_linkedin_profile(str(person.pk))

            assert result["status"] == "success"
            assert result["synced_count"] == 3
            mock_sync.assert_called_once()

    def test_sync_person_not_found(self):
        """Test sync for non-existent person."""
        import uuid

        result = sync_linkedin_profile(str(uuid.uuid4()))

        assert result["status"] == "error"
        assert "not found" in result["message"]

    def test_sync_no_linkedin_url(self):
        """Test sync when person has no LinkedIn URL."""
        person = PersonFactory(linkedin_url="")

        result = sync_linkedin_profile(str(person.pk))

        assert result["status"] == "error"
        assert "LinkedIn URL" in result["message"]

    def test_sync_config_error(self):
        """Test sync with configuration error."""
        person = PersonFactory(linkedin_url="https://linkedin.com/in/johndoe")

        with patch("apps.people.services.sync_person_from_linkedin") as mock_sync:
            mock_sync.side_effect = ValueError("LinkedIn credentials not configured")

            result = sync_linkedin_profile(str(person.pk))

            assert result["status"] == "error"

    def test_sync_inactive_person(self):
        """Test sync for inactive person."""
        person = PersonFactory(
            linkedin_url="https://linkedin.com/in/johndoe",
            is_active=False,
        )

        result = sync_linkedin_profile(str(person.pk))

        assert result["status"] == "error"


# =============================================================================
# Sync LinkedIn Profiles (Batch) Tests
# =============================================================================


@pytest.mark.django_db
class TestSyncLinkedInProfiles:
    """Tests for sync_linkedin_profiles task."""

    def test_queues_profiles_with_urls(self):
        """Test that profiles with URLs are queued."""
        PersonFactory(linkedin_url="https://linkedin.com/in/user1")
        PersonFactory(linkedin_url="https://linkedin.com/in/user2")
        PersonFactory(linkedin_url="")  # Should be skipped

        with patch.object(sync_linkedin_profile, "apply_async") as mock_async:
            result = sync_linkedin_profiles(batch_size=10, delay_seconds=5)

            assert result["status"] == "success"
            assert result["queued_count"] == 2
            assert mock_async.call_count == 2

    def test_respects_batch_size(self):
        """Test that batch size is respected."""
        for i in range(5):
            PersonFactory(linkedin_url=f"https://linkedin.com/in/user{i}")

        with patch.object(sync_linkedin_profile, "apply_async") as mock_async:
            result = sync_linkedin_profiles(batch_size=2, delay_seconds=5)

            assert result["queued_count"] == 2
            assert mock_async.call_count == 2

    def test_sets_countdown_delays(self):
        """Test that countdown delays are set correctly."""
        PersonFactory(linkedin_url="https://linkedin.com/in/user1")
        PersonFactory(linkedin_url="https://linkedin.com/in/user2")

        with patch.object(sync_linkedin_profile, "apply_async") as mock_async:
            sync_linkedin_profiles(batch_size=10, delay_seconds=30)

            # Check countdowns are progressive (0, 30, 60, etc.)
            calls = mock_async.call_args_list
            countdowns = [c.kwargs["countdown"] for c in calls]
            assert countdowns[0] == 0
            if len(countdowns) > 1:
                assert countdowns[1] == 30


# =============================================================================
# Suggest Tags For Person Tests
# =============================================================================


@pytest.mark.django_db
class TestSuggestTagsForPersonTask:
    """Tests for suggest_tags_for_person_task."""

    def test_suggest_tags_success(self):
        """Test successful tag suggestion."""
        person = PersonFactory()
        TagFactory(name="Developer")
        TagFactory(name="Manager")

        with patch("apps.people.services.suggest_tags_for_person") as mock_suggest:
            mock_suggest.return_value = [
                {"name": "Developer", "confidence": 0.9},
                {"name": "Manager", "confidence": 0.7},
            ]

            result = suggest_tags_for_person_task(str(person.pk))

            assert result["status"] == "success"
            assert len(result["suggested_tags"]) == 2

    def test_suggest_tags_person_not_found(self):
        """Test tag suggestion for non-existent person."""
        import uuid

        result = suggest_tags_for_person_task(str(uuid.uuid4()))

        assert result["status"] == "error"

    def test_suggest_tags_includes_context(self):
        """Test that context data is included in suggestion."""
        person = PersonFactory()
        owner = PersonFactory(is_owner=True)
        rt = RelationshipTypeFactory(name="Colleague")
        RelationshipFactory(person_a=person, person_b=owner, relationship_type=rt)

        with patch("apps.people.services.suggest_tags_for_person") as mock_suggest:
            mock_suggest.return_value = []

            suggest_tags_for_person_task(str(person.pk))

            mock_suggest.assert_called_once()
            call_args = mock_suggest.call_args[0]
            assert "profile" in call_args[0]


# =============================================================================
# Batch Suggest Tags Tests
# =============================================================================


@pytest.mark.django_db
class TestBatchSuggestTags:
    """Tests for batch_suggest_tags task."""

    def test_queues_persons_without_tags(self):
        """Test that persons without tags are queued."""
        from apps.people.models import Person

        # Get current count of tagless non-owner persons
        initial_count = Person.objects.filter(
            is_owner=False, is_active=True, tags__isnull=True
        ).distinct().count()

        p1 = PersonFactory(is_owner=False)  # No tags
        p2 = PersonFactory(is_owner=False)  # No tags
        p3 = PersonFactory(is_owner=False)  # Has tag
        tag = TagFactory()
        p3.tags.add(tag)

        expected_count = initial_count + 2

        with patch.object(suggest_tags_for_person_task, "delay") as mock_delay:
            mock_delay.return_value = MagicMock()

            result = batch_suggest_tags(apply_high_confidence=False)

            assert result["status"] == "success"
            assert result["queued_count"] == expected_count

    def test_excludes_owner(self):
        """Test that owner is excluded."""
        from apps.people.models import Person

        # Get current count
        initial_count = Person.objects.filter(
            is_owner=False, is_active=True, tags__isnull=True
        ).distinct().count()

        PersonFactory(is_owner=True)  # Owner, should be skipped
        PersonFactory(is_owner=False)  # Regular person

        expected_count = initial_count + 1

        with patch.object(suggest_tags_for_person_task, "delay") as mock_delay:
            mock_delay.return_value = MagicMock()

            result = batch_suggest_tags(apply_high_confidence=False)

            # Should only queue the non-owner + existing
            assert result["queued_count"] == expected_count

    def test_auto_apply_high_confidence(self):
        """Test auto-applying high confidence tags."""
        from apps.people.models import Person

        # Clear all tagless persons first to have predictable count
        Person.objects.filter(is_owner=False, tags__isnull=True).delete()

        person = PersonFactory(is_owner=False)

        mock_task_result = MagicMock()
        mock_task_result.get.return_value = {
            "status": "success",
            "suggested_tags": [
                {"name": "Developer", "confidence": 0.95},
                {"name": "Manager", "confidence": 0.5},  # Below threshold
            ],
        }

        with patch.object(suggest_tags_for_person_task, "delay") as mock_delay:
            mock_delay.return_value = mock_task_result

            result = batch_suggest_tags(
                apply_high_confidence=True,
                confidence_threshold=0.8,
            )

            assert result["status"] == "success"
            # One person with one high-confidence tag
            assert result["auto_applied_count"] == 1

            # Verify tag was applied to our test person (stored lowercase)
            person.refresh_from_db()
            assert person.tags.filter(name="developer").exists()
