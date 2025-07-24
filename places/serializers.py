from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from places.models import Place


class PlaceSerializer(GeoFeatureModelSerializer):
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Place
        geo_field = "location"
        fields = (
            "id",
            "name",
            "description",
            "photo",
            "address",
            "city",
            "country",
            "status",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "distance",
        )

    def get_distance(self, obj):
        if hasattr(obj, "distance"):
            return round(obj.distance.m, 2)
        return None
