from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from accounts.serializers import UserDetailSerializer, UserPublicSerializer
from places.models import Place


class PlaceSerializer(GeoFeatureModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)
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
        extra_kwargs = {
            "status": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance(self, obj):
        """
        Returns the distance to the object in meters, if calculated.
        """
        if hasattr(obj, "distance"):
            return round(obj.distance.m, 2)
        return None

    def get_created_by(self, obj):
        """Returns user info based on permission level."""
        if not obj.created_by:
            return None

        request = self.context.get("request")
        user = request.user if request else None

        if user and user.is_authenticated and (user.is_admin or user.is_moderator):
            return UserDetailSerializer(obj.created_by).data

        return UserPublicSerializer(obj.created_by).data
