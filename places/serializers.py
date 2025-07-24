from rest_framework_gis.serializers import GeoFeatureModelSerializer

from places.models import Place


class PlaceSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Place
        geo_field = "location"
        fields = "__all__"
