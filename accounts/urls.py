from rest_framework.routers import DefaultRouter

from accounts.views import (
    AdminUserViewSet,
    ProfileViewSet,
    RegistrationViewSet,
)

app_name = "accounts"

router = DefaultRouter()
router.register(r"users", AdminUserViewSet, basename="admin-user")
router.register(r"register", RegistrationViewSet, basename="register")
router.register(r"me", ProfileViewSet, basename="me")

urlpatterns = router.urls
