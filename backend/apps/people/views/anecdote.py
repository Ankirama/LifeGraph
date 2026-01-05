"""
Anecdote-related views.
"""

from django_filters import rest_framework as filters
from rest_framework import viewsets

from ..models import Anecdote
from ..serializers import AnecdoteSerializer


class AnecdoteFilter(filters.FilterSet):
    """Filter for Anecdote queryset."""

    person = filters.UUIDFilter(field_name="persons__id")
    tag = filters.UUIDFilter(field_name="tags__id")
    anecdote_type = filters.ChoiceFilter(choices=Anecdote.AnecdoteType.choices)
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Anecdote
        fields = ["person", "tag", "anecdote_type", "date_from", "date_to"]


class AnecdoteViewSet(viewsets.ModelViewSet):
    """ViewSet for Anecdote CRUD operations."""

    queryset = Anecdote.objects.prefetch_related("persons", "tags").all()
    serializer_class = AnecdoteSerializer
    filterset_class = AnecdoteFilter
    search_fields = ["title", "content", "location"]
    ordering_fields = ["date", "created_at", "anecdote_type"]
    ordering = ["-date", "-created_at"]
