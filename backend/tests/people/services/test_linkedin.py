"""
Tests for LinkedIn service functions.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.people.services.linkedin import (
    extract_username_from_url,
    fetch_linkedin_profile,
    get_linkedin_client,
    parse_linkedin_date,
)


# =============================================================================
# extract_username_from_url Tests
# =============================================================================


class TestExtractUsernameFromUrl:
    """Tests for extract_username_from_url function."""

    def test_extract_from_standard_url(self):
        """Test extracting username from standard LinkedIn URL."""
        url = "https://linkedin.com/in/johndoe"

        result = extract_username_from_url(url)

        assert result == "johndoe"

    def test_extract_from_www_url(self):
        """Test extracting username from www LinkedIn URL."""
        url = "https://www.linkedin.com/in/johndoe"

        result = extract_username_from_url(url)

        assert result == "johndoe"

    def test_extract_with_trailing_slash(self):
        """Test extracting username with trailing slash."""
        url = "https://linkedin.com/in/johndoe/"

        result = extract_username_from_url(url)

        assert result == "johndoe"

    def test_extract_from_invalid_url(self):
        """Test handling of invalid URL."""
        url = "not-a-valid-url"

        result = extract_username_from_url(url)

        assert result is None or result == ""

    def test_extract_from_non_linkedin_url(self):
        """Test handling of non-LinkedIn URL."""
        url = "https://twitter.com/johndoe"

        result = extract_username_from_url(url)

        assert result is None or result == ""

    def test_extract_from_empty_url(self):
        """Test handling of empty URL."""
        result = extract_username_from_url("")

        assert result is None or result == ""


# =============================================================================
# parse_linkedin_date Tests
# =============================================================================


class TestParseLinkedInDate:
    """Tests for parse_linkedin_date function."""

    def test_parse_year_month(self):
        """Test parsing year and month."""
        date_dict = {"year": 2020, "month": 6}

        result = parse_linkedin_date(date_dict)

        assert result == datetime.date(2020, 6, 1)

    def test_parse_year_only(self):
        """Test parsing year only."""
        date_dict = {"year": 2019}

        result = parse_linkedin_date(date_dict)

        assert result == datetime.date(2019, 1, 1)

    def test_parse_none(self):
        """Test parsing None returns None."""
        result = parse_linkedin_date(None)

        assert result is None

    def test_parse_empty_dict(self):
        """Test parsing empty dict."""
        result = parse_linkedin_date({})

        assert result is None


# =============================================================================
# get_linkedin_client Tests
# =============================================================================


class TestGetLinkedInClient:
    """Tests for get_linkedin_client function."""

    def test_returns_client_when_credentials_configured(self, settings):
        """Test that client is returned when credentials are set."""
        settings.LINKEDIN_EMAIL = "test@example.com"
        settings.LINKEDIN_PASSWORD = "password123"

        with patch("linkedin_api.Linkedin") as mock_linkedin:
            mock_linkedin.return_value = MagicMock()
            client = get_linkedin_client()

            mock_linkedin.assert_called_once_with("test@example.com", "password123")

    def test_raises_when_email_missing(self, settings):
        """Test that ValueError is raised when email is not set."""
        settings.LINKEDIN_EMAIL = None
        settings.LINKEDIN_PASSWORD = "password123"

        with pytest.raises(ValueError, match="LinkedIn credentials not configured"):
            get_linkedin_client()

    def test_raises_when_password_missing(self, settings):
        """Test that ValueError is raised when password is not set."""
        settings.LINKEDIN_EMAIL = "test@example.com"
        settings.LINKEDIN_PASSWORD = None

        with pytest.raises(ValueError, match="LinkedIn credentials not configured"):
            get_linkedin_client()


# =============================================================================
# fetch_linkedin_profile Tests
# =============================================================================


class TestFetchLinkedInProfile:
    """Tests for fetch_linkedin_profile function."""

    def test_fetch_profile_success(self, settings):
        """Test successful profile fetch."""
        settings.LINKEDIN_EMAIL = "test@example.com"
        settings.LINKEDIN_PASSWORD = "password123"

        with patch("linkedin_api.Linkedin") as mock_linkedin:
            mock_client = MagicMock()
            mock_linkedin.return_value = mock_client
            mock_client.get_profile.return_value = {
                "firstName": "John",
                "lastName": "Doe",
                "headline": "Software Engineer",
                "summary": "Experienced developer",
                "experience": [],
            }

            result = fetch_linkedin_profile("https://linkedin.com/in/johndoe")

            assert result is not None
            assert result["first_name"] == "John"
            assert result["last_name"] == "Doe"

    def test_fetch_profile_with_experience(self, settings):
        """Test fetching profile with work experience."""
        settings.LINKEDIN_EMAIL = "test@example.com"
        settings.LINKEDIN_PASSWORD = "password123"

        with patch("linkedin_api.Linkedin") as mock_linkedin:
            mock_client = MagicMock()
            mock_linkedin.return_value = mock_client
            mock_client.get_profile.return_value = {
                "firstName": "John",
                "lastName": "Doe",
                "headline": "Software Engineer",
                "experience": [
                    {
                        "companyName": "TechCorp",
                        "title": "Engineer",
                        "timePeriod": {"startDate": {"year": 2020, "month": 1}},
                    }
                ],
            }

            result = fetch_linkedin_profile("https://linkedin.com/in/johndoe")

            assert result is not None
            assert len(result["experiences"]) == 1
            assert result["experiences"][0]["company"] == "TechCorp"

    def test_fetch_profile_invalid_url_raises(self, settings):
        """Test fetching with invalid URL raises ValueError."""
        settings.LINKEDIN_EMAIL = "test@example.com"
        settings.LINKEDIN_PASSWORD = "password123"

        with pytest.raises(ValueError, match="Could not extract username"):
            fetch_linkedin_profile("https://facebook.com/johndoe")

    def test_fetch_profile_api_error_returns_none(self, settings):
        """Test that API errors return None."""
        settings.LINKEDIN_EMAIL = "test@example.com"
        settings.LINKEDIN_PASSWORD = "password123"

        with patch("linkedin_api.Linkedin") as mock_linkedin:
            mock_client = MagicMock()
            mock_linkedin.return_value = mock_client
            mock_client.get_profile.side_effect = Exception("API Error")

            result = fetch_linkedin_profile("https://linkedin.com/in/johndoe")

            assert result is None
