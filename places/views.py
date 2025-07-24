from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_gis.filters import InBBoxFilter

from places.filters import NearestFilter
from places.models import Place
from places.serializers import PlaceSerializer


class PlaceViewSet(ReadOnlyModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    filter_backends = [NearestFilter, InBBoxFilter]

    bbox_filter_field = "location"
    bbox_filter_include_overlapping = True
