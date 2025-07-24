from django.conf import settings
from django.contrib.gis.db import models

from places.utils import place_photo_path


class PlaceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    MODERATING = "moderating", "Moderating"
    REJECTED = "rejected", "Rejected"


class Place(models.Model):
    # Main information
    name = models.CharField("Name", max_length=255)
    description = models.TextField("Description", blank=True)
    location = models.PointField("Coordinates", srid=4326)
    photo = models.ImageField(
        "Photo", upload_to=place_photo_path, blank=True, null=True
    )

    # Address information
    address = models.CharField("Address", max_length=255, blank=True)
    city = models.CharField("City", max_length=100, blank=True)
    country = models.CharField("Country", max_length=100, blank=True)

    # Status and moderating
    status = models.CharField(
        "Status",
        max_length=20,
        choices=PlaceStatus.choices,
        default=PlaceStatus.DRAFT,
    )
    is_active = models.BooleanField("Active", default=True)

    # Meta data
    created_at = models.DateTimeField("Created", auto_now_add=True)
    updated_at = models.DateTimeField("Updated", auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Author",
        null=True,
        on_delete=models.SET_NULL,
        related_name="places",
    )

    class Meta:
        verbose_name = "Place"
        verbose_name_plural = "Places"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
