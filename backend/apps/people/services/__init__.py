"""
People app services.
"""

from .ai_parser import (
    chat_with_context,
    generate_person_summary,
    generate_photo_description,
    parse_contacts_text,
    parse_updates_text,
    smart_search,
    suggest_relationships,
    suggest_tags_for_person,
)
from .linkedin import (
    extract_username_from_url,
    fetch_linkedin_profile,
    sync_person_from_linkedin,
)

__all__ = [
    # AI Services
    "chat_with_context",
    "generate_person_summary",
    "generate_photo_description",
    "parse_contacts_text",
    "parse_updates_text",
    "smart_search",
    "suggest_relationships",
    "suggest_tags_for_person",
    # LinkedIn Services
    "extract_username_from_url",
    "fetch_linkedin_profile",
    "sync_person_from_linkedin",
]
