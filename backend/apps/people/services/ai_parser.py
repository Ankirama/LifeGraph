"""
AI-powered contact parsing service using OpenAI.
"""

import json
import logging
from typing import Any

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """Get configured OpenAI client."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=api_key)


SYSTEM_PROMPT = """You are an assistant that extracts structured contact information from natural language text.

The user will describe people and their relationships to themselves (the CRM owner).

Extract each person mentioned with their details and their relationship to the user.

Return a JSON object with the following structure:
{
  "persons": [
    {
      "first_name": "string (required)",
      "last_name": "string (optional, empty string if not provided)",
      "nickname": "string (optional)",
      "birthday": "YYYY-MM-DD or null if not provided",
      "notes": "any additional information mentioned",
      "relationship_to_owner": "the relationship type from the owner's perspective (e.g., 'mother', 'father', 'sister', 'brother', 'friend', 'colleague', 'wife', 'husband', etc.)"
    }
  ]
}

Rules:
1. Extract ALL persons mentioned
2. relationship_to_owner should be what that person IS to the user (e.g., if user says "my mother is X", relationship_to_owner is "mother")
3. For birthdays, try to parse any date format into YYYY-MM-DD
4. If only a partial date is given (e.g., "born in March"), put that info in notes instead
5. Include any extra details (job, location, how they met, etc.) in the notes field
6. Be consistent with relationship names: use lowercase singular forms (mother, father, sister, brother, aunt, uncle, cousin, friend, colleague, wife, husband, girlfriend, boyfriend, etc.)

Respond ONLY with valid JSON, no other text."""


def parse_contacts_text(text: str) -> dict[str, Any]:
    """
    Parse natural language text describing contacts into structured data.

    Args:
        text: Natural language description of contacts and relationships

    Returns:
        Dictionary with 'persons' list containing extracted contact data
    """
    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.1,  # Low temperature for more consistent parsing
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate structure
        if "persons" not in result:
            result = {"persons": []}

        # Clean up and validate each person
        cleaned_persons = []
        for person in result.get("persons", []):
            if not person.get("first_name"):
                continue  # Skip entries without a first name

            cleaned_person = {
                "first_name": person.get("first_name", "").strip(),
                "last_name": person.get("last_name", "").strip() if person.get("last_name") else "",
                "nickname": person.get("nickname", "").strip() if person.get("nickname") else "",
                "birthday": person.get("birthday") if person.get("birthday") else None,
                "notes": person.get("notes", "").strip() if person.get("notes") else "",
                "relationship_to_owner": person.get("relationship_to_owner", "").strip().lower() if person.get("relationship_to_owner") else "",
            }
            cleaned_persons.append(cleaned_person)

        return {"persons": cleaned_persons}

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        raise ValueError("Failed to parse AI response")
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise


UPDATE_SYSTEM_PROMPT = """You are an assistant that extracts updates and memories about existing contacts from natural language text.

The user will describe updates or memories about people they already know. You will be given a list of existing contacts with their names and relationships.

Your task is to:
1. Identify which existing person(s) the user is referring to
2. Extract any updates to their information (birthday, notes, etc.)
3. Extract any memories/anecdotes mentioned

Return a JSON object with the following structure:
{
  "updates": [
    {
      "match_type": "relationship" or "name",
      "match_value": "the relationship or name used to identify the person (e.g., 'mother', 'Pierre')",
      "matched_person_id": "UUID of the matched person from the existing contacts list, or null if no match",
      "matched_person_name": "Full name of the matched person, or null if no match",
      "field_updates": {
        "birthday": "YYYY-MM-DD or null if not mentioned",
        "nickname": "string or null if not mentioned",
        "notes_to_append": "any new information to add to notes, or null"
      },
      "anecdotes": [
        {
          "content": "the memory or story content",
          "title": "optional short title for the anecdote",
          "anecdote_type": "memory" or "quote" or "joke" or "note",
          "date": "YYYY-MM-DD if a date is mentioned, otherwise null",
          "location": "location if mentioned, otherwise empty string"
        }
      ]
    }
  ]
}

Rules:
1. Match people by relationship (e.g., "my mom" -> relationship "mother") or by name
2. If a person cannot be matched to an existing contact, still include them but with matched_person_id as null
3. For birthdays, parse any date format into YYYY-MM-DD. If only partial (e.g., "born in March"), put in notes_to_append instead
4. Memories, stories, things they said, events you shared should become anecdotes
5. Factual updates (birthday, job, location) go in field_updates
6. anecdote_type should be: "memory" for shared experiences, "quote" for things they said, "joke" for funny moments, "note" for general observations
7. A single input can have multiple updates for different people
8. A single person can have both field_updates AND anecdotes

Respond ONLY with valid JSON, no other text."""


def parse_updates_text(text: str, existing_contacts: list[dict]) -> dict[str, Any]:
    """
    Parse natural language text describing updates to existing contacts.

    Args:
        text: Natural language description of updates/memories
        existing_contacts: List of existing contacts with id, full_name, relationship_to_me

    Returns:
        Dictionary with 'updates' list containing parsed update data
    """
    client = get_openai_client()

    # Build context about existing contacts
    contacts_context = "Existing contacts:\n"
    for contact in existing_contacts:
        rel = contact.get("relationship_to_me", "")
        rel_str = f" (relationship: {rel})" if rel else ""
        contacts_context += f"- ID: {contact['id']}, Name: {contact['full_name']}{rel_str}\n"

    if not existing_contacts:
        contacts_context = "No existing contacts in the system.\n"

    user_message = f"{contacts_context}\nUser input:\n{text}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": UPDATE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate structure
        if "updates" not in result:
            result = {"updates": []}

        # Clean up and validate each update
        cleaned_updates = []
        for update in result.get("updates", []):
            cleaned_update = {
                "match_type": update.get("match_type", "name"),
                "match_value": update.get("match_value", ""),
                "matched_person_id": update.get("matched_person_id"),
                "matched_person_name": update.get("matched_person_name"),
                "field_updates": {},
                "anecdotes": [],
            }

            # Clean field updates
            field_updates = update.get("field_updates", {})
            if field_updates:
                if field_updates.get("birthday"):
                    cleaned_update["field_updates"]["birthday"] = field_updates["birthday"]
                if field_updates.get("nickname"):
                    cleaned_update["field_updates"]["nickname"] = field_updates["nickname"].strip()
                if field_updates.get("notes_to_append"):
                    cleaned_update["field_updates"]["notes_to_append"] = field_updates["notes_to_append"].strip()

            # Clean anecdotes
            for anecdote in update.get("anecdotes", []):
                if anecdote.get("content"):
                    cleaned_anecdote = {
                        "content": anecdote["content"].strip(),
                        "title": anecdote.get("title", "").strip() if anecdote.get("title") else "",
                        "anecdote_type": anecdote.get("anecdote_type", "note"),
                        "date": anecdote.get("date") if anecdote.get("date") else None,
                        "location": anecdote.get("location", "").strip() if anecdote.get("location") else "",
                    }
                    # Validate anecdote_type
                    if cleaned_anecdote["anecdote_type"] not in ["memory", "quote", "joke", "note"]:
                        cleaned_anecdote["anecdote_type"] = "note"
                    cleaned_update["anecdotes"].append(cleaned_anecdote)

            # Only include if there's something to update
            if cleaned_update["field_updates"] or cleaned_update["anecdotes"]:
                cleaned_updates.append(cleaned_update)

        return {"updates": cleaned_updates}

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        raise ValueError("Failed to parse AI response")
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise
