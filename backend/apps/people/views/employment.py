"""
Employment-related views.
"""

from django_filters import rest_framework as filters
from rest_framework import viewsets

from ..models import Employment
from ..serializers import EmploymentSerializer


class EmploymentFilter(filters.FilterSet):
    """Filter for Employment queryset."""

    person = filters.UUIDFilter(field_name="person__id")
    company = filters.CharFilter(lookup_expr="icontains")
    is_current = filters.BooleanFilter()
    start_after = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    end_before = filters.DateFilter(field_name="end_date", lookup_expr="lte")

    class Meta:
        model = Employment
        fields = ["person", "company", "is_current", "start_after", "end_before"]


class EmploymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Employment CRUD operations."""

    queryset = Employment.objects.select_related("person").all()
    serializer_class = EmploymentSerializer
    filterset_class = EmploymentFilter
    search_fields = ["company", "title", "department", "description"]
    ordering_fields = ["start_date", "end_date", "company", "created_at"]
    ordering = ["-is_current", "-start_date"]
