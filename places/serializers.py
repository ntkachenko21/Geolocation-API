from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from places.models import Place


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class PlaceSerializer(GeoFeatureModelSerializer):
    created_by = UserSerializer(read_only=True)
    distance = serializers.SerializerMethodField(read_only=True)

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
            "created_at",
            "updated_at",
            "created_by",
            "distance",
        )

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance(self, obj):
        """
        Returns the distance to the object in meters, if calculated.
        """
        if hasattr(obj, "distance"):
            return round(obj.distance.m, 2)
        return None
