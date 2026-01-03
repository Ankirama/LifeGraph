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


SUMMARY_SYSTEM_PROMPT = """You are an assistant that creates helpful, warm summaries of people in a personal CRM.

Given information about a person (profile, relationships, anecdotes, employment history), create a concise but comprehensive summary that helps the CRM owner remember and understand this person.

The summary should:
1. Start with who this person is and their relationship to the owner
2. Include key facts (birthday, occupation, how they met)
3. Highlight memorable anecdotes or quotes
4. Note any important relationships to other people in the CRM
5. Be written in a warm, personal tone (not clinical or robotic)
6. Be 2-4 paragraphs long

Write in second person ("Your mother...", "You met them...") to make it personal.
If there's limited information, acknowledge it and focus on what is known.
Support both French and English - write the summary in the same language as the majority of the input data."""


def generate_person_summary(person_data: dict[str, Any]) -> str:
    """
    Generate an AI summary for a person based on their profile and related data.

    Args:
        person_data: Dictionary containing:
            - profile: Basic person info (name, birthday, notes, etc.)
            - relationships: List of relationships with other people
            - anecdotes: List of anecdotes/memories
            - employments: Employment history

    Returns:
        Generated summary text
    """
    client = get_openai_client()

    # Build context from person data
    profile = person_data.get("profile", {})
    relationships = person_data.get("relationships", [])
    anecdotes = person_data.get("anecdotes", [])
    employments = person_data.get("employments", [])

    context_parts = []

    # Profile section
    context_parts.append("## Person Profile")
    context_parts.append(f"Name: {profile.get('full_name', 'Unknown')}")
    if profile.get("nickname"):
        context_parts.append(f"Nickname: {profile['nickname']}")
    if profile.get("birthday"):
        context_parts.append(f"Birthday: {profile['birthday']}")
    if profile.get("relationship_to_owner"):
        context_parts.append(f"Relationship to you: {profile['relationship_to_owner']}")
    if profile.get("met_date"):
        context_parts.append(f"Met on: {profile['met_date']}")
    if profile.get("met_context"):
        context_parts.append(f"How you met: {profile['met_context']}")
    if profile.get("notes"):
        context_parts.append(f"Notes: {profile['notes']}")

    # Relationships section
    if relationships:
        context_parts.append("\n## Relationships")
        for rel in relationships[:10]:  # Limit to 10
            context_parts.append(f"- {rel.get('type', 'Related to')}: {rel.get('person_name', 'Unknown')}")

    # Employment section
    if employments:
        context_parts.append("\n## Employment History")
        for emp in employments[:5]:  # Limit to 5
            current = " (current)" if emp.get("is_current") else ""
            context_parts.append(f"- {emp.get('title', 'Unknown')} at {emp.get('company', 'Unknown')}{current}")

    # Anecdotes section
    if anecdotes:
        context_parts.append("\n## Memories & Anecdotes")
        for anecdote in anecdotes[:10]:  # Limit to 10
            anecdote_type = anecdote.get("type", "note")
            title = anecdote.get("title", "")
            content = anecdote.get("content", "")[:500]  # Limit content length
            if title:
                context_parts.append(f"- [{anecdote_type}] {title}: {content}")
            else:
                context_parts.append(f"- [{anecdote_type}] {content}")

    context = "\n".join(context_parts)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": f"Please create a summary for this person:\n\n{context}"},
            ],
            temperature=0.7,  # Slightly creative for natural writing
            max_tokens=1000,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"OpenAI API error generating summary: {e}")
        raise


def suggest_tags_for_person(
    person_data: dict[str, Any],
    existing_tags: list[str]
) -> list[dict[str, Any]]:
    """
    Suggest relevant tags for a person based on their profile and related data.

    Args:
        person_data: Dictionary containing:
            - profile: Basic person info (name, birthday, notes, etc.)
            - relationships: List of relationships with other people
            - anecdotes: List of anecdotes/memories
            - employments: Employment history
        existing_tags: List of existing tag names in the system

    Returns:
        List of suggested tags with name, reason, confidence, and is_existing
    """
    client = get_openai_client()

    # Build context from person data (similar to summary generation)
    profile = person_data.get("profile", {})
    relationships = person_data.get("relationships", [])
    anecdotes = person_data.get("anecdotes", [])
    employments = person_data.get("employments", [])

    context_parts = []

    # Existing tags section
    context_parts.append("## Existing Tags in System")
    if existing_tags:
        context_parts.append(", ".join(existing_tags))
    else:
        context_parts.append("(No existing tags)")

    # Profile section
    context_parts.append("\n## Person Profile")
    context_parts.append(f"Name: {profile.get('full_name', 'Unknown')}")
    if profile.get("nickname"):
        context_parts.append(f"Nickname: {profile['nickname']}")
    if profile.get("birthday"):
        context_parts.append(f"Birthday: {profile['birthday']}")
    if profile.get("relationship_to_owner"):
        context_parts.append(f"Relationship to owner: {profile['relationship_to_owner']}")
    if profile.get("met_date"):
        context_parts.append(f"Met on: {profile['met_date']}")
    if profile.get("met_context"):
        context_parts.append(f"How they met: {profile['met_context']}")
    if profile.get("notes"):
        context_parts.append(f"Notes: {profile['notes']}")

    # Relationships section
    if relationships:
        context_parts.append("\n## Relationships")
        for rel in relationships[:10]:
            context_parts.append(f"- {rel.get('type', 'Related to')}: {rel.get('person_name', 'Unknown')}")

    # Employment section
    if employments:
        context_parts.append("\n## Employment History")
        for emp in employments[:5]:
            current = " (current)" if emp.get("is_current") else ""
            context_parts.append(f"- {emp.get('title', 'Unknown')} at {emp.get('company', 'Unknown')}{current}")

    # Anecdotes section
    if anecdotes:
        context_parts.append("\n## Memories & Anecdotes")
        for anecdote in anecdotes[:10]:
            anecdote_type = anecdote.get("type", "note")
            title = anecdote.get("title", "")
            content = anecdote.get("content", "")[:300]
            if title:
                context_parts.append(f"- [{anecdote_type}] {title}: {content}")
            else:
                context_parts.append(f"- [{anecdote_type}] {content}")

    context = "\n".join(context_parts)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": AUTOTAG_SYSTEM_PROMPT},
                {"role": "user", "content": f"Please suggest tags for this person:\n\n{context}"},
            ],
            temperature=0.3,  # Lower temperature for more consistent tagging
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate and clean the response
        suggested_tags = []
        existing_tags_lower = [t.lower() for t in existing_tags]

        for tag in result.get("suggested_tags", []):
            if not tag.get("name"):
                continue

            name = tag["name"].lower().strip().replace(" ", "-")
            confidence = float(tag.get("confidence", 0.5))

            # Skip low confidence tags
            if confidence < 0.5:
                continue

            suggested_tags.append({
                "name": name,
                "reason": tag.get("reason", ""),
                "confidence": confidence,
                "is_existing": name in existing_tags_lower,
            })

        # Sort by confidence (highest first)
        suggested_tags.sort(key=lambda x: x["confidence"], reverse=True)

        return suggested_tags[:10]  # Limit to top 10

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        raise ValueError("Failed to parse AI response")
    except Exception as e:
        logger.error(f"OpenAI API error suggesting tags: {e}")
        raise


AUTOTAG_SYSTEM_PROMPT = """You are an assistant that suggests relevant tags for people in a personal CRM.

Given information about a person (profile, relationships, anecdotes, employment), suggest appropriate tags that help categorize and find this person.

You will be given:
1. Existing tags in the system - prefer using these when appropriate
2. Person's data to analyze

Return a JSON object with:
{
  "suggested_tags": [
    {
      "name": "tag name (lowercase, no spaces - use hyphens)",
      "reason": "brief reason why this tag applies",
      "confidence": 0.0 to 1.0 (how confident you are this tag applies),
      "is_existing": true/false (whether this tag already exists in the system)
    }
  ]
}

Tag categories to consider:
- Profession/Industry: developer, designer, manager, entrepreneur, doctor, teacher, etc.
- Relationship context: work-friend, childhood-friend, family, neighbor, etc.
- Interests/Hobbies: music, sports, cooking, travel, gaming, etc.
- Location: paris, remote, expatriate, etc.
- Life stage: parent, student, retired, etc.
- Personality traits: creative, analytical, outgoing, etc.
- How you met: conference, online, mutual-friend, etc.

Rules:
1. Suggest 3-10 tags, ordered by confidence (highest first)
2. Prefer existing tags when they fit
3. Only suggest new tags if no existing tag is appropriate
4. Tag names should be lowercase with hyphens (e.g., "software-developer")
5. Be conservative - only suggest tags with reasonable confidence (>0.5)
6. Consider ALL available data: profile, relationships, anecdotes, employment

Respond ONLY with valid JSON, no other text."""


PHOTO_DESCRIPTION_SYSTEM_PROMPT = """You are an assistant that describes photos in a personal CRM context.

Your task is to describe what you see in the photo, focusing on:
1. People visible (describe them without naming - the user will tag who they are)
2. The setting/location (indoor, outdoor, restaurant, beach, office, etc.)
3. The activity or occasion (celebration, casual gathering, work event, vacation, etc.)
4. Notable details (decorations, landmarks, weather, mood)
5. Approximate time context if visible (season, time of day)

Guidelines:
- Be descriptive but concise (2-4 sentences)
- Focus on what's helpful for remembering this moment
- Don't assume identities - describe appearances instead
- Support both French and English - match the language of any visible text, or default to English
- If the image quality is poor or unclear, mention it briefly

Example outputs:
- "Two people are embracing at what appears to be a birthday celebration. There's a cake with candles on a table, and colorful balloons in the background. The setting is indoors, possibly a home dining room."
- "A group of four people posing in front of a mountain landscape. They're wearing hiking gear and look to be at a summit or viewpoint. Clear sunny weather with snow-capped peaks visible in the distance."
"""


def generate_photo_description(image_url: str, person_context: list[str] | None = None) -> str:
    """
    Generate an AI description for a photo using OpenAI Vision.

    Args:
        image_url: URL or base64 data URL of the image
        person_context: Optional list of person names associated with this photo for context

    Returns:
        Generated description text
    """
    client = get_openai_client()

    user_message_parts = []

    # Add person context if available
    if person_context:
        context = ", ".join(person_context)
        user_message_parts.append({
            "type": "text",
            "text": f"This photo is tagged with the following people: {context}. Please describe what you see in the photo."
        })
    else:
        user_message_parts.append({
            "type": "text",
            "text": "Please describe what you see in this photo."
        })

    # Add the image
    user_message_parts.append({
        "type": "image_url",
        "image_url": {
            "url": image_url,
            "detail": "auto"  # Let OpenAI decide resolution
        }
    })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PHOTO_DESCRIPTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_message_parts}
            ],
            max_tokens=500,
            temperature=0.5,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"OpenAI Vision API error generating photo description: {e}")
        raise


CHAT_SYSTEM_PROMPT = """You are a helpful assistant for a personal CRM called LifeGraph. You help the user remember information about the people in their life.

You have access to the user's contact database. Answer questions about:
- People's birthdays, relationships, jobs, contact info
- Memories and anecdotes about people
- Connections between people
- Finding people by various criteria

Guidelines:
1. Be conversational and helpful
2. If you don't have information, say so clearly
3. When mentioning people, include their relationship if known (e.g., "your mother Marie")
4. Support both French and English - respond in the same language as the question
5. For date-related questions, today's date will be provided
6. Be concise but complete

The user's contacts database is provided below."""


def chat_with_context(
    question: str,
    contacts_context: str,
    today_date: str,
    conversation_history: list[dict] | None = None
) -> str:
    """
    Answer questions about contacts using AI with database context.

    Args:
        question: User's question
        contacts_context: Formatted string with relevant contact information
        today_date: Today's date in YYYY-MM-DD format
        conversation_history: Optional list of previous messages

    Returns:
        AI response to the question
    """
    client = get_openai_client()

    system_message = f"""{CHAT_SYSTEM_PROMPT}

Today's date: {today_date}

## Contacts Database:
{contacts_context}"""

    messages = [{"role": "system", "content": system_message}]

    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history[-10:]:  # Limit to last 10 messages
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

    messages.append({"role": "user", "content": question})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"OpenAI API error in chat: {e}")
        raise
