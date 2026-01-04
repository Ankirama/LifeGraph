"""
Tests for AI Parser service functions.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from apps.people.services.ai_parser import (
    chat_with_context,
    generate_person_summary,
    generate_photo_description,
    get_openai_client,
    parse_contacts_text,
    parse_updates_text,
    suggest_tags_for_person,
)
from tests.factories import PersonFactory, PhotoFactory, TagFactory


# =============================================================================
# get_openai_client Tests
# =============================================================================


class TestGetOpenAIClient:
    """Tests for get_openai_client function."""

    def test_returns_client_when_key_configured(self, settings):
        """Test that client is returned when API key is set."""
        settings.OPENAI_API_KEY = "test-api-key"

        with patch("apps.people.services.ai_parser.OpenAI") as mock_openai:
            client = get_openai_client()

            mock_openai.assert_called_once_with(api_key="test-api-key")

    def test_raises_when_key_missing(self, settings):
        """Test that ValueError is raised when API key is not set."""
        settings.OPENAI_API_KEY = None

        with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
            get_openai_client()

    def test_raises_when_key_empty(self, settings):
        """Test that ValueError is raised when API key is empty."""
        settings.OPENAI_API_KEY = ""

        with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
            get_openai_client()


# =============================================================================
# parse_contacts_text Tests
# =============================================================================


class TestParseContactsText:
    """Tests for parse_contacts_text function."""

    def test_parse_contacts_success(self, mock_openai):
        """Test successful contact parsing."""
        mock_response = {
            "persons": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ]
        }
        mock_openai.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)

        result = parse_contacts_text("John Doe - john@example.com")

        assert result is not None
        assert "persons" in result
        assert len(result["persons"]) == 1
        assert result["persons"][0]["first_name"] == "John"

    def test_parse_contacts_multiple(self, mock_openai):
        """Test parsing multiple contacts."""
        mock_response = {
            "persons": [
                {"first_name": "Alice", "last_name": "Smith"},
                {"first_name": "Bob", "last_name": "Jones"},
            ]
        }
        mock_openai.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)

        result = parse_contacts_text("Alice Smith, Bob Jones")

        assert result is not None
        assert len(result["persons"]) == 2

    def test_parse_contacts_empty_text(self, mock_openai):
        """Test parsing empty text."""
        mock_openai.chat.completions.create.return_value.choices[0].message.content = '{"persons": []}'

        result = parse_contacts_text("")

        assert result == {"persons": []}

    def test_parse_contacts_api_error(self, mock_openai):
        """Test handling of API errors."""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            parse_contacts_text("John Doe")

    def test_parse_contacts_invalid_json(self, mock_openai):
        """Test handling of invalid JSON response."""
        mock_openai.chat.completions.create.return_value.choices[0].message.content = "not valid json"

        with pytest.raises(ValueError, match="Failed to parse AI response"):
            parse_contacts_text("John Doe")


# =============================================================================
# parse_updates_text Tests
# =============================================================================


class TestParseUpdatesText:
    """Tests for parse_updates_text function."""

    def test_parse_updates_success(self, mock_openai):
        """Test successful update parsing."""
        mock_response = {
            "updates": [
                {
                    "match_type": "name",
                    "match_value": "John Doe",
                    "matched_person_id": "uuid-123",
                    "matched_person_name": "John Doe",
                    "field_updates": {"notes_to_append": "Got promoted"},
                    "anecdotes": [],
                }
            ]
        }
        mock_openai.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)

        existing_contacts = [
            {"id": "uuid-123", "full_name": "John Doe", "relationship_to_me": "friend"}
        ]

        result = parse_updates_text("John got promoted to senior engineer", existing_contacts)

        assert result is not None
        assert "updates" in result
        assert len(result["updates"]) == 1

    def test_parse_updates_multiple(self, mock_openai):
        """Test parsing multiple updates."""
        mock_response = {
            "updates": [
                {
                    "match_type": "name",
                    "match_value": "Alice",
                    "field_updates": {"notes_to_append": "New job"},
                    "anecdotes": [],
                },
                {
                    "match_type": "name",
                    "match_value": "Bob",
                    "field_updates": {"birthday": "1990-05-15"},
                    "anecdotes": [],
                },
            ]
        }
        mock_openai.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)

        existing_contacts = [
            {"id": "uuid-1", "full_name": "Alice Smith"},
            {"id": "uuid-2", "full_name": "Bob Jones"},
        ]

        result = parse_updates_text("Alice got new job, Bob's birthday is May 15, 1990", existing_contacts)

        assert result is not None
        assert len(result["updates"]) == 2

    def test_parse_updates_api_error(self, mock_openai):
        """Test handling of API errors."""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            parse_updates_text("Update text", [])


# =============================================================================
# generate_person_summary Tests
# =============================================================================


class TestGeneratePersonSummary:
    """Tests for generate_person_summary function."""

    def test_generate_summary_success(self, mock_openai):
        """Test successful summary generation."""
        mock_openai.chat.completions.create.return_value.choices[0].message.content = (
            "John Doe is a software engineer with expertise in Python."
        )

        person_data = {
            "first_name": "John",
            "last_name": "Doe",
            "notes": "Works in Python development",
            "relationships": [],
            "anecdotes": [],
            "employments": [],
        }

        result = generate_person_summary(person_data)

        assert result is not None
        assert "John Doe" in result

    def test_generate_summary_with_relationships(self, mock_openai):
        """Test summary generation includes relationship context."""
        mock_openai.chat.completions.create.return_value.choices[0].message.content = (
            "John is a friend who works at TechCorp."
        )

        person_data = {
            "first_name": "John",
            "last_name": "Doe",
            "relationships": [{"type": "friend", "with": "Me"}],
            "anecdotes": [],
            "employments": [{"company": "TechCorp", "title": "Engineer"}],
        }

        result = generate_person_summary(person_data)

        assert result is not None
        assert "TechCorp" in result

    def test_generate_summary_api_error(self, mock_openai):
        """Test handling of API errors."""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            generate_person_summary({"first_name": "John"})


# =============================================================================
# suggest_tags_for_person Tests
# =============================================================================


class TestSuggestTagsForPerson:
    """Tests for suggest_tags_for_person function."""

    def test_suggest_tags_success(self, mock_openai):
        """Test successful tag suggestion."""
        mock_response = {
            "suggested_tags": [
                {"name": "developer", "confidence": 0.9, "reason": "Works in tech"},
                {"name": "python", "confidence": 0.85, "reason": "Python developer"},
            ]
        }
        mock_openai.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)

        person_data = {
            "profile": {
                "full_name": "John Doe",
                "notes": "Python developer at TechCorp",
            },
            "relationships": [],
            "anecdotes": [],
            "employments": [],
        }
        existing_tags = ["tech", "friend"]

        result = suggest_tags_for_person(person_data, existing_tags)

        assert result is not None
        assert len(result) == 2

    def test_suggest_tags_with_existing_tags(self, mock_openai):
        """Test suggestion considers existing tags."""
        mock_response = {
            "suggested_tags": [
                {"name": "senior", "confidence": 0.8, "reason": "Senior position"},
            ]
        }
        mock_openai.chat.completions.create.return_value.choices[0].message.content = json.dumps(mock_response)

        person_data = {
            "profile": {"full_name": "John Doe", "notes": "Senior developer"},
            "relationships": [],
            "anecdotes": [],
            "employments": [],
        }
        existing_tags = ["developer", "python"]

        result = suggest_tags_for_person(person_data, existing_tags)

        assert result is not None
        assert len(result) == 1

    def test_suggest_tags_invalid_json(self, mock_openai):
        """Test handling of invalid JSON response."""
        mock_openai.chat.completions.create.return_value.choices[0].message.content = "not valid json"

        with pytest.raises(ValueError):
            suggest_tags_for_person({"profile": {}}, [])


# =============================================================================
# generate_photo_description Tests
# =============================================================================


class TestGeneratePhotoDescription:
    """Tests for generate_photo_description function."""

    def test_generate_description_success(self, mock_openai_vision):
        """Test successful photo description generation."""
        result = generate_photo_description("https://example.com/photo.jpg")

        assert result is not None
        assert "photo" in result.lower()

    def test_generate_description_api_error(self, mock_openai):
        """Test handling of API errors."""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            generate_photo_description("https://example.com/photo.jpg")


# =============================================================================
# chat_with_context Tests
# =============================================================================


class TestChatWithContext:
    """Tests for chat_with_context function."""

    def test_chat_success(self, mock_openai):
        """Test successful chat response."""
        mock_openai.chat.completions.create.return_value.choices[0].message.content = (
            "Based on your contacts, John works at TechCorp as an engineer."
        )

        contacts_context = "John Doe - Engineer at TechCorp"
        today_date = "2025-01-04"

        result = chat_with_context("Where does John work?", contacts_context, today_date)

        assert result is not None
        assert "TechCorp" in result

    def test_chat_with_empty_context(self, mock_openai):
        """Test chat with empty context."""
        mock_openai.chat.completions.create.return_value.choices[0].message.content = (
            "I don't have any contact information to answer that question."
        )

        result = chat_with_context("Who is John?", "", "2025-01-04")

        assert result is not None

    def test_chat_with_conversation_history(self, mock_openai):
        """Test chat with conversation history."""
        mock_openai.chat.completions.create.return_value.choices[0].message.content = (
            "Yes, John is still at TechCorp."
        )

        contacts_context = "John Doe - Engineer at TechCorp"
        conversation_history = [
            {"role": "user", "content": "Where does John work?"},
            {"role": "assistant", "content": "John works at TechCorp."},
        ]

        result = chat_with_context(
            "Is he still there?",
            contacts_context,
            "2025-01-04",
            conversation_history=conversation_history,
        )

        assert result is not None

    def test_chat_api_error(self, mock_openai):
        """Test handling of API errors."""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            chat_with_context("Hello", "", "2025-01-04")
