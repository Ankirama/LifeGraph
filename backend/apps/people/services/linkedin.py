"""
LinkedIn integration service for fetching profile data.

WARNING: This uses the unofficial linkedin-api library which scrapes LinkedIn.
Use sparingly to avoid rate limiting or account restrictions.
Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables.
"""

import logging
import re
from datetime import date
from typing import TypedDict

from django.conf import settings

logger = logging.getLogger(__name__)


class LinkedInExperience(TypedDict):
    """Structured employment data from LinkedIn."""

    company: str
    title: str
    location: str
    start_date: date | None
    end_date: date | None
    is_current: bool
    description: str


class LinkedInProfile(TypedDict):
    """Structured profile data from LinkedIn."""

    public_id: str
    first_name: str
    last_name: str
    headline: str
    summary: str
    location: str
    experiences: list[LinkedInExperience]


def get_linkedin_client():
    """
    Get an authenticated LinkedIn API client.

    Returns:
        Linkedin: Authenticated client

    Raises:
        ValueError: If credentials are not configured
        Exception: If authentication fails
    """
    from linkedin_api import Linkedin

    email = getattr(settings, "LINKEDIN_EMAIL", None)
    password = getattr(settings, "LINKEDIN_PASSWORD", None)

    if not email or not password:
        raise ValueError(
            "LinkedIn credentials not configured. "
            "Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment."
        )

    try:
        client = Linkedin(email, password)
        logger.info("LinkedIn client authenticated successfully")
        return client
    except Exception as e:
        logger.error(f"LinkedIn authentication failed: {e}")
        raise


def extract_username_from_url(linkedin_url: str) -> str | None:
    """
    Extract the LinkedIn username/public_id from a LinkedIn profile URL.

    Args:
        linkedin_url: Full LinkedIn profile URL

    Returns:
        Username/public_id or None if not parseable

    Examples:
        https://www.linkedin.com/in/johndoe/ -> johndoe
        https://linkedin.com/in/jane-smith-123abc/ -> jane-smith-123abc
    """
    if not linkedin_url:
        return None

    # Match various LinkedIn URL formats
    patterns = [
        r"linkedin\.com/in/([^/\?]+)",
        r"linkedin\.com/pub/([^/\?]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, linkedin_url, re.IGNORECASE)
        if match:
            return match.group(1).rstrip("/")

    return None


def parse_linkedin_date(date_dict: dict | None) -> date | None:
    """
    Parse LinkedIn date format to Python date.

    LinkedIn returns dates like: {"month": 3, "year": 2020}

    Args:
        date_dict: LinkedIn date dictionary

    Returns:
        Python date object or None
    """
    if not date_dict:
        return None

    year = date_dict.get("year")
    month = date_dict.get("month", 1)

    if not year:
        return None

    try:
        return date(year=year, month=month, day=1)
    except (ValueError, TypeError):
        return None


def fetch_linkedin_profile(linkedin_url: str) -> LinkedInProfile | None:
    """
    Fetch profile data from LinkedIn.

    Args:
        linkedin_url: LinkedIn profile URL

    Returns:
        LinkedInProfile with structured data or None if fetch fails

    Raises:
        ValueError: If URL is invalid or credentials not configured
    """
    username = extract_username_from_url(linkedin_url)
    if not username:
        raise ValueError(f"Could not extract username from URL: {linkedin_url}")

    client = get_linkedin_client()

    try:
        profile = client.get_profile(username)
        logger.info(f"Fetched LinkedIn profile for {username}")
    except Exception as e:
        logger.error(f"Failed to fetch LinkedIn profile for {username}: {e}")
        return None

    # Parse experiences
    experiences: list[LinkedInExperience] = []
    for exp in profile.get("experience", []):
        # Handle company name - can be nested
        company_name = exp.get("companyName", "")
        if not company_name and "company" in exp:
            company_name = exp["company"].get("name", "")

        # Parse dates
        time_period = exp.get("timePeriod", {})
        start_date = parse_linkedin_date(time_period.get("startDate"))
        end_date = parse_linkedin_date(time_period.get("endDate"))

        experiences.append(
            LinkedInExperience(
                company=company_name,
                title=exp.get("title", ""),
                location=exp.get("locationName", "") or exp.get("geoLocationName", ""),
                start_date=start_date,
                end_date=end_date,
                is_current=end_date is None and start_date is not None,
                description=exp.get("description", "") or "",
            )
        )

    return LinkedInProfile(
        public_id=username,
        first_name=profile.get("firstName", ""),
        last_name=profile.get("lastName", ""),
        headline=profile.get("headline", ""),
        summary=profile.get("summary", ""),
        location=profile.get("locationName", "") or profile.get("geoLocationName", ""),
        experiences=experiences,
    )


def sync_person_from_linkedin(person, create_missing: bool = True) -> dict:
    """
    Sync a person's employment data from their LinkedIn profile.

    Args:
        person: Person model instance with linkedin_url set
        create_missing: If True, create new Employment records for missing jobs

    Returns:
        Dict with sync results:
        - synced_count: Number of employment records updated/created
        - skipped_count: Number of LinkedIn jobs not synced
        - errors: List of error messages
    """
    from django.utils import timezone

    from ..models import Employment

    if not person.linkedin_url:
        return {
            "synced_count": 0,
            "skipped_count": 0,
            "errors": ["Person has no LinkedIn URL"],
        }

    try:
        profile = fetch_linkedin_profile(person.linkedin_url)
    except ValueError as e:
        return {"synced_count": 0, "skipped_count": 0, "errors": [str(e)]}

    if not profile:
        return {
            "synced_count": 0,
            "skipped_count": 0,
            "errors": ["Failed to fetch LinkedIn profile"],
        }

    synced_count = 0
    skipped_count = 0
    errors = []

    for exp in profile["experiences"]:
        if not exp["company"] or not exp["title"]:
            skipped_count += 1
            continue

        try:
            # Try to find existing employment by company + title
            employment, created = Employment.objects.update_or_create(
                person=person,
                company=exp["company"],
                title=exp["title"],
                defaults={
                    "location": exp["location"],
                    "start_date": exp["start_date"],
                    "end_date": exp["end_date"],
                    "is_current": exp["is_current"],
                    "description": exp["description"],
                    "linkedin_synced": True,
                    "linkedin_last_sync": timezone.now(),
                },
            )
            synced_count += 1
            logger.debug(
                f"{'Created' if created else 'Updated'} employment: {exp['title']} at {exp['company']}"
            )
        except Exception as e:
            errors.append(f"Failed to sync {exp['title']} at {exp['company']}: {e}")
            logger.error(f"Error syncing employment: {e}")

    return {
        "synced_count": synced_count,
        "skipped_count": skipped_count,
        "errors": errors,
        "profile": {
            "name": f"{profile['first_name']} {profile['last_name']}",
            "headline": profile["headline"],
            "experiences_count": len(profile["experiences"]),
        },
    }
