"""
Tests for the Photo model.
"""

import datetime

import pytest

from apps.people.models import Photo
from tests.factories import (
    AnecdoteFactory,
    PersonFactory,
    PhotoFactory,
    PhotoWithAIFactory,
    PhotoWithCoordsFactory,
)


# =============================================================================
# Photo Creation Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoCreation:
    """Tests for Photo model creation."""

    def test_create_basic_photo(self):
        """Test creating a basic photo."""
        photo = PhotoFactory(caption="Beach sunset")

        assert photo.caption == "Beach sunset"
        assert photo.file is not None
        assert photo.pk is not None

    def test_photo_with_date_taken(self):
        """Test creating a photo with date taken."""
        date = datetime.datetime(2023, 8, 15, 14, 30)
        photo = PhotoFactory(date_taken=date)

        assert photo.date_taken is not None

    def test_photo_with_location(self):
        """Test creating a photo with location."""
        photo = PhotoFactory(location="New York City")

        assert photo.location == "New York City"

    def test_photo_timestamps(self):
        """Test that photos have timestamps."""
        photo = PhotoFactory()

        assert photo.created_at is not None
        assert photo.updated_at is not None


# =============================================================================
# Photo Location Coordinates Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoLocationCoordinates:
    """Tests for Photo location coordinates."""

    def test_photo_with_coordinates(self):
        """Test creating a photo with location coordinates."""
        photo = PhotoWithCoordsFactory()

        assert photo.location_coords is not None
        assert "lat" in photo.location_coords
        assert "lng" in photo.location_coords
        assert photo.location_coords["lat"] == 40.7128
        assert photo.location_coords["lng"] == -74.0060

    def test_photo_coordinates_optional(self):
        """Test that coordinates are optional."""
        photo = PhotoFactory(location_coords=None)

        assert photo.location_coords is None


# =============================================================================
# Photo AI Fields Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoAIFields:
    """Tests for Photo AI-related fields."""

    def test_photo_with_ai_description(self):
        """Test creating a photo with AI description."""
        photo = PhotoWithAIFactory()

        assert photo.ai_description != ""

    def test_photo_with_detected_faces(self):
        """Test creating a photo with detected faces."""
        photo = PhotoWithAIFactory()

        assert photo.detected_faces is not None
        assert len(photo.detected_faces) > 0
        assert "x" in photo.detected_faces[0]
        assert "y" in photo.detected_faces[0]

    def test_photo_ai_fields_optional(self):
        """Test that AI fields are optional."""
        photo = PhotoFactory(ai_description="", detected_faces=[])

        assert photo.ai_description == ""
        assert photo.detected_faces == []


# =============================================================================
# Photo String Representation Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoStrRepresentation:
    """Tests for Photo __str__ method."""

    def test_str_with_caption(self):
        """Test string representation with caption."""
        photo = PhotoFactory(caption="A beautiful landscape")

        assert str(photo) == "A beautiful landscape"

    def test_str_long_caption_truncated(self):
        """Test that long captions are truncated."""
        long_caption = "A" * 100
        photo = PhotoFactory(caption=long_caption)

        assert len(str(photo)) <= 50

    def test_str_without_caption(self):
        """Test string representation without caption."""
        photo = PhotoFactory(caption="")

        assert "Photo" in str(photo)


# =============================================================================
# Photo Ordering Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoOrdering:
    """Tests for Photo ordering."""

    def test_ordering_by_date_taken_desc(self):
        """Test that photos are ordered by date_taken descending."""
        photo1 = PhotoFactory(date_taken=datetime.datetime(2020, 1, 1))
        photo2 = PhotoFactory(date_taken=datetime.datetime(2023, 6, 15))
        photo3 = PhotoFactory(date_taken=datetime.datetime(2021, 12, 31))

        photos = list(Photo.objects.all())

        # Most recent first
        assert photos[0].pk == photo2.pk
        assert photos[1].pk == photo3.pk
        assert photos[2].pk == photo1.pk


# =============================================================================
# Photo Person Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoPersonRelationship:
    """Tests for Photo-Person many-to-many relationship."""

    def test_add_persons_to_photo(self):
        """Test adding persons to a photo."""
        person1 = PersonFactory()
        person2 = PersonFactory()
        photo = PhotoFactory()

        photo.persons.add(person1, person2)

        assert photo.persons.count() == 2

    def test_get_photos_for_person(self):
        """Test getting photos associated with a person."""
        person = PersonFactory()
        photo1 = PhotoFactory()
        photo2 = PhotoFactory()
        photo3 = PhotoFactory()  # Not associated

        photo1.persons.add(person)
        photo2.persons.add(person)

        person_photos = list(person.photos.all())

        assert len(person_photos) == 2
        assert photo1 in person_photos
        assert photo3 not in person_photos

    def test_photo_factory_with_persons(self):
        """Test factory with persons parameter."""
        person = PersonFactory()
        photo = PhotoFactory(persons=[person])

        assert person in photo.persons.all()


# =============================================================================
# Photo Anecdote Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoAnecdoteRelationship:
    """Tests for Photo-Anecdote relationship."""

    def test_photo_with_anecdote(self):
        """Test associating a photo with an anecdote."""
        anecdote = AnecdoteFactory(title="Birthday Party")
        photo = PhotoFactory(anecdote=anecdote)

        assert photo.anecdote == anecdote

    def test_anecdote_photos(self):
        """Test getting photos for an anecdote."""
        anecdote = AnecdoteFactory()
        photo1 = PhotoFactory(anecdote=anecdote)
        photo2 = PhotoFactory(anecdote=anecdote)

        assert anecdote.photos.count() == 2
        assert photo1 in anecdote.photos.all()
        assert photo2 in anecdote.photos.all()

    def test_delete_anecdote_nullifies_photo(self):
        """Test that deleting anecdote nullifies photo.anecdote."""
        anecdote = AnecdoteFactory()
        photo = PhotoFactory(anecdote=anecdote)
        photo_id = photo.pk

        anecdote.delete()

        photo = Photo.objects.get(pk=photo_id)
        assert photo.anecdote is None

    def test_photo_anecdote_optional(self):
        """Test that anecdote is optional."""
        photo = PhotoFactory(anecdote=None)

        assert photo.anecdote is None


# =============================================================================
# Photo File Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoFile:
    """Tests for Photo file field."""

    def test_photo_file_upload_path(self):
        """Test that photos are uploaded to correct path."""
        photo = PhotoFactory()

        # File path should contain photos/
        assert "photos" in photo.file.name or photo.file.name.startswith("test")

    def test_photo_file_exists(self):
        """Test that photo file is created."""
        photo = PhotoFactory()

        assert photo.file is not None
        assert photo.file.size > 0
