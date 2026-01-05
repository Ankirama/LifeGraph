"""
Custom exceptions for the people app.

These provide more specific error handling and cleaner API responses.
DRF automatically converts these exceptions to appropriate HTTP responses.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


# =============================================================================
# AI Service Exceptions
# =============================================================================


class AIServiceError(APIException):
    """Raised when AI service (OpenAI) fails."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "AI service is temporarily unavailable."
    default_code = "ai_service_error"


class AIRateLimitError(AIServiceError):
    """Raised when AI rate limit is exceeded."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "AI rate limit exceeded. Please try again later."
    default_code = "ai_rate_limit"


class AIParsingError(AIServiceError):
    """Raised when AI response cannot be parsed."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Failed to parse AI response."
    default_code = "ai_parsing_error"


class AIConfigurationError(AIServiceError):
    """Raised when AI service is not configured."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "AI service is not configured. Please set OPENAI_API_KEY."
    default_code = "ai_not_configured"


# =============================================================================
# LinkedIn Service Exceptions
# =============================================================================


class LinkedInServiceError(APIException):
    """Raised when LinkedIn integration fails."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "LinkedIn service is temporarily unavailable."
    default_code = "linkedin_service_error"


class LinkedInAuthError(LinkedInServiceError):
    """Raised when LinkedIn authentication fails."""

    default_detail = "LinkedIn authentication failed. Check credentials."
    default_code = "linkedin_auth_error"


class LinkedInProfileError(LinkedInServiceError):
    """Raised when LinkedIn profile cannot be fetched."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "LinkedIn profile not found or inaccessible."
    default_code = "linkedin_profile_not_found"


# =============================================================================
# Person Exceptions
# =============================================================================


class PersonNotFoundError(APIException):
    """Raised when a person is not found."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Person not found."
    default_code = "person_not_found"


class OwnerNotFoundError(APIException):
    """Raised when the owner person is not configured."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Owner profile not configured. Please set up your profile first."
    default_code = "owner_not_found"


# =============================================================================
# Relationship Exceptions
# =============================================================================


class RelationshipTypeNotFoundError(APIException):
    """Raised when a relationship type is not found."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Relationship type not found."
    default_code = "relationship_type_not_found"


class DuplicateRelationshipError(APIException):
    """Raised when attempting to create a duplicate relationship."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This relationship already exists."
    default_code = "duplicate_relationship"


# =============================================================================
# Export Exceptions
# =============================================================================


class ExportError(APIException):
    """Raised when data export fails."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Failed to export data."
    default_code = "export_error"


class InvalidExportFormatError(APIException):
    """Raised when an invalid export format is requested."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid export format. Supported formats: json, csv."
    default_code = "invalid_export_format"
