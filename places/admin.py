from django.contrib.gis import admin

from places.models import Place


@admin.register(Place)
class PlaceAdmin(admin.GISModelAdmin):
    list_display = ("name", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "description")
