from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from rest_framework.filters import BaseFilterBackend


class NearestFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        radius = request.query_params.get("radius", 10)

        if lat and lon:
            try:
                user_location = Point(float(lon), float(lat), srid=4326)

                return (
                    queryset.filter(
                        location__distance_lte=(user_location, D(km=radius))
                    )
                    .annotate(distance=Distance("location", user_location))
                    .order_by("distance")
                )

            except (ValueError, TypeError):
                return queryset

        return queryset
