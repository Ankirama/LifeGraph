"""
Tests for Photo and Employment API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.people.models import Employment, Photo
from tests.factories import EmploymentFactory, PersonFactory, PhotoFactory


# =============================================================================
# Photo List Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoListAPI:
    """Tests for Photo list endpoint."""

    def test_list_photos_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("photo-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_photos(self, authenticated_client):
        """Test listing photos."""
        PhotoFactory.create_batch(3)
        url = reverse("photo-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_filter_photos_by_person(self, authenticated_client):
        """Test filtering photos by person."""
        person = PersonFactory()
        photo = PhotoFactory()
        photo.persons.add(person)
        PhotoFactory()  # Different photo

        url = reverse("photo-list")
        response = authenticated_client.get(url, {"persons": person.pk})

        assert response.status_code == status.HTTP_200_OK

    def test_filter_photos_with_location(self, authenticated_client):
        """Test filtering photos by has_location."""
        PhotoFactory(location="New York")
        PhotoFactory(location="")

        url = reverse("photo-list")
        response = authenticated_client.get(url, {"has_location": "true"})

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Photo Create Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoCreateAPI:
    """Tests for Photo create endpoint."""

    def test_create_photo(self, authenticated_client, sample_image):
        """Test creating a photo."""
        url = reverse("photo-list")

        response = authenticated_client.post(
            url,
            {"file": sample_image, "caption": "Test Photo"},
            format="multipart",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_photo_with_metadata(self, authenticated_client, sample_image):
        """Test creating a photo with metadata."""
        url = reverse("photo-list")

        response = authenticated_client.post(
            url,
            {
                "file": sample_image,
                "caption": "Vacation Photo",
                "location": "Hawaii",
                "date_taken": "2023-07-15T10:30:00Z",
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_201_CREATED


# =============================================================================
# Photo Detail Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoDetailAPI:
    """Tests for Photo detail endpoint."""

    def test_get_photo(self, authenticated_client, photo):
        """Test getting a photo detail."""
        url = reverse("photo-detail", kwargs={"pk": photo.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_update_photo_caption(self, authenticated_client, photo):
        """Test updating photo caption."""
        url = reverse("photo-detail", kwargs={"pk": photo.pk})
        data = {"caption": "Updated Caption"}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["caption"] == "Updated Caption"

    def test_update_photo_persons(self, authenticated_client, photo):
        """Test adding persons to a photo."""
        person = PersonFactory()
        url = reverse("photo-detail", kwargs={"pk": photo.pk})
        data = {"persons": [str(person.pk)]}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_delete_photo(self, authenticated_client, photo):
        """Test deleting a photo."""
        url = reverse("photo-detail", kwargs={"pk": photo.pk})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Photo.objects.filter(pk=photo.pk).exists()


# =============================================================================
# Photo Generate Description Tests
# =============================================================================


@pytest.mark.django_db
class TestPhotoGenerateDescriptionAPI:
    """Tests for Photo AI description generation."""

    def test_generate_description(self, authenticated_client, photo, mock_openai_vision):
        """Test generating AI description for a photo."""
        url = reverse("photo-generate-description", kwargs={"pk": photo.pk})

        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Employment List Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentListAPI:
    """Tests for Employment list endpoint."""

    def test_list_employments_unauthenticated(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("employment-list")

        response = api_client.get(url)

        # SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_employments(self, authenticated_client):
        """Test listing employments."""
        EmploymentFactory.create_batch(3)
        url = reverse("employment-list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_filter_employments_by_person(self, authenticated_client):
        """Test filtering employments by person."""
        person = PersonFactory()
        EmploymentFactory(person=person)
        EmploymentFactory()  # Different person

        url = reverse("employment-list")
        response = authenticated_client.get(url, {"person": person.pk})

        assert response.status_code == status.HTTP_200_OK

    def test_filter_employments_current(self, authenticated_client):
        """Test filtering current employments."""
        EmploymentFactory(is_current=True)
        EmploymentFactory(is_current=False)

        url = reverse("employment-list")
        response = authenticated_client.get(url, {"is_current": "true"})

        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Employment Create Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentCreateAPI:
    """Tests for Employment create endpoint."""

    def test_create_employment(self, authenticated_client):
        """Test creating an employment record."""
        person = PersonFactory()
        url = reverse("employment-list")
        data = {
            "person": str(person.pk),
            "company": "TechCorp",
            "title": "Software Engineer",
            "is_current": True,
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["company"] == "TechCorp"

    def test_create_employment_full(self, authenticated_client):
        """Test creating employment with all details."""
        person = PersonFactory()
        url = reverse("employment-list")
        data = {
            "person": str(person.pk),
            "company": "BigCorp",
            "title": "Senior Developer",
            "department": "Engineering",
            "start_date": "2020-01-15",
            "is_current": True,
            "location": "San Francisco",
            "description": "Building awesome products.",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_past_employment(self, authenticated_client):
        """Test creating a past employment record."""
        person = PersonFactory()
        url = reverse("employment-list")
        data = {
            "person": str(person.pk),
            "company": "OldCorp",
            "title": "Junior Developer",
            "start_date": "2018-01-01",
            "end_date": "2019-12-31",
            "is_current": False,
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_current"] is False


# =============================================================================
# Employment Detail Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentDetailAPI:
    """Tests for Employment detail endpoint."""

    def test_get_employment(self, authenticated_client, employment):
        """Test getting an employment detail."""
        url = reverse("employment-detail", kwargs={"pk": employment.pk})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_update_employment(self, authenticated_client, employment):
        """Test updating an employment."""
        url = reverse("employment-detail", kwargs={"pk": employment.pk})
        data = {
            "title": "Updated Title",
            "company": "New Company",
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"

    def test_end_current_employment(self, authenticated_client, employment):
        """Test ending a current employment."""
        url = reverse("employment-detail", kwargs={"pk": employment.pk})
        data = {
            "is_current": False,
            "end_date": "2024-01-01",
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_current"] is False

    def test_delete_employment(self, authenticated_client, employment):
        """Test deleting an employment."""
        url = reverse("employment-detail", kwargs={"pk": employment.pk})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Employment.objects.filter(pk=employment.pk).exists()


# =============================================================================
# Employment Validation Tests
# =============================================================================


@pytest.mark.django_db
class TestEmploymentValidationAPI:
    """Tests for Employment validation."""

    def test_create_employment_missing_person(self, authenticated_client):
        """Test that person is required."""
        url = reverse("employment-list")
        data = {
            "company": "TechCorp",
            "title": "Engineer",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_employment_missing_company(self, authenticated_client):
        """Test that company is required."""
        person = PersonFactory()
        url = reverse("employment-list")
        data = {
            "person": str(person.pk),
            "title": "Engineer",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_employment_missing_title(self, authenticated_client):
        """Test that title is required."""
        person = PersonFactory()
        url = reverse("employment-list")
        data = {
            "person": str(person.pk),
            "company": "TechCorp",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
