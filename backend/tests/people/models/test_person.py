"""
Tests for the Person model.
"""

import datetime

import pytest

from apps.people.models import Person
from tests.factories import (
    GroupFactory,
    OwnerPersonFactory,
    PersonFactory,
    PersonWithFullProfileFactory,
    TagFactory,
)


# =============================================================================
# Person Creation Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonCreation:
    """Tests for Person model creation."""

    def test_create_basic_person(self):
        """Test creating a person with minimal required fields."""
        person = PersonFactory(first_name="John", last_name="Doe")

        assert person.first_name == "John"
        assert person.last_name == "Doe"
        assert person.pk is not None
        assert person.is_active is True
        assert person.is_owner is False

    def test_create_person_first_name_only(self):
        """Test creating a person with only first name."""
        person = PersonFactory(first_name="Madonna", last_name="")

        assert person.first_name == "Madonna"
        assert person.last_name == ""
        assert person.full_name == "Madonna"

    def test_create_person_with_nickname(self):
        """Test creating a person with a nickname."""
        person = PersonFactory(
            first_name="William",
            last_name="Smith",
            nickname="Bill",
        )

        assert person.nickname == "Bill"
        assert "Bill" in str(person)

    def test_create_owner_person(self):
        """Test creating the owner person."""
        owner = OwnerPersonFactory()

        assert owner.is_owner is True
        assert owner.first_name == "Owner"

    def test_person_timestamps(self):
        """Test that persons have created_at and updated_at timestamps."""
        person = PersonFactory()

        assert person.created_at is not None
        assert person.updated_at is not None

    def test_person_with_full_profile(self):
        """Test creating a person with complete profile data."""
        person = PersonWithFullProfileFactory()

        assert person.nickname != ""
        assert person.linkedin_url != ""
        assert person.discord_id != ""
        assert person.ai_summary != ""
        assert person.ai_summary_updated is not None
        assert person.last_contact is not None


# =============================================================================
# Person Properties Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonProperties:
    """Tests for Person model properties."""

    def test_full_name_with_last_name(self):
        """Test full_name property with first and last name."""
        person = PersonFactory(first_name="John", last_name="Doe")

        assert person.full_name == "John Doe"

    def test_full_name_without_last_name(self):
        """Test full_name property with only first name."""
        person = PersonFactory(first_name="Prince", last_name="")

        assert person.full_name == "Prince"

    def test_primary_email_with_emails(self):
        """Test primary_email property returns first email."""
        person = PersonFactory(
            emails=[
                {"email": "primary@example.com", "label": "personal"},
                {"email": "secondary@example.com", "label": "work"},
            ]
        )

        assert person.primary_email == "primary@example.com"

    def test_primary_email_empty(self):
        """Test primary_email property with no emails."""
        person = PersonFactory(emails=[])

        assert person.primary_email is None

    def test_primary_phone_with_phones(self):
        """Test primary_phone property returns first phone."""
        person = PersonFactory(
            phones=[
                {"phone": "+1234567890", "label": "mobile"},
                {"phone": "+0987654321", "label": "work"},
            ]
        )

        assert person.primary_phone == "+1234567890"

    def test_primary_phone_empty(self):
        """Test primary_phone property with no phones."""
        person = PersonFactory(phones=[])

        assert person.primary_phone is None


# =============================================================================
# Person String Representation Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonStrRepresentation:
    """Tests for Person __str__ method."""

    def test_str_with_full_name(self):
        """Test string representation with full name."""
        person = PersonFactory(first_name="Jane", last_name="Smith", nickname="")

        assert str(person) == "Jane Smith"

    def test_str_with_nickname(self):
        """Test string representation includes nickname."""
        person = PersonFactory(
            first_name="Robert",
            last_name="Johnson",
            nickname="Bobby",
        )

        assert str(person) == "Robert Johnson (Bobby)"

    def test_str_first_name_only(self):
        """Test string representation with first name only."""
        person = PersonFactory(first_name="Cher", last_name="", nickname="")

        assert str(person) == "Cher"


# =============================================================================
# Person Soft Delete Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonSoftDelete:
    """Tests for Person soft delete functionality."""

    def test_person_default_active(self):
        """Test that persons are active by default."""
        person = PersonFactory()

        assert person.is_active is True

    def test_person_soft_delete(self):
        """Test soft deleting a person."""
        person = PersonFactory()
        person.is_active = False
        person.save()

        person.refresh_from_db()

        assert person.is_active is False

    def test_person_can_query_inactive(self):
        """Test that inactive persons are still queryable."""
        person = PersonFactory(is_active=False)

        found = Person.objects.filter(pk=person.pk, is_active=False).first()

        assert found is not None
        assert found.pk == person.pk


# =============================================================================
# Person Ordering Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonOrdering:
    """Tests for Person default ordering."""

    def test_ordering_by_last_name_first_name(self):
        """Test that persons are ordered by last_name, first_name."""
        p1 = PersonFactory(first_name="Zack", last_name="Adams")
        p2 = PersonFactory(first_name="Adam", last_name="Zack")
        p3 = PersonFactory(first_name="Beta", last_name="Adams")

        # Filter to only our test records to avoid interference from other tests
        test_ids = [p1.pk, p2.pk, p3.pk]
        persons = list(Person.objects.filter(pk__in=test_ids))

        # Should be ordered: Adams, Adams, Zack (by last name first)
        assert persons[0].last_name == "Adams"
        assert persons[0].first_name == "Beta"  # Then by first name
        assert persons[1].last_name == "Adams"
        assert persons[1].first_name == "Zack"
        assert persons[2].last_name == "Zack"


# =============================================================================
# Person Date Fields Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonDateFields:
    """Tests for Person date fields."""

    def test_person_with_birthday(self):
        """Test creating a person with birthday."""
        birthday = datetime.date(1990, 6, 15)
        person = PersonFactory(birthday=birthday)

        assert person.birthday == birthday

    def test_person_without_birthday(self):
        """Test creating a person without birthday."""
        person = PersonFactory(birthday=None)

        assert person.birthday is None

    def test_person_met_date(self):
        """Test creating a person with met_date."""
        met_date = datetime.date(2020, 1, 1)
        person = PersonFactory(met_date=met_date)

        assert person.met_date == met_date

    def test_person_last_contact(self):
        """Test updating last_contact timestamp."""
        person = PersonFactory(last_contact=None)

        now = datetime.datetime.now()
        person.last_contact = now
        person.save()

        person.refresh_from_db()
        # Note: Datetime comparison might have microsecond differences
        assert person.last_contact is not None


# =============================================================================
# Person Social Links Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonSocialLinks:
    """Tests for Person social link fields."""

    def test_person_linkedin_url(self):
        """Test person with LinkedIn URL."""
        linkedin_url = "https://linkedin.com/in/john-doe"
        person = PersonFactory(linkedin_url=linkedin_url)

        assert person.linkedin_url == linkedin_url

    def test_person_discord_id(self):
        """Test person with Discord ID."""
        discord_id = "johndoe#1234"
        person = PersonFactory(discord_id=discord_id)

        assert person.discord_id == discord_id

    def test_person_social_links_optional(self):
        """Test that social links are optional."""
        person = PersonFactory(linkedin_url="", discord_id="")

        assert person.linkedin_url == ""
        assert person.discord_id == ""


# =============================================================================
# Person AI Fields Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonAIFields:
    """Tests for Person AI-related fields."""

    def test_person_ai_summary(self):
        """Test person with AI summary."""
        summary = "This person is a software engineer with interests in AI."
        person = PersonFactory(ai_summary=summary)

        assert person.ai_summary == summary

    def test_person_ai_summary_updated(self):
        """Test AI summary updated timestamp."""
        now = datetime.datetime.now()
        person = PersonFactory(ai_summary="Summary", ai_summary_updated=now)

        assert person.ai_summary_updated is not None

    def test_person_ai_fields_optional(self):
        """Test that AI fields are optional."""
        person = PersonFactory(ai_summary="", ai_summary_updated=None)

        assert person.ai_summary == ""
        assert person.ai_summary_updated is None


# =============================================================================
# Person Relationships Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonRelationships:
    """Tests for Person many-to-many relationships."""

    def test_person_add_groups(self):
        """Test adding groups to a person."""
        person = PersonFactory()
        group1 = GroupFactory(name="Family")
        group2 = GroupFactory(name="Friends")

        person.groups.add(group1, group2)

        assert person.groups.count() == 2

    def test_person_add_tags(self):
        """Test adding tags to a person."""
        person = PersonFactory()
        tag1 = TagFactory(name="VIP")
        tag2 = TagFactory(name="Priority")

        person.tags.add(tag1, tag2)

        assert person.tags.count() == 2

    def test_person_factory_with_groups(self):
        """Test factory with groups parameter."""
        group = GroupFactory(name="Test Group")
        person = PersonFactory(groups=[group])

        assert group in person.groups.all()

    def test_person_factory_with_tags(self):
        """Test factory with tags parameter."""
        tag = TagFactory(name="Test Tag")
        person = PersonFactory(tags=[tag])

        assert tag in person.tags.all()
