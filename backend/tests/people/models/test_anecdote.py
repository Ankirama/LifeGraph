"""
Tests for the Anecdote model.
"""

import datetime

import pytest

from apps.people.models import Anecdote
from tests.factories import (
    AnecdoteFactory,
    JokeAnecdoteFactory,
    NoteAnecdoteFactory,
    PersonFactory,
    QuoteAnecdoteFactory,
    TagFactory,
)


# =============================================================================
# Anecdote Creation Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteCreation:
    """Tests for Anecdote model creation."""

    def test_create_basic_anecdote(self):
        """Test creating a basic anecdote."""
        anecdote = AnecdoteFactory(
            title="A memorable day",
            content="We had a great time at the park.",
        )

        assert anecdote.title == "A memorable day"
        assert anecdote.content == "We had a great time at the park."
        assert anecdote.pk is not None

    def test_create_anecdote_with_date(self):
        """Test creating an anecdote with a date."""
        date = datetime.date(2023, 7, 4)
        anecdote = AnecdoteFactory(date=date)

        assert anecdote.date == date

    def test_create_anecdote_with_location(self):
        """Test creating an anecdote with a location."""
        anecdote = AnecdoteFactory(location="Central Park, NYC")

        assert anecdote.location == "Central Park, NYC"

    def test_anecdote_timestamps(self):
        """Test that anecdotes have timestamps."""
        anecdote = AnecdoteFactory()

        assert anecdote.created_at is not None
        assert anecdote.updated_at is not None


# =============================================================================
# Anecdote Type Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteTypes:
    """Tests for different Anecdote types."""

    def test_memory_anecdote(self):
        """Test creating a memory type anecdote."""
        anecdote = AnecdoteFactory(anecdote_type=Anecdote.AnecdoteType.MEMORY)

        assert anecdote.anecdote_type == Anecdote.AnecdoteType.MEMORY

    def test_joke_anecdote(self):
        """Test creating a joke type anecdote."""
        anecdote = JokeAnecdoteFactory()

        assert anecdote.anecdote_type == Anecdote.AnecdoteType.JOKE

    def test_quote_anecdote(self):
        """Test creating a quote type anecdote."""
        anecdote = QuoteAnecdoteFactory()

        assert anecdote.anecdote_type == Anecdote.AnecdoteType.QUOTE
        assert anecdote.title == ""  # Quotes typically don't have titles

    def test_note_anecdote(self):
        """Test creating a note type anecdote."""
        anecdote = NoteAnecdoteFactory()

        assert anecdote.anecdote_type == Anecdote.AnecdoteType.NOTE

    def test_all_anecdote_types_valid(self):
        """Test all anecdote type choices are valid."""
        valid_types = [choice[0] for choice in Anecdote.AnecdoteType.choices]

        assert "memory" in valid_types
        assert "joke" in valid_types
        assert "quote" in valid_types
        assert "note" in valid_types


# =============================================================================
# Anecdote String Representation Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteStrRepresentation:
    """Tests for Anecdote __str__ method."""

    def test_str_with_title(self):
        """Test string representation with title."""
        anecdote = AnecdoteFactory(title="Important Memory")

        assert str(anecdote) == "Important Memory"

    def test_str_without_title(self):
        """Test string representation without title uses type and date."""
        anecdote = AnecdoteFactory(title="", anecdote_type=Anecdote.AnecdoteType.NOTE)

        str_rep = str(anecdote)
        assert "note" in str_rep.lower()


# =============================================================================
# Anecdote Ordering Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteOrdering:
    """Tests for Anecdote ordering."""

    def test_ordering_by_date_desc(self):
        """Test that anecdotes are ordered by date descending."""
        anecdote1 = AnecdoteFactory(date=datetime.date(2020, 1, 1))
        anecdote2 = AnecdoteFactory(date=datetime.date(2023, 6, 15))
        anecdote3 = AnecdoteFactory(date=datetime.date(2021, 12, 31))

        anecdotes = list(Anecdote.objects.all())

        # Most recent first
        assert anecdotes[0].pk == anecdote2.pk
        assert anecdotes[1].pk == anecdote3.pk
        assert anecdotes[2].pk == anecdote1.pk


# =============================================================================
# Anecdote Person Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdotePersonRelationship:
    """Tests for Anecdote-Person many-to-many relationship."""

    def test_add_persons_to_anecdote(self):
        """Test adding persons to an anecdote."""
        person1 = PersonFactory()
        person2 = PersonFactory()
        anecdote = AnecdoteFactory()

        anecdote.persons.add(person1, person2)

        assert anecdote.persons.count() == 2
        assert person1 in anecdote.persons.all()
        assert person2 in anecdote.persons.all()

    def test_get_anecdotes_for_person(self):
        """Test getting anecdotes associated with a person."""
        person = PersonFactory()
        anecdote1 = AnecdoteFactory()
        anecdote2 = AnecdoteFactory()
        anecdote3 = AnecdoteFactory()  # Not associated with person

        anecdote1.persons.add(person)
        anecdote2.persons.add(person)

        person_anecdotes = list(person.anecdotes.all())

        assert len(person_anecdotes) == 2
        assert anecdote1 in person_anecdotes
        assert anecdote2 in person_anecdotes
        assert anecdote3 not in person_anecdotes

    def test_anecdote_factory_with_persons(self):
        """Test factory with persons parameter."""
        person = PersonFactory()
        anecdote = AnecdoteFactory(persons=[person])

        assert person in anecdote.persons.all()

    def test_anecdote_with_multiple_persons(self):
        """Test anecdote with group memory."""
        persons = [PersonFactory() for _ in range(5)]
        anecdote = AnecdoteFactory(
            title="Group Trip",
            content="We all went hiking together.",
        )
        for person in persons:
            anecdote.persons.add(person)

        assert anecdote.persons.count() == 5


# =============================================================================
# Anecdote Tag Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteTagRelationship:
    """Tests for Anecdote-Tag many-to-many relationship."""

    def test_add_tags_to_anecdote(self):
        """Test adding tags to an anecdote."""
        tag1 = TagFactory(name="Fun")
        tag2 = TagFactory(name="Travel")
        anecdote = AnecdoteFactory()

        anecdote.tags.add(tag1, tag2)

        assert anecdote.tags.count() == 2

    def test_get_anecdotes_by_tag(self):
        """Test getting anecdotes with a specific tag."""
        tag = TagFactory(name="Work")
        anecdote1 = AnecdoteFactory()
        anecdote2 = AnecdoteFactory()
        anecdote3 = AnecdoteFactory()  # Not tagged

        anecdote1.tags.add(tag)
        anecdote2.tags.add(tag)

        tagged_anecdotes = list(tag.anecdotes.all())

        assert len(tagged_anecdotes) == 2
        assert anecdote1 in tagged_anecdotes
        assert anecdote3 not in tagged_anecdotes

    def test_anecdote_factory_with_tags(self):
        """Test factory with tags parameter."""
        tag = TagFactory(name="Important")
        anecdote = AnecdoteFactory(tags=[tag])

        assert tag in anecdote.tags.all()


# =============================================================================
# Anecdote Content Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteContent:
    """Tests for Anecdote content field."""

    def test_anecdote_content_supports_markdown(self):
        """Test that content can contain markdown."""
        markdown_content = """
        # Heading

        Some **bold** and *italic* text.

        - List item 1
        - List item 2

        ```python
        print("Hello World")
        ```
        """
        anecdote = AnecdoteFactory(content=markdown_content)

        assert "# Heading" in anecdote.content
        assert "**bold**" in anecdote.content

    def test_anecdote_content_supports_unicode(self):
        """Test that content supports unicode characters."""
        unicode_content = "Meeting with 日本の友人 was fun! 🎉🎊"
        anecdote = AnecdoteFactory(content=unicode_content)

        assert "日本の友人" in anecdote.content
        assert "🎉" in anecdote.content


# =============================================================================
# Anecdote Optional Fields Tests
# =============================================================================


@pytest.mark.django_db
class TestAnecdoteOptionalFields:
    """Tests for Anecdote optional fields."""

    def test_title_optional(self):
        """Test that title is optional."""
        anecdote = AnecdoteFactory(title="")

        assert anecdote.title == ""
        assert anecdote.pk is not None

    def test_date_optional(self):
        """Test that date is optional."""
        anecdote = AnecdoteFactory(date=None)

        assert anecdote.date is None

    def test_location_optional(self):
        """Test that location is optional."""
        anecdote = AnecdoteFactory(location="")

        assert anecdote.location == ""
