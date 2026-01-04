"""
Factory Boy factories for LifeGraph models.

Provides consistent test data generation for all models.
"""

import datetime
from io import BytesIO

import factory
from django.core.files.base import ContentFile
from factory.django import DjangoModelFactory
from PIL import Image

from apps.core.models import Group, Tag
from apps.people.models import (
    Anecdote,
    CustomFieldDefinition,
    CustomFieldValue,
    Employment,
    Person,
    Photo,
    Relationship,
    RelationshipType,
)


# =============================================================================
# Core Model Factories
# =============================================================================


class TagFactory(DjangoModelFactory):
    """Factory for Tag model."""

    class Meta:
        model = Tag
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Tag {n}")
    color = factory.LazyFunction(lambda: f"#{factory.Faker('hex_color').evaluate(None, None, {'locale': None})[1:]}")
    description = factory.Faker("sentence")


class GroupFactory(DjangoModelFactory):
    """Factory for Group model."""

    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f"Group {n}")
    description = factory.Faker("paragraph")
    color = "#8b5cf6"
    parent = None


class ChildGroupFactory(GroupFactory):
    """Factory for creating child groups."""

    parent = factory.SubFactory(GroupFactory)


# =============================================================================
# People Model Factories
# =============================================================================


class PersonFactory(DjangoModelFactory):
    """Factory for Person model."""

    class Meta:
        model = Person

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    nickname = ""
    birthday = factory.LazyFunction(
        lambda: datetime.date(1990, 1, 1) + datetime.timedelta(days=factory.Faker("random_int", min=0, max=10000).evaluate(None, None, {"locale": None}))
    )
    met_date = factory.LazyFunction(lambda: datetime.date.today() - datetime.timedelta(days=365))
    met_context = factory.Faker("sentence")

    # Contact information
    emails = factory.LazyAttribute(
        lambda o: [{"email": f"{o.first_name.lower()}.{o.last_name.lower()}@example.com", "label": "personal"}]
    )
    phones = factory.LazyAttribute(lambda o: [{"phone": "+1234567890", "label": "mobile"}])
    addresses = factory.LazyAttribute(lambda o: [{"address": "123 Test St, City, ST 12345", "label": "home"}])

    # Social
    linkedin_url = ""
    discord_id = ""

    # Metadata
    notes = factory.Faker("paragraph")
    is_active = True
    is_owner = False

    # AI
    ai_summary = ""
    ai_summary_updated = None

    # Tracking
    last_contact = None

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Handle many-to-many groups."""
        if not create:
            return
        if extracted:
            for group in extracted:
                self.groups.add(group)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Handle many-to-many tags."""
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class OwnerPersonFactory(PersonFactory):
    """Factory for creating the owner person."""

    first_name = "Owner"
    last_name = "User"
    is_owner = True


# =============================================================================
# Relationship Factories
# =============================================================================


class RelationshipTypeFactory(DjangoModelFactory):
    """Factory for RelationshipType model."""

    class Meta:
        model = RelationshipType
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Relationship Type {n}")
    inverse_name = factory.LazyAttribute(lambda o: f"Inverse of {o.name}")
    category = RelationshipType.Category.SOCIAL
    is_symmetric = False
    auto_create_inverse = True


class SymmetricRelationshipTypeFactory(RelationshipTypeFactory):
    """Factory for symmetric relationship types (e.g., friend, spouse)."""

    name = factory.Sequence(lambda n: f"Friend {n}")
    inverse_name = ""  # Will be set to name on save
    is_symmetric = True


class FamilyRelationshipTypeFactory(RelationshipTypeFactory):
    """Factory for family relationship types."""

    name = factory.Sequence(lambda n: f"Parent {n}")
    inverse_name = factory.Sequence(lambda n: f"Child {n}")
    category = RelationshipType.Category.FAMILY


class ProfessionalRelationshipTypeFactory(RelationshipTypeFactory):
    """Factory for professional relationship types."""

    name = factory.Sequence(lambda n: f"Manager {n}")
    inverse_name = factory.Sequence(lambda n: f"Report {n}")
    category = RelationshipType.Category.PROFESSIONAL


class RelationshipFactory(DjangoModelFactory):
    """Factory for Relationship model."""

    class Meta:
        model = Relationship

    person_a = factory.SubFactory(PersonFactory)
    person_b = factory.SubFactory(PersonFactory)
    relationship_type = factory.SubFactory(RelationshipTypeFactory)
    started_date = factory.LazyFunction(lambda: datetime.date.today() - datetime.timedelta(days=180))
    notes = factory.Faker("sentence")
    strength = factory.Faker("random_int", min=1, max=5)
    auto_created = False


# =============================================================================
# Anecdote Factory
# =============================================================================


class AnecdoteFactory(DjangoModelFactory):
    """Factory for Anecdote model."""

    class Meta:
        model = Anecdote

    title = factory.Faker("sentence", nb_words=4)
    content = factory.Faker("paragraph", nb_sentences=5)
    date = factory.LazyFunction(lambda: datetime.date.today() - datetime.timedelta(days=30))
    location = factory.Faker("city")
    anecdote_type = Anecdote.AnecdoteType.MEMORY

    @factory.post_generation
    def persons(self, create, extracted, **kwargs):
        """Handle many-to-many persons."""
        if not create:
            return
        if extracted:
            for person in extracted:
                self.persons.add(person)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Handle many-to-many tags."""
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class JokeAnecdoteFactory(AnecdoteFactory):
    """Factory for joke anecdotes."""

    anecdote_type = Anecdote.AnecdoteType.JOKE
    title = factory.Faker("sentence", nb_words=3)


class QuoteAnecdoteFactory(AnecdoteFactory):
    """Factory for quote anecdotes."""

    anecdote_type = Anecdote.AnecdoteType.QUOTE
    title = ""
    content = factory.Faker("sentence")


class NoteAnecdoteFactory(AnecdoteFactory):
    """Factory for note anecdotes."""

    anecdote_type = Anecdote.AnecdoteType.NOTE
    title = ""


# =============================================================================
# Custom Field Factories
# =============================================================================


class CustomFieldDefinitionFactory(DjangoModelFactory):
    """Factory for CustomFieldDefinition model."""

    class Meta:
        model = CustomFieldDefinition
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Custom Field {n}")
    field_type = CustomFieldDefinition.FieldType.TEXT
    options = []
    is_required = False
    order = factory.Sequence(lambda n: n)


class SelectCustomFieldDefinitionFactory(CustomFieldDefinitionFactory):
    """Factory for select-type custom fields."""

    field_type = CustomFieldDefinition.FieldType.SELECT
    options = ["Option 1", "Option 2", "Option 3"]


class MultiSelectCustomFieldDefinitionFactory(CustomFieldDefinitionFactory):
    """Factory for multi-select custom fields."""

    field_type = CustomFieldDefinition.FieldType.MULTISELECT
    options = ["Choice A", "Choice B", "Choice C", "Choice D"]


class NumberCustomFieldDefinitionFactory(CustomFieldDefinitionFactory):
    """Factory for number-type custom fields."""

    field_type = CustomFieldDefinition.FieldType.NUMBER


class DateCustomFieldDefinitionFactory(CustomFieldDefinitionFactory):
    """Factory for date-type custom fields."""

    field_type = CustomFieldDefinition.FieldType.DATE


class CustomFieldValueFactory(DjangoModelFactory):
    """Factory for CustomFieldValue model."""

    class Meta:
        model = CustomFieldValue

    person = factory.SubFactory(PersonFactory)
    definition = factory.SubFactory(CustomFieldDefinitionFactory)
    value = factory.LazyAttribute(lambda o: "Test Value")


# =============================================================================
# Photo Factory
# =============================================================================


def create_test_image(width=100, height=100, color="red", format="JPEG"):
    """Create a test image file."""
    image = Image.new("RGB", (width, height), color=color)
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


class PhotoFactory(DjangoModelFactory):
    """Factory for Photo model."""

    class Meta:
        model = Photo

    file = factory.LazyAttribute(
        lambda o: ContentFile(create_test_image().read(), name="test_photo.jpg")
    )
    caption = factory.Faker("sentence", nb_words=6)
    date_taken = factory.LazyFunction(lambda: datetime.datetime.now() - datetime.timedelta(days=7))
    location = factory.Faker("city")
    location_coords = None
    ai_description = ""
    detected_faces = []

    @factory.post_generation
    def persons(self, create, extracted, **kwargs):
        """Handle many-to-many persons."""
        if not create:
            return
        if extracted:
            for person in extracted:
                self.persons.add(person)


class PhotoWithCoordsFactory(PhotoFactory):
    """Factory for photos with location coordinates."""

    location_coords = {"lat": 40.7128, "lng": -74.0060}


class PhotoWithAIFactory(PhotoFactory):
    """Factory for photos with AI description."""

    ai_description = factory.Faker("paragraph")
    detected_faces = [{"x": 10, "y": 10, "width": 50, "height": 50}]


# =============================================================================
# Employment Factory
# =============================================================================


class EmploymentFactory(DjangoModelFactory):
    """Factory for Employment model."""

    class Meta:
        model = Employment

    person = factory.SubFactory(PersonFactory)
    company = factory.Faker("company")
    title = factory.Faker("job")
    department = factory.Faker("word")
    start_date = factory.LazyFunction(lambda: datetime.date.today() - datetime.timedelta(days=365 * 2))
    end_date = None
    is_current = True
    location = factory.Faker("city")
    description = factory.Faker("paragraph")
    linkedin_synced = False
    linkedin_last_sync = None


class PastEmploymentFactory(EmploymentFactory):
    """Factory for past employment records."""

    start_date = factory.LazyFunction(lambda: datetime.date.today() - datetime.timedelta(days=365 * 5))
    end_date = factory.LazyFunction(lambda: datetime.date.today() - datetime.timedelta(days=365))
    is_current = False


class LinkedInSyncedEmploymentFactory(EmploymentFactory):
    """Factory for LinkedIn-synced employment records."""

    linkedin_synced = True
    linkedin_last_sync = factory.LazyFunction(lambda: datetime.datetime.now())


# =============================================================================
# Composite Factories (for complex test scenarios)
# =============================================================================


class PersonWithFullProfileFactory(PersonFactory):
    """Factory for creating a person with complete profile data."""

    nickname = factory.Faker("first_name")
    linkedin_url = factory.LazyAttribute(
        lambda o: f"https://linkedin.com/in/{o.first_name.lower()}-{o.last_name.lower()}"
    )
    discord_id = factory.Sequence(lambda n: f"user{n}#1234")
    ai_summary = factory.Faker("paragraph", nb_sentences=3)
    ai_summary_updated = factory.LazyFunction(lambda: datetime.datetime.now())
    last_contact = factory.LazyFunction(lambda: datetime.datetime.now() - datetime.timedelta(days=3))

    @factory.post_generation
    def with_employment(self, create, extracted, **kwargs):
        """Optionally create employment record."""
        if not create or not extracted:
            return
        EmploymentFactory(person=self)

    @factory.post_generation
    def with_photo(self, create, extracted, **kwargs):
        """Optionally create photo."""
        if not create or not extracted:
            return
        photo = PhotoFactory()
        photo.persons.add(self)
