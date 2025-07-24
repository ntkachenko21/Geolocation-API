import django_filters
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from rest_framework.exceptions import ParseError


class PlaceRadiusSearchFilter(django_filters.FilterSet):
    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        params = self.request.query_params

        lat = params.get("lat")
        lon = params.get("lon")
        radius = params.get("radius", 10)

        if lat and lon:
            try:
                lat_val = float(lat)
                lon_val = float(lon)
                radius_val = float(radius)

                if not (-90 <= lat_val <= 90):
                    raise ParseError("Latitude must be between -90 and 90")
                if not (-180 <= lon_val <= 180):
                    raise ParseError("Longitude must be between -180 and 180")
                if not (0 < radius_val <= 1000):
                    raise ParseError("Radius must be between 0 and 1000 km")

                user_location = Point(lon_val, lat_val, srid=4326)

                return (
                    queryset.filter(
                        location__distance_lte=(user_location, D(km=radius_val))
                    )
                    .annotate(distance=Distance("location", user_location))
                    .order_by("distance")
                )

            except (ValueError, TypeError) as err:
                raise ParseError(
                    "Incorrect parameters for radius search."
                    " 'lat', 'lon' and 'radius' should be numbers."
                ) from err

        return queryset


class BboxSearchFilter(django_filters.FilterSet):
    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        params = self.request.query_params

        bbox_str = params.get("in_bbox")
        if not bbox_str:
            raise ParseError("Parameter 'in_bbox' is required")

        try:
            coords = [float(x) for x in bbox_str.split(",")]
            if len(coords) != 4:
                raise ValueError("Expected 4 coordinates")

            min_lon, min_lat, max_lon, max_lat = coords

            if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
                raise ValueError("Invalid longitude values")
            if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
                raise ValueError("Invalid latitude values")
            if min_lon >= max_lon or min_lat >= max_lat:
                raise ValueError("Invalid bounding box")

            poly = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))
            queryset = queryset.filter(location__bboverlaps=poly)

        except (ValueError, IndexError) as err:
            raise ParseError(f"Incorrect format for 'in_bbox': {str(err)}") from err

        lat = params.get("lat")
        lon = params.get("lon")

        if lat and lon:
            try:
                user_location = Point(float(lon), float(lat), srid=4326)
                queryset = queryset.annotate(
                    distance=Distance("location", user_location)
                ).order_by("distance")
            except (ValueError, TypeError):
                pass

        return queryset
