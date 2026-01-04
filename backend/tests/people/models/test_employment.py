"""
Tests for the Employment model.
"""

import datetime

import pytest

from apps.people.models import Employment
from tests.factories import (
    EmploymentFactory,
    LinkedInSyncedEmploymentFactory,
    PastEmploymentFactory,
    PersonFactory,
)


# =============================================================================
# Employment Creation Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentCreation:
    """Tests for Employment model creation."""

    def test_create_basic_employment(self):
        """Test creating a basic employment record."""
        person = PersonFactory()
        employment = EmploymentFactory(
            person=person,
            company="TechCorp",
            title="Software Engineer",
        )

        assert employment.person == person
        assert employment.company == "TechCorp"
        assert employment.title == "Software Engineer"
        assert employment.pk is not None

    def test_create_employment_with_department(self):
        """Test creating employment with department."""
        employment = EmploymentFactory(department="Engineering")

        assert employment.department == "Engineering"

    def test_create_employment_with_dates(self):
        """Test creating employment with dates."""
        start = datetime.date(2020, 1, 1)
        end = datetime.date(2023, 12, 31)

        employment = EmploymentFactory(
            start_date=start,
            end_date=end,
            is_current=False,
        )

        assert employment.start_date == start
        assert employment.end_date == end

    def test_employment_timestamps(self):
        """Test that employment has timestamps."""
        employment = EmploymentFactory()

        assert employment.created_at is not None
        assert employment.updated_at is not None


# =============================================================================
# Current Employment Tests
# =============================================================================


@pytest.mark.django_db
class TestCurrentEmployment:
    """Tests for current employment logic."""

    def test_current_employment(self):
        """Test creating a current employment."""
        employment = EmploymentFactory(is_current=True, end_date=None)

        assert employment.is_current is True
        assert employment.end_date is None

    def test_setting_current_unmarks_previous(self):
        """Test that setting new current unmarks previous current jobs."""
        person = PersonFactory()

        # Create first current job
        job1 = EmploymentFactory(person=person, company="First Corp", is_current=True)
        assert job1.is_current is True

        # Create second current job
        job2 = EmploymentFactory(person=person, company="Second Corp", is_current=True)

        # Refresh job1 from database
        job1.refresh_from_db()

        assert job2.is_current is True
        assert job1.is_current is False

    def test_past_employment_factory(self):
        """Test the past employment factory."""
        employment = PastEmploymentFactory()

        assert employment.is_current is False
        assert employment.end_date is not None


# =============================================================================
# Employment String Representation Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentStrRepresentation:
    """Tests for Employment __str__ method."""

    def test_str_current_employment(self):
        """Test string representation of current employment."""
        person = PersonFactory(first_name="John", last_name="Doe")
        employment = EmploymentFactory(
            person=person,
            company="TechCorp",
            title="Developer",
            is_current=True,
        )

        expected = "John Doe - Developer at TechCorp (current)"
        assert str(employment) == expected

    def test_str_past_employment(self):
        """Test string representation of past employment."""
        person = PersonFactory(first_name="Jane", last_name="Smith")
        employment = EmploymentFactory(
            person=person,
            company="OldCorp",
            title="Manager",
            is_current=False,
        )

        expected = "Jane Smith - Manager at OldCorp"
        assert str(employment) == expected


# =============================================================================
# Employment Ordering Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentOrdering:
    """Tests for Employment ordering."""

    def test_ordering_current_first(self):
        """Test that current jobs come first."""
        person = PersonFactory()

        past = PastEmploymentFactory(
            person=person,
            start_date=datetime.date(2022, 1, 1),
        )
        current = EmploymentFactory(
            person=person,
            is_current=True,
            start_date=datetime.date(2020, 1, 1),
        )

        employments = list(Employment.objects.filter(person=person))

        # Current first, then by start_date descending
        assert employments[0].is_current is True

    def test_ordering_by_start_date_desc(self):
        """Test that within same is_current, ordered by start_date desc."""
        person = PersonFactory()

        job1 = PastEmploymentFactory(
            person=person,
            start_date=datetime.date(2015, 1, 1),
        )
        job2 = PastEmploymentFactory(
            person=person,
            start_date=datetime.date(2020, 1, 1),
        )
        job3 = PastEmploymentFactory(
            person=person,
            start_date=datetime.date(2018, 1, 1),
        )

        employments = list(Employment.objects.filter(person=person, is_current=False))

        # Most recent start_date first
        assert employments[0].pk == job2.pk
        assert employments[1].pk == job3.pk
        assert employments[2].pk == job1.pk


# =============================================================================
# Employment LinkedIn Sync Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentLinkedInSync:
    """Tests for Employment LinkedIn sync fields."""

    def test_linkedin_synced_employment(self):
        """Test LinkedIn synced employment."""
        employment = LinkedInSyncedEmploymentFactory()

        assert employment.linkedin_synced is True
        assert employment.linkedin_last_sync is not None

    def test_not_synced_by_default(self):
        """Test that employment is not synced by default."""
        employment = EmploymentFactory()

        assert employment.linkedin_synced is False
        assert employment.linkedin_last_sync is None


# =============================================================================
# Employment Person Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentPersonRelationship:
    """Tests for Employment-Person relationship."""

    def test_person_employments(self):
        """Test getting all employments for a person."""
        person = PersonFactory()
        job1 = EmploymentFactory(person=person, company="Company A")
        job2 = EmploymentFactory(person=person, company="Company B")

        assert person.employments.count() == 2
        assert job1 in person.employments.all()
        assert job2 in person.employments.all()

    def test_delete_person_cascades(self):
        """Test that deleting person deletes their employment."""
        person = PersonFactory()
        employment = EmploymentFactory(person=person)
        emp_id = employment.pk

        person.delete()

        assert not Employment.objects.filter(pk=emp_id).exists()


# =============================================================================
# Employment Optional Fields Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentOptionalFields:
    """Tests for Employment optional fields."""

    def test_department_optional(self):
        """Test that department is optional."""
        employment = EmploymentFactory(department="")

        assert employment.department == ""

    def test_dates_optional(self):
        """Test that dates are optional."""
        employment = EmploymentFactory(start_date=None, end_date=None)

        assert employment.start_date is None
        assert employment.end_date is None

    def test_location_optional(self):
        """Test that location is optional."""
        employment = EmploymentFactory(location="")

        assert employment.location == ""

    def test_description_optional(self):
        """Test that description is optional."""
        employment = EmploymentFactory(description="")

        assert employment.description == ""
