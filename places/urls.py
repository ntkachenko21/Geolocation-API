from rest_framework.routers import DefaultRouter

from places.views import PlaceViewSet

app_name = "places"

router = DefaultRouter()
router.register("", PlaceViewSet, basename="places")

urlpatterns = router.urls
