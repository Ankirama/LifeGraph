"""
Export service for LifeGraph data.

Supports JSON and CSV export formats for all data or specific entities.
"""

import csv
import io
import json
from datetime import date, datetime
from typing import Any
from uuid import UUID

from apps.core.models import Group, Tag
from apps.people.models import (
    Anecdote,
    Employment,
    Person,
    Photo,
    Relationship,
    RelationshipType,
)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling special types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def export_persons(include_related: bool = True) -> list[dict]:
    """
    Export all persons with optional related data.

    Args:
        include_related: Include tags, groups, employments, etc.

    Returns:
        List of person dictionaries.
    """
    persons = Person.objects.prefetch_related(
        "tags", "groups", "employments"
    ).all()

    result = []
    for person in persons:
        data = {
            "id": str(person.id),
            "first_name": person.first_name,
            "last_name": person.last_name,
            "nickname": person.nickname,
            "birthday": person.birthday.isoformat() if person.birthday else None,
            "met_date": person.met_date.isoformat() if person.met_date else None,
            "met_context": person.met_context,
            "emails": person.emails,
            "phones": person.phones,
            "addresses": person.addresses,
            "linkedin_url": person.linkedin_url,
            "discord_id": person.discord_id,
            "notes": person.notes,
            "is_active": person.is_active,
            "is_owner": person.is_owner,
            "ai_summary": person.ai_summary,
            "last_contact": person.last_contact.isoformat() if person.last_contact else None,
            "created_at": person.created_at.isoformat(),
            "updated_at": person.updated_at.isoformat(),
        }

        if include_related:
            data["tags"] = [tag.name for tag in person.tags.all()]
            data["groups"] = [group.name for group in person.groups.all()]
            data["employments"] = [
                {
                    "company": emp.company,
                    "title": emp.title,
                    "department": emp.department,
                    "start_date": emp.start_date.isoformat() if emp.start_date else None,
                    "end_date": emp.end_date.isoformat() if emp.end_date else None,
                    "is_current": emp.is_current,
                    "location": emp.location,
                    "description": emp.description,
                }
                for emp in person.employments.all()
            ]

        result.append(data)

    return result


def export_relationships() -> list[dict]:
    """Export all relationships."""
    relationships = Relationship.objects.select_related(
        "person_a", "person_b", "relationship_type"
    ).all()

    return [
        {
            "id": str(rel.id),
            "person_a": rel.person_a.full_name,
            "person_a_id": str(rel.person_a.id),
            "person_b": rel.person_b.full_name,
            "person_b_id": str(rel.person_b.id),
            "relationship_type": rel.relationship_type.name,
            "relationship_type_inverse": rel.relationship_type.inverse_name,
            "started_date": rel.started_date.isoformat() if rel.started_date else None,
            "notes": rel.notes,
            "strength": rel.strength,
            "auto_created": rel.auto_created,
            "created_at": rel.created_at.isoformat(),
        }
        for rel in relationships
    ]


def export_anecdotes() -> list[dict]:
    """Export all anecdotes."""
    anecdotes = Anecdote.objects.prefetch_related("persons", "tags").all()

    return [
        {
            "id": str(anecdote.id),
            "title": anecdote.title,
            "content": anecdote.content,
            "date": anecdote.date.isoformat() if anecdote.date else None,
            "location": anecdote.location,
            "anecdote_type": anecdote.anecdote_type,
            "persons": [p.full_name for p in anecdote.persons.all()],
            "person_ids": [str(p.id) for p in anecdote.persons.all()],
            "tags": [t.name for t in anecdote.tags.all()],
            "created_at": anecdote.created_at.isoformat(),
            "updated_at": anecdote.updated_at.isoformat(),
        }
        for anecdote in anecdotes
    ]


def export_photos() -> list[dict]:
    """Export all photo metadata (not the actual files)."""
    photos = Photo.objects.prefetch_related("persons").select_related("anecdote").all()

    return [
        {
            "id": str(photo.id),
            "file_path": photo.file.name if photo.file else None,
            "caption": photo.caption,
            "date_taken": photo.date_taken.isoformat() if photo.date_taken else None,
            "location": photo.location,
            "location_coords": photo.location_coords,
            "ai_description": photo.ai_description,
            "detected_faces": photo.detected_faces,
            "persons": [p.full_name for p in photo.persons.all()],
            "person_ids": [str(p.id) for p in photo.persons.all()],
            "anecdote_id": str(photo.anecdote.id) if photo.anecdote else None,
            "created_at": photo.created_at.isoformat(),
        }
        for photo in photos
    ]


def export_tags() -> list[dict]:
    """Export all tags."""
    tags = Tag.objects.all()

    return [
        {
            "id": str(tag.id),
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "created_at": tag.created_at.isoformat(),
        }
        for tag in tags
    ]


def export_groups() -> list[dict]:
    """Export all groups."""
    groups = Group.objects.select_related("parent").all()

    return [
        {
            "id": str(group.id),
            "name": group.name,
            "description": group.description,
            "parent": group.parent.name if group.parent else None,
            "parent_id": str(group.parent.id) if group.parent else None,
            "color": group.color,
            "created_at": group.created_at.isoformat(),
        }
        for group in groups
    ]


def export_relationship_types() -> list[dict]:
    """Export all relationship types."""
    types = RelationshipType.objects.all()

    return [
        {
            "id": str(rt.id),
            "name": rt.name,
            "inverse_name": rt.inverse_name,
            "category": rt.category,
            "is_symmetric": rt.is_symmetric,
            "auto_create_inverse": rt.auto_create_inverse,
            "created_at": rt.created_at.isoformat(),
        }
        for rt in types
    ]


def export_all_json() -> str:
    """
    Export all data as a comprehensive JSON structure.

    Returns:
        JSON string with all exportable data.
    """
    data = {
        "export_version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "data": {
            "persons": export_persons(include_related=True),
            "relationships": export_relationships(),
            "relationship_types": export_relationship_types(),
            "anecdotes": export_anecdotes(),
            "photos": export_photos(),
            "tags": export_tags(),
            "groups": export_groups(),
        },
        "counts": {
            "persons": Person.objects.count(),
            "relationships": Relationship.objects.count(),
            "relationship_types": RelationshipType.objects.count(),
            "anecdotes": Anecdote.objects.count(),
            "photos": Photo.objects.count(),
            "tags": Tag.objects.count(),
            "groups": Group.objects.count(),
        },
    }

    return json.dumps(data, cls=JSONEncoder, indent=2, ensure_ascii=False)


def export_entity_json(entity_type: str) -> str:
    """
    Export a specific entity type as JSON.

    Args:
        entity_type: One of 'persons', 'relationships', 'anecdotes',
                     'photos', 'tags', 'groups', 'relationship_types'

    Returns:
        JSON string with the entity data.
    """
    exporters = {
        "persons": lambda: export_persons(include_related=True),
        "relationships": export_relationships,
        "relationship_types": export_relationship_types,
        "anecdotes": export_anecdotes,
        "photos": export_photos,
        "tags": export_tags,
        "groups": export_groups,
    }

    if entity_type not in exporters:
        raise ValueError(f"Unknown entity type: {entity_type}")

    data = {
        "export_version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "entity_type": entity_type,
        "data": exporters[entity_type](),
        "count": len(exporters[entity_type]()),
    }

    return json.dumps(data, cls=JSONEncoder, indent=2, ensure_ascii=False)


def export_persons_csv() -> str:
    """
    Export persons as CSV format.

    Returns:
        CSV string with person data.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    headers = [
        "id",
        "first_name",
        "last_name",
        "nickname",
        "birthday",
        "met_date",
        "met_context",
        "primary_email",
        "primary_phone",
        "linkedin_url",
        "discord_id",
        "notes",
        "is_active",
        "is_owner",
        "tags",
        "groups",
        "current_company",
        "current_title",
        "created_at",
        "updated_at",
    ]
    writer.writerow(headers)

    persons = Person.objects.prefetch_related(
        "tags", "groups", "employments"
    ).all()

    for person in persons:
        current_emp = person.employments.filter(is_current=True).first()
        emails = person.emails or []
        phones = person.phones or []

        row = [
            str(person.id),
            person.first_name,
            person.last_name,
            person.nickname or "",
            person.birthday.isoformat() if person.birthday else "",
            person.met_date.isoformat() if person.met_date else "",
            person.met_context or "",
            emails[0]["email"] if emails else "",
            phones[0]["phone"] if phones else "",
            person.linkedin_url or "",
            person.discord_id or "",
            person.notes or "",
            str(person.is_active),
            str(person.is_owner),
            "|".join(t.name for t in person.tags.all()),
            "|".join(g.name for g in person.groups.all()),
            current_emp.company if current_emp else "",
            current_emp.title if current_emp else "",
            person.created_at.isoformat(),
            person.updated_at.isoformat(),
        ]
        writer.writerow(row)

    return output.getvalue()


def export_relationships_csv() -> str:
    """Export relationships as CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "id",
        "person_a",
        "person_a_id",
        "person_b",
        "person_b_id",
        "relationship_type",
        "relationship_type_inverse",
        "started_date",
        "notes",
        "strength",
        "auto_created",
        "created_at",
    ]
    writer.writerow(headers)

    relationships = Relationship.objects.select_related(
        "person_a", "person_b", "relationship_type"
    ).all()

    for rel in relationships:
        row = [
            str(rel.id),
            rel.person_a.full_name,
            str(rel.person_a.id),
            rel.person_b.full_name,
            str(rel.person_b.id),
            rel.relationship_type.name,
            rel.relationship_type.inverse_name or "",
            rel.started_date.isoformat() if rel.started_date else "",
            rel.notes or "",
            rel.strength or "",
            str(rel.auto_created),
            rel.created_at.isoformat(),
        ]
        writer.writerow(row)

    return output.getvalue()


def export_anecdotes_csv() -> str:
    """Export anecdotes as CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "id",
        "title",
        "content",
        "date",
        "location",
        "anecdote_type",
        "persons",
        "tags",
        "created_at",
        "updated_at",
    ]
    writer.writerow(headers)

    anecdotes = Anecdote.objects.prefetch_related("persons", "tags").all()

    for anecdote in anecdotes:
        row = [
            str(anecdote.id),
            anecdote.title,
            anecdote.content,
            anecdote.date.isoformat() if anecdote.date else "",
            anecdote.location or "",
            anecdote.anecdote_type,
            "|".join(p.full_name for p in anecdote.persons.all()),
            "|".join(t.name for t in anecdote.tags.all()),
            anecdote.created_at.isoformat(),
            anecdote.updated_at.isoformat(),
        ]
        writer.writerow(row)

    return output.getvalue()


def export_entity_csv(entity_type: str) -> str:
    """
    Export a specific entity type as CSV.

    Args:
        entity_type: One of 'persons', 'relationships', 'anecdotes'

    Returns:
        CSV string with the entity data.
    """
    csv_exporters = {
        "persons": export_persons_csv,
        "relationships": export_relationships_csv,
        "anecdotes": export_anecdotes_csv,
    }

    if entity_type not in csv_exporters:
        raise ValueError(
            f"CSV export not supported for entity type: {entity_type}. "
            f"Supported types: {', '.join(csv_exporters.keys())}"
        )

    return csv_exporters[entity_type]()
