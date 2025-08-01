import io

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import QuerySet
from PIL import Image

from accounts.models import CustomUser
from places.models import Place, PlaceStatus


class PlaceValidationService:
    """Service for validating place data"""

    ALLOWED_IMAGE_FORMATS = ["JPEG", "PNG", "WEBP"]
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_IMAGE_DIMENSIONS = (2048, 2048)

    @classmethod
    def validate_photo(cls, photo: InMemoryUploadedFile) -> None:
        """Validation of uploaded photo"""
        if photo.size > cls.MAX_IMAGE_SIZE:
            raise ValidationError(
                f"The file size must not exceed {cls.MAX_IMAGE_SIZE // (1024 * 1024)}MB"
            )

        try:
            img = Image.open(photo)
            if img.format not in cls.ALLOWED_IMAGE_FORMATS:
                raise ValidationError(
                    f"Supported formats: {', '.join(cls.ALLOWED_IMAGE_FORMATS)}"
                )

            if (
                img.size[0] > cls.MAX_IMAGE_DIMENSIONS[0]
                or img.size[1] > cls.MAX_IMAGE_DIMENSIONS[1]
            ):
                raise ValidationError(
                    f"Maximum image sizes: {cls.MAX_IMAGE_DIMENSIONS}"
                )

        except Exception as err:
            raise ValidationError(f"Incorrect image file: {str(err)}") from err

        photo.seek(0)


class PlaceImageProcessor:
    """Service for image processing"""

    @staticmethod
    def optimize_image(photo: InMemoryUploadedFile) -> InMemoryUploadedFile:
        """Image Optimization"""
        img = Image.open(photo)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85, optimize=True)
        output.seek(0)

        return InMemoryUploadedFile(
            output,
            "ImageField",
            f"{photo.name.split('.')[0]}.jpg",
            "image/jpeg",
            len(output.getvalue()),
            None,
        )


class PlaceService:
    """Main service for working with places (coordinates other services)"""

    @staticmethod
    def create_place(serializer, user: CustomUser) -> Place:
        """Creating a new place"""
        if "photo" in serializer.validated_data:
            PlaceValidationService.validate_photo(serializer.validated_data["photo"])

            serializer.validated_data["photo"] = PlaceImageProcessor.optimize_image(
                serializer.validated_data["photo"]
            )

        return serializer.save(created_by=user, status=PlaceStatus.MODERATING)

    @staticmethod
    def update_photo(place: Place, photo: InMemoryUploadedFile) -> Place:
        """Updating the photo of the place"""
        PlaceValidationService.validate_photo(photo)
        optimized_photo = PlaceImageProcessor.optimize_image(photo)

        if place.photo:
            place.photo.delete(save=False)

        place.photo = optimized_photo
        place.save(update_fields=["photo", "updated_at"])
        return place

    @staticmethod
    def get_places_for_moderation() -> QuerySet[Place]:
        """Getting places for moderation"""
        return (
            Place.objects.filter(status=PlaceStatus.MODERATING)
            .select_related("created_by")
            .order_by("created_at")
        )


class GeospatialService:
    """Service for Geospatial Operations"""

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> tuple[bool, str]:
        """Coordinate validation"""
        if not (-90 <= lat <= 90):
            return False, "The latitude should be between -90 and 90"
        if not (-180 <= lon <= 180):
            return False, "The longitude should be between -180 and 180"
        return True, ""

    @staticmethod
    def validate_radius(radius: float) -> tuple[bool, str]:
        """Search radius validation"""
        if not (0 < radius <= 1000):
            return False, "The radius should be between 0 and 1000 km"
        return True, ""
