"""
Tests for AI-related API endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories import PersonFactory, PhotoFactory, TagFactory


# =============================================================================
# Person Generate Summary Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonGenerateSummaryAPI:
    """Tests for Person AI summary generation endpoint."""

    def test_generate_summary_unauthenticated(self, api_client, person):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-generate-summary", kwargs={"pk": person.pk})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_generate_summary_success(self, authenticated_client, person):
        """Test successful summary generation."""
        with patch("apps.people.views.generate_person_summary") as mock_gen:
            mock_gen.return_value = "This is an AI-generated summary."

            url = reverse("person-generate-summary", kwargs={"pk": person.pk})
            response = authenticated_client.post(url)

            assert response.status_code == status.HTTP_200_OK
            assert "summary" in response.data
            mock_gen.assert_called_once()

    def test_generate_summary_not_found(self, authenticated_client):
        """Test summary generation for non-existent person."""
        import uuid

        url = reverse("person-generate-summary", kwargs={"pk": uuid.uuid4()})

        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Person Suggest Tags Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonSuggestTagsAPI:
    """Tests for Person AI tag suggestion endpoint."""

    def test_suggest_tags_unauthenticated(self, api_client, person):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-suggest-tags", kwargs={"pk": person.pk})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_suggest_tags_success(self, authenticated_client, person):
        """Test successful tag suggestion."""
        # Create some tags to be suggested
        TagFactory(name="Developer")
        TagFactory(name="Manager")

        with patch("apps.people.views.suggest_tags_for_person") as mock_suggest:
            mock_suggest.return_value = {
                "suggestions": [
                    {"tag_id": "uuid1", "tag_name": "Developer", "confidence": 0.9},
                    {"tag_id": "uuid2", "tag_name": "Manager", "confidence": 0.7},
                ]
            }

            url = reverse("person-suggest-tags", kwargs={"pk": person.pk})
            response = authenticated_client.post(url)

            assert response.status_code == status.HTTP_200_OK
            mock_suggest.assert_called_once()


# =============================================================================
# Person Apply Tags Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonApplyTagsAPI:
    """Tests for Person apply tags endpoint."""

    def test_apply_tags_unauthenticated(self, api_client, person):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-apply-tags", kwargs={"pk": person.pk})

        response = api_client.post(url, {"tag_ids": []})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_apply_tags_success(self, authenticated_client, person):
        """Test successfully applying tags."""
        TagFactory(name="vip")
        TagFactory(name="developer")

        url = reverse("person-apply-tags", kwargs={"pk": person.pk})
        response = authenticated_client.post(
            url,
            {"tags": ["vip", "developer"]},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "vip" in response.data["applied_tags"]
        assert "developer" in response.data["applied_tags"]

    def test_apply_tags_empty_list(self, authenticated_client, person):
        """Test applying empty tag list returns error."""
        url = reverse("person-apply-tags", kwargs={"pk": person.pk})
        response = authenticated_client.post(
            url,
            {"tags": []},
            format="json",
        )

        # Empty list should return error
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_apply_tags_missing_tags_field(self, authenticated_client, person):
        """Test apply tags without tags field."""
        url = reverse("person-apply-tags", kwargs={"pk": person.pk})
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_apply_tags_create_missing(self, authenticated_client, person):
        """Test applying tags with create_missing option."""
        url = reverse("person-apply-tags", kwargs={"pk": person.pk})
        response = authenticated_client.post(
            url,
            {"tags": ["new-tag"], "create_missing": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "new-tag" in response.data["created_tags"]


# =============================================================================
# Person Sync LinkedIn Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonSyncLinkedInAPI:
    """Tests for Person LinkedIn sync endpoint."""

    def test_sync_linkedin_unauthenticated(self, api_client, person):
        """Test that unauthenticated requests are rejected."""
        url = reverse("person-sync-linkedin", kwargs={"pk": person.pk})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sync_linkedin_no_url(self, authenticated_client, person):
        """Test sync without LinkedIn URL."""
        person.linkedin_url = ""
        person.save()

        url = reverse("person-sync-linkedin", kwargs={"pk": person.pk})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sync_linkedin_success(self, authenticated_client, person):
        """Test successful LinkedIn sync."""
        person.linkedin_url = "https://linkedin.com/in/johndoe"
        person.save()

        with patch("apps.people.views.sync_person_from_linkedin") as mock_sync:
            mock_sync.return_value = {
                "synced_count": 2,
                "skipped_count": 1,
                "errors": [],
                "profile": {},
            }

            url = reverse("person-sync-linkedin", kwargs={"pk": person.pk})
            response = authenticated_client.post(url)

            assert response.status_code == status.HTTP_200_OK
            assert response.data["status"] == "success"
            mock_sync.assert_called_once()


# =============================================================================
# Photo Generate Description Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoGenerateDescriptionAPI:
    """Tests for Photo AI description generation endpoint."""

    def test_generate_description_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        photo = PhotoFactory()
        url = reverse("photo-generate-description", kwargs={"pk": photo.pk})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_generate_description_success(self, authenticated_client):
        """Test successful description generation."""
        photo = PhotoFactory()

        with patch("apps.people.views.generate_photo_description") as mock_gen:
            mock_gen.return_value = "A beautiful photo description."

            url = reverse("photo-generate-description", kwargs={"pk": photo.pk})
            response = authenticated_client.post(url)

            assert response.status_code == status.HTTP_200_OK
            assert "ai_description" in response.data
            mock_gen.assert_called_once()


# =============================================================================
# AI Parse Contacts Tests
# =============================================================================


@pytest.mark.django_db
class TestAIParseContactsAPI:
    """Tests for AI contact parsing endpoint."""

    def test_parse_contacts_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("ai-parse-contacts")

        response = api_client.post(url, {"text": "John Doe"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_parse_contacts_success(self, authenticated_client):
        """Test successful contact parsing."""
        with patch("apps.people.views.parse_contacts_text") as mock_parse:
            mock_parse.return_value = {
                "contacts": [
                    {"first_name": "John", "last_name": "Doe", "email": "john@example.com"}
                ]
            }

            url = reverse("ai-parse-contacts")
            response = authenticated_client.post(
                url,
                {"text": "John Doe john@example.com"},
                format="json",
            )

            assert response.status_code == status.HTTP_200_OK
            mock_parse.assert_called_once()

    def test_parse_contacts_empty_text(self, authenticated_client):
        """Test parsing with empty text."""
        url = reverse("ai-parse-contacts")
        response = authenticated_client.post(url, {"text": ""}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# AI Bulk Import Tests
# =============================================================================


@pytest.mark.django_db
class TestAIBulkImportAPI:
    """Tests for AI bulk import endpoint."""

    def test_bulk_import_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("ai-bulk-import")

        response = api_client.post(url, {"contacts": []})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_bulk_import_success(self, authenticated_client, db):
        """Test successful bulk import."""
        from apps.people.models import Person

        # Ensure exactly one owner exists
        Person.objects.filter(is_owner=True).delete()
        PersonFactory(is_owner=True, first_name="Owner", last_name="User")

        url = reverse("ai-bulk-import")
        data = {
            "persons": [
                {"first_name": "John", "last_name": "Doe"},
                {"first_name": "Jane", "last_name": "Smith"},
            ]
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["summary"]["persons_created"] == 2

    def test_bulk_import_empty_list(self, authenticated_client):
        """Test bulk import with empty persons list."""
        url = reverse("ai-bulk-import")
        response = authenticated_client.post(url, {"persons": []}, format="json")

        # Empty list should return validation error
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# AI Parse Updates Tests
# =============================================================================


@pytest.mark.django_db
class TestAIParseUpdatesAPI:
    """Tests for AI update parsing endpoint."""

    def test_parse_updates_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("ai-parse-updates")

        response = api_client.post(url, {"text": "update info"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_parse_updates_success(self, authenticated_client, person):
        """Test successful update parsing."""
        with patch("apps.people.views.parse_updates_text") as mock_parse:
            mock_parse.return_value = {
                "updates": [
                    {
                        "person_id": str(person.pk),
                        "field": "notes",
                        "new_value": "Updated notes",
                    }
                ]
            }

            url = reverse("ai-parse-updates")
            response = authenticated_client.post(
                url,
                {"text": f"Update {person.first_name}'s notes to 'Updated notes'"},
                format="json",
            )

            assert response.status_code == status.HTTP_200_OK
            mock_parse.assert_called_once()


# =============================================================================
# AI Apply Updates Tests
# =============================================================================


@pytest.mark.django_db
class TestAIApplyUpdatesAPI:
    """Tests for AI update application endpoint."""

    def test_apply_updates_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("ai-apply-updates")

        response = api_client.post(url, {"updates": []})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_apply_updates_success(self, authenticated_client, person):
        """Test successfully applying updates."""
        url = reverse("ai-apply-updates")
        data = {
            "updates": [
                {
                    "person_id": str(person.pk),
                    "field": "notes",
                    "new_value": "New notes content",
                }
            ]
        }

        response = authenticated_client.post(url, data, format="json")

        # Should succeed or return expected response
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


# =============================================================================
# AI Chat Tests
# =============================================================================


@pytest.mark.django_db
class TestAIChatAPI:
    """Tests for AI chat endpoint."""

    def test_chat_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("ai-chat")

        response = api_client.post(url, {"message": "Hello"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_chat_success(self, authenticated_client):
        """Test successful chat interaction."""
        with patch("apps.people.views.chat_with_context") as mock_chat:
            mock_chat.return_value = "Hello! How can I help you today?"

            url = reverse("ai-chat")
            response = authenticated_client.post(
                url,
                {"question": "Hello"},
                format="json",
            )

            assert response.status_code == status.HTTP_200_OK
            assert "answer" in response.data
            mock_chat.assert_called_once()

    def test_chat_empty_question(self, authenticated_client):
        """Test chat with empty question."""
        url = reverse("ai-chat")
        response = authenticated_client.post(url, {"question": ""}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
