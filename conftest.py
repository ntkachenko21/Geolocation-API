import factory.django
import pytest
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient

from accounts.models import CustomUser, UserRole
from places.models import Place


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Test"
    last_name = factory.Sequence(lambda n: f"User{n}")
    password = factory.PostGenerationMethodCall("set_password", "VerySecret12345")

    @factory.post_generation
    def save_user(obj, create, extracted, **kwargs):
        obj.save()


class PlaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Place

    name = factory.Sequence(lambda n: f"Place{n}")
    location = Point(19.946083279790873, 50.06771748395846)

    created_by = factory.SubFactory(UserFactory)


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def place_factory():
    return PlaceFactory


@pytest.fixture
def authenticated_client(user_factory):
    """Creates and returns a fully isolated client authenticated as a regular user"""
    client = APIClient()
    user = user_factory()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def admin_user(user_factory):
    return user_factory(role=UserRole.ADMIN, is_staff=True, is_superuser=True)


@pytest.fixture
def admin_client(admin_user):
    """Creates and returns a fully isolated client authenticated as an admin"""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
