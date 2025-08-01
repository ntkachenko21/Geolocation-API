from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from places.filters import BboxSearchFilter, PlaceRadiusSearchFilter
from places.models import Place, PlaceStatus
from places.permissions import IsOwnerOrModerator
from places.serializers import PlaceSerializer
from places.services import PlaceService


class PlaceViewSet(viewsets.ModelViewSet):
    """ViewSet for place management"""

    serializer_class = PlaceSerializer
    permission_classes = [IsOwnerOrModerator]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Place.objects.filter(status=PlaceStatus.PUBLISHED).select_related(
                "created_by"
            )

        if user.is_moderator:
            return Place.objects.exclude(status=PlaceStatus.ARCHIVED).select_related(
                "created_by"
            )

        return (
            Place.objects.filter(Q(status=PlaceStatus.PUBLISHED) | Q(created_by=user))
            .exclude(status=PlaceStatus.ARCHIVED)
            .select_related("created_by")
        )

    def destroy(self, request, *args, **kwargs):
        place = self.get_object()
        place.status = PlaceStatus.ARCHIVED
        place.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        """Creating a user-defined location"""
        place = PlaceService.create_place(serializer=serializer, user=self.request.user)
        return place

    @action(
        detail=False,
        methods=["get"],
        url_path="archived",
        permission_classes=[IsAdminUser],
    )
    def archived_places(self, request):
        """
        Returns a list of archived locations.
        Available for administrators only.
        """
        archived_queryset = Place.objects.filter(
            status=PlaceStatus.ARCHIVED
        ).select_related("created_by")

        page = self.paginate_queryset(archived_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(archived_queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="upload-photo")
    def upload_photo(self, request, pk=None):
        """Separate endpoint for uploading photos"""
        place = self.get_object()
        photo = request.FILES.get("photo")

        if not photo:
            return Response(
                {"error": "Photo file is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        updated_place = PlaceService.update_photo(place, photo)
        serializer = self.get_serializer(updated_place)
        return Response(serializer.data)


class BaseSearchListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PlaceSerializer
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return Place.objects.filter(status=PlaceStatus.PUBLISHED).select_related(
            "created_by"
        )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="lat",
            description="Latitude of the user's current location.",
            required=True,
            type=float,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample("Kraków latitude", value="50.0613")],
        ),
        OpenApiParameter(
            name="lon",
            description="Longitude of the user's current location.",
            required=True,
            type=float,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample("Kraków longitude", value="19.937")],
        ),
        OpenApiParameter(
            name="radius",
            description="Search radius in kilometers (default: 5, max: 1000).",
            required=False,
            type=float,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample("5 km radius", value="5")],
        ),
    ]
)
class PlaceRadiusSearchViewSet(BaseSearchListViewSet):
    """
    Search for places within a specified radius from given coordinates.
    """

    filterset_class = PlaceRadiusSearchFilter


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="in_bbox",
            description="Filter by bounding box."
            " Format: min_lon,min_lat,max_lon,max_lat",
            required=True,
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[
                OpenApiExample(
                    "Kraków Main Square Area", value="19.93,50.06,19.94,50.065"
                ),
                OpenApiExample("Warsaw (City)", value="20.85,52.09,21.27,52.36"),
                OpenApiExample(
                    "Poland (whole country)", value="14.12,49.00,24.14,54.83"
                ),
                OpenApiExample(
                    "Ukraine (whole country)", value="22.13,44.38,40.22,52.37"
                ),
            ],
        ),
        OpenApiParameter(
            name="lat",
            description="User's latitude"
            " (optional, for distance calculation and sorting)",
            required=False,
            type=float,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample("Kraków latitude", value="50.0613")],
        ),
        OpenApiParameter(
            name="lon",
            description="User's longitude"
            " (optional, for distance calculation and sorting)",
            required=False,
            type=float,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample("Kraków longitude", value="19.937")],
        ),
    ]
)
class PlaceBboxSearchViewSet(BaseSearchListViewSet):
    """
    Search for places within a given bounding box.
    Optionally sort by distance if user coordinates are provided.
    """

    filterset_class = BboxSearchFilter
