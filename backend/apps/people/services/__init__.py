"""
People app services.
"""

from .ai_parser import (
    chat_with_context,
    generate_person_summary,
    parse_contacts_text,
    parse_updates_text,
)

__all__ = [
    "chat_with_context",
    "generate_person_summary",
    "parse_contacts_text",
    "parse_updates_text",
]
