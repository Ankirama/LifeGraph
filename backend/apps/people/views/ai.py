"""
AI-powered views for contact parsing, suggestions, and smart search.
"""

import logging
from collections import defaultdict
from datetime import date

from django.db.models import Q
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Group, Tag
from apps.core.ratelimit import ai_ratelimit

from ..exceptions import AIServiceError, OwnerNotFoundError
from ..models import Anecdote, Employment, Person, Photo, Relationship, RelationshipType
from ..serializers import PersonListSerializer, RelationshipSerializer
from ..services import (
    chat_with_context,
    parse_contacts_text,
    parse_updates_text,
    smart_search,
    suggest_relationships,
)


logger = logging.getLogger(__name__)


class AIParseContactsView(APIView):
    """
    Parse natural language text into structured contact data using AI.

    POST: Accepts text describing contacts and returns parsed structured data.
    Rate limited to prevent abuse of expensive AI operations.
    """

    @method_decorator(ai_ratelimit())
    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response(
                {"detail": "Text is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(text) > 10000:
            return Response(
                {"detail": "Text too long. Maximum 10,000 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = parse_contacts_text(text)
            return Response(result)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            raise AIServiceError(detail=f"AI parsing failed: {str(e)}")


class AIBulkImportView(APIView):
    """
    Bulk import contacts from AI-parsed data.

    POST: Creates persons and relationships from parsed contact data.
    Rate limited to prevent abuse.
    """

    @method_decorator(ai_ratelimit())
    def post(self, request):
        persons_data = request.data.get("persons", [])
        if not persons_data:
            return Response(
                {"detail": "No persons data provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the owner for creating relationships
        try:
            owner = Person.objects.get(is_owner=True)
        except Person.DoesNotExist:
            raise OwnerNotFoundError(
                detail="Owner profile not set up. Please create your profile first."
            )

        created_persons = []
        created_relationships = []
        errors = []

        for idx, person_data in enumerate(persons_data):
            try:
                # Create the person
                person = Person.objects.create(
                    first_name=person_data.get("first_name", ""),
                    last_name=person_data.get("last_name", ""),
                    nickname=person_data.get("nickname", ""),
                    birthday=person_data.get("birthday"),
                    notes=person_data.get("notes", ""),
                )
                created_persons.append(PersonListSerializer(person).data)

                # Create relationship if specified
                relationship_name = person_data.get("relationship_to_owner", "").strip().lower()
                if relationship_name:
                    # Find matching relationship type
                    relationship_type = RelationshipType.objects.filter(
                        Q(name__iexact=relationship_name) | Q(inverse_name__iexact=relationship_name)
                    ).first()

                    if relationship_type:
                        # Determine the correct direction:
                        # If the person is "mother" to owner, then:
                        # - person_a = person (the mother)
                        # - person_b = owner (me)
                        # - relationship_type should have name="mother"
                        if relationship_type.name.lower() == relationship_name:
                            # Direct match: person is [name] to owner
                            rel = Relationship.objects.create(
                                person_a=person,
                                person_b=owner,
                                relationship_type=relationship_type,
                            )
                        else:
                            # Inverse match: owner is [name] to person
                            # So we flip: person_a = owner, person_b = person
                            rel = Relationship.objects.create(
                                person_a=owner,
                                person_b=person,
                                relationship_type=relationship_type,
                            )
                        created_relationships.append(RelationshipSerializer(rel).data)
                    else:
                        errors.append(f"Person {idx + 1}: Relationship type '{relationship_name}' not found")

            except Exception as e:
                errors.append(f"Person {idx + 1}: {str(e)}")

        return Response({
            "created_persons": created_persons,
            "created_relationships": created_relationships,
            "errors": errors,
            "summary": {
                "persons_created": len(created_persons),
                "relationships_created": len(created_relationships),
                "errors_count": len(errors),
            }
        }, status=status.HTTP_201_CREATED if created_persons else status.HTTP_400_BAD_REQUEST)


class AIParseUpdatesView(APIView):
    """
    Parse natural language text into updates for existing contacts using AI.

    POST: Accepts text describing updates/memories and returns parsed structured data.
    Rate limited to prevent abuse of expensive AI operations.
    """

    @method_decorator(ai_ratelimit())
    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response(
                {"detail": "Text is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(text) > 10000:
            return Response(
                {"detail": "Text too long. Maximum 10,000 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get existing contacts with their relationships to owner
        try:
            owner = Person.objects.get(is_owner=True)
        except Person.DoesNotExist:
            owner = None

        # Build list of existing contacts with relationship info
        existing_contacts = []
        for person in Person.objects.filter(is_active=True, is_owner=False):
            contact_info = {
                "id": str(person.id),
                "full_name": person.full_name,
                "relationship_to_me": None,
            }

            # Get relationship to owner if owner exists
            if owner:
                rel = Relationship.objects.filter(
                    person_a=person, person_b=owner
                ).select_related("relationship_type").first()
                if rel:
                    contact_info["relationship_to_me"] = rel.relationship_type.name

                if not contact_info["relationship_to_me"]:
                    rel = Relationship.objects.filter(
                        person_a=owner, person_b=person
                    ).select_related("relationship_type").first()
                    if rel:
                        contact_info["relationship_to_me"] = rel.relationship_type.inverse_name

            existing_contacts.append(contact_info)

        try:
            result = parse_updates_text(text, existing_contacts)
            return Response(result)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            raise AIServiceError(detail=f"AI parsing failed: {str(e)}")


class AIApplyUpdatesView(APIView):
    """
    Apply AI-parsed updates to existing contacts.

    POST: Applies field updates and creates anecdotes from parsed data.
    Rate limited to prevent abuse.
    """

    @method_decorator(ai_ratelimit())
    def post(self, request):
        updates_data = request.data.get("updates", [])
        if not updates_data:
            return Response(
                {"detail": "No updates data provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_persons = []
        created_anecdotes = []
        errors = []

        for idx, update in enumerate(updates_data):
            person_id = update.get("matched_person_id")
            if not person_id:
                errors.append(f"Update {idx + 1}: No matched person ID")
                continue

            try:
                person = Person.objects.get(id=person_id, is_active=True)
            except Person.DoesNotExist:
                errors.append(f"Update {idx + 1}: Person not found")
                continue

            try:
                # Apply field updates
                field_updates = update.get("field_updates", {})
                fields_changed = []

                if field_updates.get("birthday"):
                    person.birthday = field_updates["birthday"]
                    fields_changed.append("birthday")

                if field_updates.get("nickname"):
                    person.nickname = field_updates["nickname"]
                    fields_changed.append("nickname")

                if field_updates.get("notes_to_append"):
                    if person.notes:
                        person.notes = f"{person.notes}\n\n{field_updates['notes_to_append']}"
                    else:
                        person.notes = field_updates["notes_to_append"]
                    fields_changed.append("notes")

                if fields_changed:
                    person.save()
                    updated_persons.append({
                        "id": str(person.id),
                        "full_name": person.full_name,
                        "fields_updated": fields_changed,
                    })

                # Create anecdotes
                for anecdote_data in update.get("anecdotes", []):
                    anecdote = Anecdote.objects.create(
                        title=anecdote_data.get("title", ""),
                        content=anecdote_data["content"],
                        anecdote_type=anecdote_data.get("anecdote_type", "note"),
                        date=anecdote_data.get("date"),
                        location=anecdote_data.get("location", ""),
                    )
                    anecdote.persons.add(person)
                    created_anecdotes.append({
                        "id": str(anecdote.id),
                        "title": anecdote.title,
                        "content": anecdote.content[:100] + "..." if len(anecdote.content) > 100 else anecdote.content,
                        "person_name": person.full_name,
                    })

            except Exception as e:
                errors.append(f"Update {idx + 1}: {str(e)}")

        return Response({
            "updated_persons": updated_persons,
            "created_anecdotes": created_anecdotes,
            "errors": errors,
            "summary": {
                "persons_updated": len(updated_persons),
                "anecdotes_created": len(created_anecdotes),
                "errors_count": len(errors),
            }
        }, status=status.HTTP_200_OK if (updated_persons or created_anecdotes) else status.HTTP_400_BAD_REQUEST)


class AIChatView(APIView):
    """
    AI-powered chat about contacts.

    POST: Answer questions about the user's contacts using AI.
    Rate limited to prevent abuse of expensive AI operations.
    """

    @method_decorator(ai_ratelimit())
    def post(self, request):
        question = request.data.get("question", "").strip()
        if not question:
            return Response(
                {"detail": "Question is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(question) > 2000:
            return Response(
                {"detail": "Question too long. Maximum 2,000 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get conversation history if provided
        conversation_history = request.data.get("history", [])

        # Build contacts context
        owner = Person.objects.filter(is_owner=True).first()
        context_parts = []

        # Add owner info
        if owner:
            context_parts.append(f"Owner (You): {owner.full_name}")

        # Add all contacts with their relationships and key info
        for person in Person.objects.filter(is_active=True, is_owner=False).prefetch_related("anecdotes", "employments")[:100]:
            person_info = [f"\n### {person.full_name}"]

            # Get relationship to owner
            if owner:
                rel = Relationship.objects.filter(
                    person_a=person, person_b=owner
                ).select_related("relationship_type").first()
                if rel:
                    person_info.append(f"Relationship: {rel.relationship_type.name}")

            if person.birthday:
                person_info.append(f"Birthday: {person.birthday.isoformat()}")

            if person.nickname:
                person_info.append(f"Nickname: {person.nickname}")

            if person.notes:
                person_info.append(f"Notes: {person.notes[:200]}")

            # Current employment
            current_job = person.employments.filter(is_current=True).first()
            if current_job:
                person_info.append(f"Current job: {current_job.title} at {current_job.company}")

            # Recent anecdotes (limit to 3)
            anecdotes = person.anecdotes.all()[:3]
            if anecdotes:
                anecdote_texts = []
                for a in anecdotes:
                    anecdote_texts.append(f"- [{a.anecdote_type}] {a.title or ''}: {a.content[:100]}")
                person_info.append(f"Anecdotes:\n" + "\n".join(anecdote_texts))

            context_parts.append("\n".join(person_info))

        contacts_context = "\n".join(context_parts)
        today_date = date.today().isoformat()

        try:
            response = chat_with_context(
                question=question,
                contacts_context=contacts_context,
                today_date=today_date,
                conversation_history=conversation_history,
            )

            return Response({
                "answer": response,
                "question": question,
            })
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise AIServiceError(detail=f"Chat failed: {str(e)}")


class AISuggestRelationshipsView(APIView):
    """
    AI-powered relationship suggestions.

    GET: Analyze contacts and suggest potential relationships.
    Rate limited to prevent abuse of expensive AI operations.
    """

    @method_decorator(ai_ratelimit())
    def get(self, request):
        # Get all active persons (excluding owner)
        owner = Person.objects.filter(is_owner=True).first()
        persons = Person.objects.filter(is_active=True, is_owner=False).prefetch_related(
            "tags", "groups", "employments"
        )

        if persons.count() < 2:
            return Response({
                "suggestions": [],
                "message": "Need at least 2 contacts to suggest relationships.",
            })

        # Build persons data
        persons_data = []
        for person in persons:
            current_emp = person.employments.filter(is_current=True).first()
            persons_data.append({
                "id": str(person.id),
                "full_name": person.full_name,
                "tags": [t.name for t in person.tags.all()],
                "groups": [g.name for g in person.groups.all()],
                "current_employment": {
                    "company": current_emp.company if current_emp else None,
                    "title": current_emp.title if current_emp else None,
                } if current_emp else None,
                "notes": person.notes or "",
            })

        # Get existing relationships (between contacts, not with owner)
        existing_relationships = []
        for rel in Relationship.objects.filter(
            person_a__is_owner=False,
            person_b__is_owner=False,
            person_a__is_active=True,
            person_b__is_active=True,
        ).select_related("relationship_type", "person_a", "person_b"):
            existing_relationships.append({
                "person1_id": str(rel.person_a_id),
                "person1_name": rel.person_a.full_name,
                "person2_id": str(rel.person_b_id),
                "person2_name": rel.person_b.full_name,
                "type": rel.relationship_type.name,
            })

        # Build shared contexts
        shared_contexts = {
            "photo_coappearances": [],
            "anecdote_comentions": [],
        }

        # Find photo co-appearances
        photo_people = defaultdict(set)
        for photo in Photo.objects.prefetch_related("persons"):
            person_ids = [(str(p.id), p.full_name) for p in photo.persons.filter(is_owner=False)]
            if len(person_ids) > 1:
                for i, (p1_id, p1_name) in enumerate(person_ids):
                    for p2_id, p2_name in person_ids[i+1:]:
                        key = tuple(sorted([p1_id, p2_id]))
                        photo_people[key].add(photo.id)

        for (p1_id, p2_id), photos in photo_people.items():
            # Get names
            p1 = next((p for p in persons_data if p["id"] == p1_id), None)
            p2 = next((p for p in persons_data if p["id"] == p2_id), None)
            if p1 and p2:
                shared_contexts["photo_coappearances"].append(
                    (p1_id, p1["full_name"], p2_id, p2["full_name"], len(photos))
                )

        # Find anecdote co-mentions
        anecdote_people = defaultdict(set)
        for anecdote in Anecdote.objects.prefetch_related("persons"):
            person_ids = [(str(p.id), p.full_name) for p in anecdote.persons.filter(is_owner=False)]
            if len(person_ids) > 1:
                for i, (p1_id, p1_name) in enumerate(person_ids):
                    for p2_id, p2_name in person_ids[i+1:]:
                        key = tuple(sorted([p1_id, p2_id]))
                        anecdote_people[key].add(anecdote.id)

        for (p1_id, p2_id), anecdotes in anecdote_people.items():
            p1 = next((p for p in persons_data if p["id"] == p1_id), None)
            p2 = next((p for p in persons_data if p["id"] == p2_id), None)
            if p1 and p2:
                shared_contexts["anecdote_comentions"].append(
                    (p1_id, p1["full_name"], p2_id, p2["full_name"], len(anecdotes))
                )

        try:
            suggestions = suggest_relationships(
                persons_data=persons_data,
                existing_relationships=existing_relationships,
                shared_contexts=shared_contexts,
            )

            return Response({
                "suggestions": suggestions,
                "total_contacts": len(persons_data),
                "existing_relationships_count": len(existing_relationships),
            })
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            raise AIServiceError(detail=f"Failed to generate suggestions: {str(e)}")


class AIApplyRelationshipSuggestionView(APIView):
    """
    Apply a relationship suggestion by creating the relationship.

    POST: Create a relationship from a suggestion.
    """

    def post(self, request):
        person1_id = request.data.get("person1_id")
        person2_id = request.data.get("person2_id")
        relationship_type_name = request.data.get("relationship_type", "").strip().lower()

        if not all([person1_id, person2_id, relationship_type_name]):
            return Response(
                {"detail": "person1_id, person2_id, and relationship_type are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate persons exist
        try:
            person1 = Person.objects.get(id=person1_id, is_active=True)
            person2 = Person.objects.get(id=person2_id, is_active=True)
        except Person.DoesNotExist:
            return Response(
                {"detail": "One or both persons not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate relationship type exists
        try:
            rel_type = RelationshipType.objects.get(name__iexact=relationship_type_name)
        except RelationshipType.DoesNotExist:
            return Response(
                {"detail": f"Relationship type '{relationship_type_name}' not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if relationship already exists
        existing = Relationship.objects.filter(
            Q(person_a=person1, person_b=person2) |
            Q(person_a=person2, person_b=person1)
        ).first()

        if existing:
            return Response(
                {"detail": "Relationship already exists between these persons."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the relationship
        relationship = Relationship.objects.create(
            person_a=person1,
            person_b=person2,
            relationship_type=rel_type,
        )

        return Response({
            "id": str(relationship.id),
            "person1": person1.full_name,
            "person2": person2.full_name,
            "relationship_type": rel_type.name,
            "message": f"Created relationship: {person1.full_name} is {rel_type.name} of {person2.full_name}",
        }, status=status.HTTP_201_CREATED)


class AISmartSearchView(APIView):
    """
    AI-powered natural language search.

    POST: Interpret natural language query and search across all data.
    Rate limited to prevent abuse of expensive AI operations.
    """

    @method_decorator(ai_ratelimit())
    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query or len(query) < 3:
            return Response(
                {"detail": "Query must be at least 3 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Gather available options for the AI to reference
        available_tags = list(Tag.objects.values_list("name", flat=True))
        available_groups = list(Group.objects.values_list("name", flat=True))
        available_relationship_types = list(
            RelationshipType.objects.values_list("name", flat=True)
        )
        available_companies = list(
            Employment.objects.filter(company__isnull=False)
            .values_list("company", flat=True)
            .distinct()[:50]
        )

        # Get AI interpretation of the query
        try:
            search_params = smart_search(
                query=query,
                available_tags=available_tags,
                available_groups=available_groups,
                available_relationship_types=available_relationship_types,
                available_companies=available_companies,
            )
        except Exception as e:
            logger.error(f"AI search failed: {e}")
            raise AIServiceError(detail=f"AI search failed: {str(e)}")

        # Execute the search based on parsed parameters
        results = {
            "query": query,
            "interpreted_as": search_params.get("intent", query),
            "search_type": search_params.get("search_type", "mixed"),
            "persons": [],
            "anecdotes": [],
            "employments": [],
        }

        limit = search_params.get("limit", 20)
        person_filters = search_params.get("person_filters", {})
        anecdote_filters = search_params.get("anecdote_filters", {})
        employment_filters = search_params.get("employment_filters", {})
        keywords = search_params.get("keywords", [])

        # Build person query
        if search_params.get("search_type") in ("person", "mixed"):
            results["persons"] = self._search_persons(
                person_filters, keywords, limit
            )

        # Build anecdote query
        if search_params.get("search_type") in ("anecdote", "mixed"):
            results["anecdotes"] = self._search_anecdotes(
                anecdote_filters, keywords, limit
            )

        # Build employment query (usually for "who works at X" type queries)
        if employment_filters.get("company_contains") or employment_filters.get("title_contains"):
            results["employments"] = self._search_employments(
                employment_filters, limit
            )

        # Add total counts
        results["counts"] = {
            "persons": len(results["persons"]),
            "anecdotes": len(results["anecdotes"]),
            "employments": len(results["employments"]),
        }

        return Response(results)

    def _search_persons(self, person_filters, keywords, limit):
        """Search persons based on filters and keywords."""
        person_qs = Person.objects.filter(is_active=True, is_owner=False)

        # Apply person filters
        if person_filters.get("name_contains"):
            name = person_filters["name_contains"]
            person_qs = person_qs.filter(
                Q(first_name__icontains=name) |
                Q(last_name__icontains=name) |
                Q(nickname__icontains=name)
            )

        if person_filters.get("tag"):
            person_qs = person_qs.filter(tags__name__iexact=person_filters["tag"])

        if person_filters.get("group"):
            person_qs = person_qs.filter(groups__name__iexact=person_filters["group"])

        if person_filters.get("notes_contain"):
            person_qs = person_qs.filter(notes__icontains=person_filters["notes_contain"])

        if person_filters.get("met_context_contains"):
            person_qs = person_qs.filter(
                met_context__icontains=person_filters["met_context_contains"]
            )

        if person_filters.get("relationship_type"):
            rel_type = person_filters["relationship_type"]
            person_qs = person_qs.filter(
                Q(relationships_as_b__relationship_type__name__icontains=rel_type) |
                Q(relationships_as_a__relationship_type__name__icontains=rel_type) |
                Q(relationships_as_b__relationship_type__inverse_name__icontains=rel_type) |
                Q(relationships_as_a__relationship_type__inverse_name__icontains=rel_type)
            )

        if person_filters.get("works_at"):
            company = person_filters["works_at"]
            person_qs = person_qs.filter(
                employments__company__icontains=company,
                employments__is_current=True,
            )

        if person_filters.get("job_title_contains"):
            title = person_filters["job_title_contains"]
            person_qs = person_qs.filter(
                employments__title__icontains=title,
                employments__is_current=True,
            )

        if person_filters.get("has_birthday_soon"):
            today = date.today()
            person_qs = person_qs.filter(birthday__isnull=False)
            persons_with_birthday = []
            for person in person_qs.distinct()[:100]:
                if person.birthday:
                    this_year_bday = person.birthday.replace(year=today.year)
                    if this_year_bday < today:
                        this_year_bday = this_year_bday.replace(year=today.year + 1)
                    days_until = (this_year_bday - today).days
                    if 0 <= days_until <= 30:
                        persons_with_birthday.append(person.id)
            person_qs = Person.objects.filter(id__in=persons_with_birthday)

        # If no specific filters matched, do keyword search
        if not any(person_filters.values()) and keywords:
            keyword_q = Q()
            for kw in keywords[:5]:
                keyword_q |= (
                    Q(first_name__icontains=kw) |
                    Q(last_name__icontains=kw) |
                    Q(nickname__icontains=kw) |
                    Q(notes__icontains=kw) |
                    Q(met_context__icontains=kw)
                )
            person_qs = person_qs.filter(keyword_q)

        # Get owner for relationship lookup
        owner = Person.objects.filter(is_owner=True).first()

        # Serialize results
        results = []
        for person in person_qs.distinct()[:limit]:
            current_emp = person.employments.filter(is_current=True).first()

            # Get relationship to owner
            relationship_to_me = None
            if owner:
                rel = Relationship.objects.filter(
                    person_a=owner, person_b=person
                ).select_related("relationship_type").first()
                if rel:
                    relationship_to_me = rel.relationship_type.name
                else:
                    rel = Relationship.objects.filter(
                        person_a=person, person_b=owner
                    ).select_related("relationship_type").first()
                    if rel:
                        relationship_to_me = rel.relationship_type.inverse_name or rel.relationship_type.name

            results.append({
                "id": str(person.id),
                "full_name": person.full_name,
                "relationship_to_me": relationship_to_me,
                "current_job": f"{current_emp.title} at {current_emp.company}" if current_emp else None,
                "tags": [t.name for t in person.tags.all()[:5]],
                "avatar_url": person.avatar.url if person.avatar else None,
            })

        return results

    def _search_anecdotes(self, anecdote_filters, keywords, limit):
        """Search anecdotes based on filters and keywords."""
        anecdote_qs = Anecdote.objects.all()

        if anecdote_filters.get("content_contains"):
            text = anecdote_filters["content_contains"]
            anecdote_qs = anecdote_qs.filter(
                Q(title__icontains=text) | Q(content__icontains=text)
            )

        if anecdote_filters.get("anecdote_type"):
            anecdote_qs = anecdote_qs.filter(
                anecdote_type=anecdote_filters["anecdote_type"]
            )

        if anecdote_filters.get("location_contains"):
            anecdote_qs = anecdote_qs.filter(
                location__icontains=anecdote_filters["location_contains"]
            )

        date_range = anecdote_filters.get("date_range", {})
        if date_range.get("start"):
            anecdote_qs = anecdote_qs.filter(date__gte=date_range["start"])
        if date_range.get("end"):
            anecdote_qs = anecdote_qs.filter(date__lte=date_range["end"])

        # If no specific filters, keyword search
        if not any(anecdote_filters.values()) and keywords:
            keyword_q = Q()
            for kw in keywords[:5]:
                keyword_q |= (
                    Q(title__icontains=kw) |
                    Q(content__icontains=kw) |
                    Q(location__icontains=kw)
                )
            anecdote_qs = anecdote_qs.filter(keyword_q)

        results = []
        for anecdote in anecdote_qs.distinct()[:limit]:
            results.append({
                "id": str(anecdote.id),
                "title": anecdote.title,
                "content": anecdote.content[:200] + "..." if len(anecdote.content) > 200 else anecdote.content,
                "anecdote_type": anecdote.anecdote_type,
                "date": anecdote.date.isoformat() if anecdote.date else None,
                "location": anecdote.location,
                "persons": [p.full_name for p in anecdote.persons.all()[:3]],
            })

        return results

    def _search_employments(self, employment_filters, limit):
        """Search employments based on filters."""
        emp_qs = Employment.objects.select_related("person")

        if employment_filters.get("company_contains"):
            emp_qs = emp_qs.filter(
                company__icontains=employment_filters["company_contains"]
            )

        if employment_filters.get("title_contains"):
            emp_qs = emp_qs.filter(
                title__icontains=employment_filters["title_contains"]
            )

        if employment_filters.get("is_current") is not None:
            emp_qs = emp_qs.filter(is_current=employment_filters["is_current"])

        results = []
        for emp in emp_qs.distinct()[:limit]:
            results.append({
                "id": str(emp.id),
                "person_id": str(emp.person.id),
                "person_name": emp.person.full_name,
                "company": emp.company,
                "title": emp.title,
                "is_current": emp.is_current,
            })

        return results
