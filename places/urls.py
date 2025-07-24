from rest_framework.routers import DefaultRouter

from places.views import PlaceBboxSearchViewSet, PlaceRadiusSearchViewSet, PlaceViewSet

app_name = "places"

router = DefaultRouter()
router.register(r"", PlaceViewSet, basename="place")
router.register(r"search/radius", PlaceRadiusSearchViewSet, basename="search-radius")
router.register(r"search/bbox", PlaceBboxSearchViewSet, basename="search-bbox")

urlpatterns = router.urls
