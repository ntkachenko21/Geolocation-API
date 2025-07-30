import django_filters
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from rest_framework.exceptions import ParseError

from places.models import Place, PlaceStatus
from places.services import GeospatialService


class BaseGeospatialFilter(django_filters.FilterSet):
    """Base class for geospatial filters"""

    def _get_user_location(self, params) -> Point | None:
        """Getting user location from parameters"""
        lon = params.get("lon")
        lat = params.get("lat")

        if lat and lon:
            try:
                lat_val, lon_val = float(lat), float(lon)
                is_valid, error_msg = GeospatialService.validate_coordinates(
                    lat_val, lon_val
                )

                if not is_valid:
                    raise ParseError(error_msg)
                return Point(lon_val, lat_val, srid=4326)
            except (ValueError, TypeError) as err:
                raise ParseError("Incorrect user coordinates") from err
        return None

    def _add_distance_annotation(self, queryset, user_location: Point):
        """Adding distance annotation and sorting"""
        return queryset.annotate(distance=Distance("location", user_location)).order_by(
            "distance"
        )


class PlaceRadiusSearchFilter(BaseGeospatialFilter):
    """Search filter for places in the radius"""

    DEFAULT_RADIUS = 5.0

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        params = self.request.query_params

        lon = params.get("lon")
        lat = params.get("lat")

        if not (lon and lat):
            raise ParseError(
                "The parameters 'lat' and 'lon' are mandatory for radius search"
            )

        radius = params.get("radius", self.DEFAULT_RADIUS)

        try:
            lat_val, lon_val, radius_val = float(lat), float(lon), float(radius)

            is_coord_valid, coord_error = GeospatialService.validate_coordinates(
                lat_val, lon_val
            )
            if not is_coord_valid:
                raise ParseError(coord_error)

            is_radius_valid, radius_error = GeospatialService.validate_radius(
                radius_val
            )
            if not is_radius_valid:
                raise ParseError(radius_error)

            user_location = Point(lon_val, lat_val, srid=4326)

            queryset = queryset.filter(
                location__distance_lte=(user_location, D(km=radius_val))
            )

            return self._add_distance_annotation(queryset, user_location)

        except (ValueError, TypeError) as err:
            raise ParseError(
                "Incorrect parameters. 'lat', 'lon' and 'radius' must be numbers"
            ) from err


class BboxSearchFilter(BaseGeospatialFilter):
    """Search filter for places in the bounding rectangle"""

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        params = self.request.query_params

        bbox_str = params.get("in_bbox")
        if not bbox_str:
            raise ParseError("The 'in_bbox' parameter is mandatory")

        try:
            coords = self._parse_bbox(bbox_str)
            poly = Polygon.from_bbox(coords)
            queryset = queryset.filter(location__bboverlaps=poly)

            user_location = self._get_user_location(params)
            if user_location:
                queryset = self._add_distance_annotation(queryset, user_location)

            return queryset

        except (ValueError, IndexError) as err:
            raise ParseError(f"Incorrect format 'in_bbox': {str(err)}") from err

    def _parse_bbox(self, bbox_str: str) -> tuple[float, float, float, float]:
        """Parsing and validation bbox"""
        coords = [float(x.strip()) for x in bbox_str.split(",")]

        if len(coords) != 4:
            raise ValueError("Expected 4 coordinates")

        min_lon, min_lat, max_lon, max_lat = coords

        for lat in [min_lat, max_lat]:
            is_valid, error = GeospatialService.validate_coordinates(lat, 0)
            if not is_valid:
                raise ValueError(f"Incorrect latitude: {lat}")

        for lon in [min_lon, max_lon]:
            is_valid, error = GeospatialService.validate_coordinates(0, lon)
            if not is_valid:
                raise ValueError(f"Incorrect longitude: {lon}")

        if min_lon >= max_lon or min_lat >= max_lat:
            raise ValueError("Incorrect bounding rectangle")

        return min_lon, min_lat, max_lon, max_lat


class PlaceStatusFilter(django_filters.FilterSet):
    """Filter by place status (for admins/moderators)"""

    status = django_filters.ChoiceFilter(choices=PlaceStatus.choices)
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Place
        fields = ["status", "created_after", "created_before"]
