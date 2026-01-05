"""
Dashboard and search views.
"""

from datetime import date

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..exceptions import OwnerNotFoundError
from ..models import Anecdote, Employment, Person, Photo, Relationship
from ..serializers import (
    AnecdoteSerializer,
    EmploymentSerializer,
    PersonCreateUpdateSerializer,
    PersonDetailSerializer,
    PersonListSerializer,
)


class MeView(APIView):
    """
    Get or create the CRM owner (you).

    GET: Returns the owner record if it exists, 404 otherwise
    POST: Creates the owner record (only one allowed)
    PUT/PATCH: Updates the owner record
    """

    def get(self, request):
        try:
            owner = Person.objects.get(is_owner=True)
            serializer = PersonDetailSerializer(owner)
            return Response(serializer.data)
        except Person.DoesNotExist:
            return Response(
                {"detail": "Owner profile not set up yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request):
        # Check if owner already exists
        if Person.objects.filter(is_owner=True).exists():
            return Response(
                {"detail": "Owner profile already exists. Use PUT to update."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PersonCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            person = serializer.save(is_owner=True)
            return Response(
                PersonDetailSerializer(person).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            owner = Person.objects.get(is_owner=True)
        except Person.DoesNotExist:
            return Response(
                {"detail": "Owner profile not set up yet. Use POST to create."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PersonCreateUpdateSerializer(owner, data=request.data)
        if serializer.is_valid():
            person = serializer.save()
            return Response(PersonDetailSerializer(person).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            owner = Person.objects.get(is_owner=True)
        except Person.DoesNotExist:
            return Response(
                {"detail": "Owner profile not set up yet. Use POST to create."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PersonCreateUpdateSerializer(owner, data=request.data, partial=True)
        if serializer.is_valid():
            person = serializer.save()
            return Response(PersonDetailSerializer(person).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardView(APIView):
    """Dashboard statistics and recent activity."""

    def get(self, request):
        today = date.today()

        # Get counts (exclude owner from person count)
        total_persons = Person.objects.filter(is_active=True, is_owner=False).count()
        total_relationships = Relationship.objects.count()
        total_anecdotes = Anecdote.objects.count()
        total_photos = Photo.objects.count()

        # Upcoming birthdays (next 30 days)
        upcoming_birthdays = []
        persons_with_birthday = Person.objects.filter(
            is_active=True,
            is_owner=False,
            birthday__isnull=False
        )

        for person in persons_with_birthday:
            # Calculate this year's birthday
            try:
                birthday_this_year = person.birthday.replace(year=today.year)
            except ValueError:
                # Handle Feb 29 for non-leap years
                birthday_this_year = person.birthday.replace(year=today.year, day=28)

            # If birthday already passed this year, check next year
            if birthday_this_year < today:
                try:
                    birthday_this_year = person.birthday.replace(year=today.year + 1)
                except ValueError:
                    birthday_this_year = person.birthday.replace(year=today.year + 1, day=28)

            days_until = (birthday_this_year - today).days
            if 0 <= days_until <= 30:
                # Calculate age they'll be turning
                age = birthday_this_year.year - person.birthday.year
                upcoming_birthdays.append({
                    "id": str(person.id),
                    "full_name": person.full_name,
                    "birthday": person.birthday.isoformat(),
                    "days_until": days_until,
                    "turning_age": age,
                    "date": birthday_this_year.isoformat(),
                })

        # Sort by days until
        upcoming_birthdays.sort(key=lambda x: x["days_until"])

        # Recent anecdotes (last 10)
        recent_anecdotes = []
        for anecdote in Anecdote.objects.prefetch_related("persons")[:10]:
            person_names = [p.full_name for p in anecdote.persons.all()[:3]]
            recent_anecdotes.append({
                "id": str(anecdote.id),
                "title": anecdote.title,
                "content": anecdote.content[:150] + "..." if len(anecdote.content) > 150 else anecdote.content,
                "anecdote_type": anecdote.anecdote_type,
                "date": anecdote.date.isoformat() if anecdote.date else None,
                "persons": person_names,
                "created_at": anecdote.created_at.isoformat(),
            })

        # Recently added people (last 10)
        recent_persons = []
        owner = Person.objects.filter(is_owner=True).first()
        for person in Person.objects.filter(is_active=True, is_owner=False).order_by("-created_at")[:10]:
            # Get relationship to owner (what this person IS to me)
            relationship_to_me = None
            if owner:
                # Look for relationship where this person is related TO the owner
                rel = Relationship.objects.filter(
                    person_a=person,
                    person_b=owner
                ).select_related("relationship_type").first()
                if rel:
                    relationship_to_me = rel.relationship_type.name

            recent_persons.append({
                "id": str(person.id),
                "full_name": person.full_name,
                "relationship_to_me": relationship_to_me,
                "created_at": person.created_at.isoformat(),
            })

        # Relationship type distribution
        relationship_stats = list(
            Relationship.objects.values("relationship_type__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        return Response({
            "stats": {
                "total_persons": total_persons,
                "total_relationships": total_relationships,
                "total_anecdotes": total_anecdotes,
                "total_photos": total_photos,
            },
            "upcoming_birthdays": upcoming_birthdays[:10],
            "recent_anecdotes": recent_anecdotes,
            "recent_persons": recent_persons,
            "relationship_distribution": [
                {"name": r["relationship_type__name"], "count": r["count"]}
                for r in relationship_stats
            ],
        })


class GlobalSearchView(APIView):
    """
    Full-text search across all major models.

    Supports searching across Person, Anecdote, and Employment.
    Uses PostgreSQL's full-text search for relevance ranking.
    """

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response({
                "persons": [],
                "anecdotes": [],
                "employments": [],
            })

        # Use PostgreSQL full-text search
        search_query = SearchQuery(query, search_type="websearch")

        # Search persons
        person_vector = SearchVector(
            "first_name", weight="A"
        ) + SearchVector(
            "last_name", weight="A"
        ) + SearchVector(
            "nickname", weight="A"
        ) + SearchVector(
            "notes", weight="B"
        ) + SearchVector(
            "met_context", weight="C"
        )

        persons = (
            Person.objects.annotate(
                search=person_vector,
                rank=SearchRank(person_vector, search_query),
            )
            .filter(
                Q(search=search_query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(nickname__icontains=query),
                is_active=True,
            )
            .order_by("-rank")[:20]
        )

        person_results = PersonListSerializer(persons, many=True).data

        # Search anecdotes
        anecdote_vector = SearchVector(
            "title", weight="A"
        ) + SearchVector(
            "content", weight="B"
        ) + SearchVector(
            "location", weight="C"
        )

        anecdotes = (
            Anecdote.objects.annotate(
                search=anecdote_vector,
                rank=SearchRank(anecdote_vector, search_query),
            )
            .filter(
                Q(search=search_query) | Q(title__icontains=query) | Q(content__icontains=query)
            )
            .prefetch_related("persons", "tags")
            .order_by("-rank")[:20]
        )

        anecdote_results = AnecdoteSerializer(anecdotes, many=True).data

        # Search employments
        employment_vector = SearchVector(
            "company", weight="A"
        ) + SearchVector(
            "title", weight="A"
        ) + SearchVector(
            "department", weight="B"
        ) + SearchVector(
            "description", weight="C"
        )

        employments = (
            Employment.objects.annotate(
                search=employment_vector,
                rank=SearchRank(employment_vector, search_query),
            )
            .filter(
                Q(search=search_query) | Q(company__icontains=query) | Q(title__icontains=query)
            )
            .select_related("person")
            .order_by("-rank")[:20]
        )

        employment_results = EmploymentSerializer(employments, many=True).data

        return Response({
            "persons": person_results,
            "anecdotes": anecdote_results,
            "employments": employment_results,
            "query": query,
        })
