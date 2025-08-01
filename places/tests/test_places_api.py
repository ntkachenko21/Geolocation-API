import pytest
from django.contrib.gis.geos import Point

from accounts.models import UserRole
from places.models import Place, PlaceStatus


@pytest.mark.django_db
class TestPlacePermissions:
    def test_create_place_by_unauthenticated_user(self, client):
        """An anonymous user cannot create a location"""

        url = "/api/v1/places/"
        place_data = {
            "name": "Some Place",
            "description": "Description of some place",
            "location": {"type": "Point", "coordinates": [10.0, 20.0]},
        }

        response = client.post(url, data=place_data, format="json")

        assert response.status_code == 401
        assert Place.objects.count() == 0
        assert (
            response.data["detail"] == "Authentication credentials were not provided."
        )

    def test_create_place_by_authenticated_user(self, authenticated_client):
        """An authenticated user can create a location"""

        client, user = authenticated_client

        url = "/api/v1/places/"
        place_data = {
            "name": "Some Place",
            "description": "Description of some place",
            "location": {"type": "Point", "coordinates": [10.0, 20.0]},
        }

        response = client.post(url, data=place_data, format="json")

        new_place = Place.objects.first()

        assert response.status_code == 201
        assert Place.objects.count() == 1
        assert new_place.name == place_data["name"]
        assert new_place.created_by == user

    def test_update_place_by_owner_succeeds(self, authenticated_client, place_factory):
        """The owner can update his place"""

        client, user = authenticated_client
        place = place_factory(created_by=user, status=PlaceStatus.PUBLISHED)
        url = f"/api/v1/places/{place.pk}/"
        updated_data = {"name": "New name"}

        response = client.patch(url, data=updated_data)

        assert response.status_code == 200

        place.refresh_from_db()
        assert place.name == updated_data["name"]

    def test_update_place_by_other_user_fails(
        self, authenticated_client, user_factory, place_factory
    ):
        """A user cannot update someone else's place"""

        owner_user = user_factory()
        place = place_factory(created_by=owner_user, status=PlaceStatus.PUBLISHED)

        client, other_user = authenticated_client

        url = f"/api/v1/places/{place.pk}/"
        updated_data = {"name": "New name"}
        response = client.patch(url, data=updated_data)

        assert response.status_code == 403

        place.refresh_from_db()
        assert place.name != updated_data["name"]

    def test_update_place_by_admin_succeeds(
        self, admin_client, place_factory, user_factory
    ):
        """An admin can update someone else's place"""

        owner_user = user_factory()
        place = place_factory(created_by=owner_user, status=PlaceStatus.PUBLISHED)

        url = f"/api/v1/places/{place.pk}/"
        updated_data = {"name": "New name"}
        response = admin_client.patch(url, data=updated_data)

        assert response.status_code == 200

        place.refresh_from_db()
        assert place.name == updated_data["name"]

    def test_delete_place_by_owner_succeeds(self, authenticated_client, place_factory):
        """The owner can remove his place"""

        client, user = authenticated_client
        place = place_factory(created_by=user, status=PlaceStatus.PUBLISHED)

        assert Place.objects.filter(status=PlaceStatus.PUBLISHED).count() == 1
        assert Place.objects.filter(status=PlaceStatus.ARCHIVED).count() == 0

        url = f"/api/v1/places/{place.pk}/"
        response = client.delete(url)

        assert response.status_code == 204
        assert Place.objects.filter(status=PlaceStatus.PUBLISHED).count() == 0
        assert Place.objects.filter(status=PlaceStatus.ARCHIVED).count() == 1

    def test_delete_place_by_admin_succeeds(
        self, admin_client, place_factory, user_factory
    ):
        """The admin can delete any place"""

        owner_user = user_factory()
        place = place_factory(created_by=owner_user, status=PlaceStatus.PUBLISHED)

        url = f"/api/v1/places/{place.pk}/"
        response = admin_client.delete(url)

        assert response.status_code == 204
        assert Place.objects.filter(status=PlaceStatus.PUBLISHED).count() == 0
        assert Place.objects.filter(status=PlaceStatus.ARCHIVED).count() == 1


@pytest.mark.django_db
class TestPlaceAPIFunctionality:
    def test_list_places_only_shows_published(
        self, client, place_factory, user_factory
    ):
        """
        Only places with PUBLISHED status are displayed
        in the general list of places
        """

        published_place = place_factory(status=PlaceStatus.PUBLISHED)
        place_factory(status=PlaceStatus.ARCHIVED)
        place_factory(status=PlaceStatus.DRAFT)
        place_factory(status=PlaceStatus.MODERATING)

        url = "/api/v1/places/"
        response = client.get(url)
        assert response.status_code == 200

        response_data = response.data
        assert response_data["count"] == 1

        results = response_data["results"]["features"]
        assert len(results) == 1

        result_place_data = results[0]
        assert result_place_data["properties"]["name"] == published_place.name
        assert result_place_data["id"] == published_place.id

    def test_created_by_serialization_for_regular_user(
        self, authenticated_client, place_factory, user_factory
    ):
        """
        For a regular user, the information about
        the place creator is brief (PublicUserSerializer)
        """

        client, user = authenticated_client
        place_factory(created_by=user, status=PlaceStatus.PUBLISHED)

        url = "/api/v1/places/"
        response = client.get(url)

        assert response.status_code == 200

        response_data = response.data["results"]["features"][0]["properties"][
            "created_by"
        ]
        assert len(response_data) == 3

    def test_created_by_serialization_for_admin_user(
        self, place_factory, admin_client, user_factory
    ):
        """For admin the information about the place creator is full"""
        regular_user = user_factory(role=UserRole.USER)
        place = place_factory(created_by=regular_user, status=PlaceStatus.PUBLISHED)

        url = f"/api/v1/places/{place.id}/"
        response = admin_client.get(url)

        assert response.status_code == 200

        response_data = response.data["properties"]["created_by"]
        assert len(response_data) == 9


@pytest.mark.django_db
class TestPlaceSearchAPI:
    def test_search_by_radius_returns_correct_places(
        self, authenticated_client, place_factory
    ):
        """
        The radius search returns only locations
        that fall within the specified radius
        """
        client, user = authenticated_client

        lat = 50.0613
        lon = 19.937
        radius = 5

        place_in_radius = place_factory(
            name="Place Inside",
            status=PlaceStatus.PUBLISHED,
            location=Point(19.945, 50.062),  # ~1km from curren user location
        )
        place_out_of_radius = place_factory(
            name="Place Outside",
            status=PlaceStatus.PUBLISHED,
            location=Point(
                21.0122, 52.2297
            ),  # Warsaw, ~250km from current user location
        )

        url = f"/api/v1/places/search/radius/?lat={lat}&lon={lon}&radius={radius}"

        response = client.get(url)

        assert response.status_code == 200

        results = response.data["results"]["features"]
        assert len(results) == 1

        found_place_id = results[0]["id"]
        assert found_place_id == place_in_radius.id
        assert found_place_id != place_out_of_radius.id

    def test_search_by_bbox_returns_correct_places(self, client, place_factory):
        """
        Searching the bounding rectangle returns
        only locations that fall within the specified boundaries
        """

        in_bbox_poland = "14.12%2C49.00%2C24.14%2C54.83"  # Area of entire Poland
        in_bbox_warsaw = "20.85%2C52.09%2C21.27%2C52.36"  # Area of Warsaw city

        place_in_cracow = place_factory(
            name="Kraków", status=PlaceStatus.PUBLISHED, location=Point(19.945, 50.062)
        )
        place_in_warsaw = place_factory(
            name="Warsaw",
            status=PlaceStatus.PUBLISHED,
            location=Point(21.0122, 52.2297),
        )

        url_poland = f"/api/v1/places/search/bbox/?in_bbox={in_bbox_poland}"
        response_poland = client.get(url_poland)
        url_warsaw = f"/api/v1/places/search/bbox/?in_bbox={in_bbox_warsaw}"
        response_warsaw = client.get(url_warsaw)

        assert response_poland.status_code == 200
        assert response_warsaw.status_code == 200

        results_poland = response_poland.data["results"]["features"]
        results_warsaw = response_warsaw.data["results"]["features"]

        assert len(results_poland) == 2
        assert len(results_warsaw) == 1

        expected_poland_ids = {place_in_cracow.id, place_in_warsaw.id}
        received_poland_ids = {item["id"] for item in results_poland}
        assert received_poland_ids == expected_poland_ids

        assert results_warsaw[0]["id"] == place_in_warsaw.id

    def test_search_by_radius_without_coords_fails(
        self, authenticated_client, place_factory
    ):
        """Searching by radius without coordinates returns error 400"""
        client, user = authenticated_client
        url = "/api/v1/places/search/radius/?radius=5"

        response = client.get(url)

        assert response.status_code == 400

        assert "The parameters 'lat' and 'lon' are mandatory for radius search" in str(
            response.data
        )
