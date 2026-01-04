"""
Pytest configuration and shared fixtures for LifeGraph tests.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

# Set up Django settings before any imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lifegraph.settings.development")

# Generate a test encryption key
TEST_FERNET_KEY = "dGVzdC1mZXJuZXQta2V5LWZvci10ZXN0aW5nLW9ubHk="


@pytest.fixture(scope="session")
def django_db_setup():
    """Configure test database."""
    pass


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpassword123",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an admin-authenticated API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client


# =============================================================================
# Model Fixtures (imported from factories)
# =============================================================================


@pytest.fixture
def tag(db):
    """Create a test tag."""
    from tests.factories import TagFactory
    return TagFactory()


@pytest.fixture
def group(db):
    """Create a test group."""
    from tests.factories import GroupFactory
    return GroupFactory()


@pytest.fixture
def person(db):
    """Create a test person."""
    from tests.factories import PersonFactory
    return PersonFactory()


@pytest.fixture
def owner_person(db):
    """Create the owner person (is_owner=True)."""
    from tests.factories import PersonFactory
    return PersonFactory(is_owner=True, first_name="Owner", last_name="User")


@pytest.fixture
def relationship_type(db):
    """Create a test relationship type."""
    from tests.factories import RelationshipTypeFactory
    return RelationshipTypeFactory()


@pytest.fixture
def symmetric_relationship_type(db):
    """Create a symmetric relationship type."""
    from tests.factories import RelationshipTypeFactory
    return RelationshipTypeFactory(
        name="friend",
        inverse_name="friend",
        is_symmetric=True,
    )


@pytest.fixture
def relationship(db, person, relationship_type):
    """Create a test relationship."""
    from tests.factories import PersonFactory, RelationshipFactory
    other_person = PersonFactory()
    return RelationshipFactory(
        person_a=person,
        person_b=other_person,
        relationship_type=relationship_type,
    )


@pytest.fixture
def anecdote(db, person):
    """Create a test anecdote."""
    from tests.factories import AnecdoteFactory
    anecdote = AnecdoteFactory()
    anecdote.persons.add(person)
    return anecdote


@pytest.fixture
def photo(db):
    """Create a test photo."""
    from tests.factories import PhotoFactory
    return PhotoFactory()


@pytest.fixture
def employment(db, person):
    """Create a test employment record."""
    from tests.factories import EmploymentFactory
    return EmploymentFactory(person=person)


@pytest.fixture
def custom_field_definition(db):
    """Create a custom field definition."""
    from tests.factories import CustomFieldDefinitionFactory
    return CustomFieldDefinitionFactory()


# =============================================================================
# Mock Fixtures for External Services
# =============================================================================


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for AI service tests."""
    with patch("apps.people.services.ai_parser.get_openai_client") as mock:
        client = MagicMock()
        mock.return_value = client

        # Default mock response
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = '{"result": "mocked"}'
        client.chat.completions.create.return_value = response

        yield client


@pytest.fixture
def mock_linkedin():
    """Mock LinkedIn client for LinkedIn service tests."""
    with patch("apps.people.services.linkedin.get_linkedin_client") as mock:
        client = MagicMock()
        mock.return_value = client

        # Default mock profile response
        client.get_profile.return_value = {
            "firstName": "John",
            "lastName": "Doe",
            "headline": "Software Engineer at TechCorp",
            "summary": "Experienced developer",
            "experience": [
                {
                    "companyName": "TechCorp",
                    "title": "Software Engineer",
                    "timePeriod": {
                        "startDate": {"year": 2020, "month": 1},
                    },
                }
            ],
        }

        yield client


@pytest.fixture
def mock_openai_vision():
    """Mock OpenAI Vision API for photo description tests."""
    with patch("apps.people.services.ai_parser.get_openai_client") as mock:
        client = MagicMock()
        mock.return_value = client

        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "A scenic photo of a group of friends."
        client.chat.completions.create.return_value = response

        yield client


# =============================================================================
# Settings Overrides
# =============================================================================


@pytest.fixture
def with_encryption(settings):
    """Enable encryption for tests."""
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    settings.FERNET_KEYS = [key]
    return key


@pytest.fixture
def without_rate_limit(settings):
    """Disable rate limiting for tests."""
    settings.RATELIMIT_ENABLE = False


# =============================================================================
# Database Helpers
# =============================================================================


@pytest.fixture
def sample_persons(db):
    """Create multiple test persons for list/search tests."""
    from tests.factories import PersonFactory
    return [
        PersonFactory(first_name="Alice", last_name="Smith"),
        PersonFactory(first_name="Bob", last_name="Johnson"),
        PersonFactory(first_name="Charlie", last_name="Williams"),
        PersonFactory(first_name="Diana", last_name="Brown"),
        PersonFactory(first_name="Eve", last_name="Jones"),
    ]


@pytest.fixture
def person_with_relationships(db, person, symmetric_relationship_type):
    """Create a person with multiple relationships."""
    from tests.factories import PersonFactory, RelationshipFactory

    friends = [PersonFactory() for _ in range(3)]
    for friend in friends:
        RelationshipFactory(
            person_a=person,
            person_b=friend,
            relationship_type=symmetric_relationship_type,
        )

    return person, friends


@pytest.fixture
def person_with_anecdotes(db, person):
    """Create a person with multiple anecdotes."""
    from tests.factories import AnecdoteFactory

    anecdotes = [AnecdoteFactory() for _ in range(5)]
    for anecdote in anecdotes:
        anecdote.persons.add(person)

    return person, anecdotes


# =============================================================================
# File Upload Helpers
# =============================================================================


@pytest.fixture
def sample_image():
    """Create a sample image file for upload tests."""
    from io import BytesIO
    from PIL import Image
    from django.core.files.uploadedfile import SimpleUploadedFile

    # Create a simple test image
    image = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    return SimpleUploadedFile(
        name="test_image.jpg",
        content=buffer.read(),
        content_type="image/jpeg",
    )


# =============================================================================
# API Response Helpers
# =============================================================================


@pytest.fixture
def assert_api_success():
    """Helper to assert successful API responses."""
    def _assert(response, expected_status=200):
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}: {response.data}"
        )
        return response.data
    return _assert


@pytest.fixture
def assert_api_error():
    """Helper to assert error API responses."""
    def _assert(response, expected_status):
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}: {response.data}"
        )
        return response.data
    return _assert
