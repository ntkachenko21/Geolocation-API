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
    name = models.CharField(
        "Name", max_length=255, help_text="The name of the place or establishment."
    )
    description = models.TextField(
        "Description", blank=True, help_text="A detailed description of the location."
    )
    location = models.PointField(
        "Coordinates", srid=4326, help_text="Geographic coordinates (point)."
    )
    photo = models.ImageField(
        "Photo",
        upload_to=place_photo_path,
        blank=True,
        null=True,
        help_text="A representative photo of the place.",
    )

    # Address information
    address = models.CharField(
        "Address",
        max_length=255,
        blank=True,
        help_text="The specific street address of the place.",
    )
    city = models.CharField(
        "City",
        max_length=100,
        blank=True,
        help_text="The city where the place is located.",
    )
    country = models.CharField(
        "Country",
        max_length=100,
        blank=True,
        help_text="The country where the place is located.",
    )

    # Status and moderating
    status = models.CharField(
        "Status",
        max_length=20,
        choices=PlaceStatus.choices,
        default=PlaceStatus.DRAFT,
        help_text="The current moderation status of the place.",
    )

    # Meta data
    created_at = models.DateTimeField(
        "Created", auto_now_add=True, help_text="Timestamp when the place was created."
    )
    updated_at = models.DateTimeField(
        "Updated", auto_now=True, help_text="Timestamp of the last update to the place."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Author",
        null=True,
        on_delete=models.SET_NULL,
        related_name="places",
        help_text="The user who originally created this place.",
    )

    class Meta:
        verbose_name = "Place"
        verbose_name_plural = "Places"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.city}"
