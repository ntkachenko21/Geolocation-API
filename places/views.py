from rest_framework.viewsets import ReadOnlyModelViewSet

from places.models import Place
from places.serializers import PlaceSerializer


class PlaceViewSet(ReadOnlyModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
