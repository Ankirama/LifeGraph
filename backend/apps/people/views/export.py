"""
Data export views.
"""

from datetime import date

from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Group, Tag

from ..models import Anecdote, Employment, Person, Photo, Relationship, RelationshipType
from ..services import export_all_json, export_entity_csv, export_entity_json


class ExportDataView(APIView):
    """
    Export data in JSON or CSV format.

    Supports full export of all data or specific entity types.
    """

    def get(self, request):
        """
        Export data based on query parameters.

        Query Parameters:
            export_format: 'json' (default) or 'csv'
            entity: Optional entity type to export (persons, relationships,
                    anecdotes, photos, tags, groups, relationship_types).
                    If not specified, exports all data (JSON only).
        """
        # Use 'export_format' to avoid conflict with DRF's 'format' suffix
        export_format = request.query_params.get("export_format", "json").lower()
        entity_type = request.query_params.get("entity", None)

        if export_format not in ("json", "csv"):
            return Response(
                {"detail": "Invalid format. Use 'json' or 'csv'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # CSV requires entity type
        if export_format == "csv" and not entity_type:
            return Response(
                {
                    "detail": "Entity type is required for CSV export. "
                    "Use entity=persons, relationships, or anecdotes."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if export_format == "json":
                if entity_type:
                    content = export_entity_json(entity_type)
                    filename = f"lifegraph_{entity_type}_{date.today().isoformat()}.json"
                else:
                    content = export_all_json()
                    filename = f"lifegraph_full_export_{date.today().isoformat()}.json"

                response = HttpResponse(content, content_type="application/json")
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                return response

            else:  # CSV
                content = export_entity_csv(entity_type)
                filename = f"lifegraph_{entity_type}_{date.today().isoformat()}.csv"

                response = HttpResponse(content, content_type="text/csv")
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                return response

        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"detail": f"Export failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportPreviewView(APIView):
    """
    Preview export data without downloading.

    Returns a summary of what would be exported.
    """

    def get(self, request):
        """
        Get export preview with counts and sample data.

        Query Parameters:
            entity: Optional entity type to preview.
        """
        entity_type = request.query_params.get("entity", None)

        counts = {
            "persons": Person.objects.count(),
            "relationships": Relationship.objects.count(),
            "relationship_types": RelationshipType.objects.count(),
            "anecdotes": Anecdote.objects.count(),
            "photos": Photo.objects.count(),
            "tags": Tag.objects.count(),
            "groups": Group.objects.count(),
        }

        if entity_type:
            if entity_type not in counts:
                return Response(
                    {"detail": f"Unknown entity type: {entity_type}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response({
                "entity_type": entity_type,
                "count": counts[entity_type],
                "available_formats": ["json", "csv"] if entity_type in ["persons", "relationships", "anecdotes"] else ["json"],
            })

        return Response({
            "export_type": "full",
            "counts": counts,
            "total_items": sum(counts.values()),
            "available_formats": {
                "json": {
                    "full_export": True,
                    "entity_types": list(counts.keys()),
                },
                "csv": {
                    "full_export": False,
                    "entity_types": ["persons", "relationships", "anecdotes"],
                },
            },
        })
