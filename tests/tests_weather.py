from random import randint
from unittest.mock import Mock, patch, sentinel
from urllib.parse import urlencode

from django.db.models import F
from django.test import TestCase, Client
from django.urls import reverse
from django.core.paginator import Paginator

import weatherapp.weather.views
from weatherapp.weather.models import Location, UserLocation, User
from weatherapp.external_services.openweathermap.geocodingapi.responsedto import GeocodingLocationDto
from weatherapp.external_services.openweathermap.errors import OpenweathermapApiHTTPResponseError


class WeatherAppBaseViewTestCase(TestCase):
    fixtures = ['weatherapp-testdata.json']
    _mocked_method_name: str

    def setUp(self) -> None:
        self.client = Client()
        self.openweathermap_patcher = patch('weatherapp.weather.views.openweathermap')
        self.mock_openweathermap = self.openweathermap_patcher.start()
        return_value = getattr(self, '_mock_return_value', None) or sentinel
        if isinstance(return_value, type):
            return_value = return_value()
        if hasattr(self, '_mocked_method_name'):
            setattr(self.mock_openweathermap, self._mocked_method_name, Mock(return_value=return_value))

    def tearDown(self) -> None:
        self.openweathermap_patcher.stop()

    def login_user(self, username: str):
        user = User.objects.get(username=username)
        self.client.force_login(user)
        return user

    def get_login_url(self, _next: str | None = None):
        path = reverse('users:login')
        if _next:
            path = path + '?' + urlencode({'next': _next})
        return path


class IndexViewTestCase(WeatherAppBaseViewTestCase):
    REQUEST_URL = reverse('index')
    fixtures = ['weatherapp-testdata.json']
    _mocked_method_name = 'get_current_weather_data'

    def test_requestIsSuccessful(self):
        user = self.login_user(username='Gevorji')
        response = self.client.get(self.REQUEST_URL)

        ctxt = response.context

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            Location.objects.filter(
                users=user
            ).annotate(
                date_added=F('userlocation__date_added')
            ).order_by('-date_added')[:weatherapp.weather.views.NLOCATIONS_ON_PAGE],
            [locw[0] for locw in ctxt['locations_weather']]
        )

    def test_rendersGuestIndexOnRequestFromUnauthorized(self):
        response = self.client.get(self.REQUEST_URL)
        self.assertTemplateUsed(response, 'weather/guest_index.html')


class IndexViewPaginationTest(IndexViewTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.user = self.login_user(username='Gevorji')
        self.paginator = Paginator(
            Location.objects.filter(users=self.user).annotate(
                date_added=F('userlocation__date_added')
            ).order_by('-date_added'), weatherapp.weather.views.NLOCATIONS_ON_PAGE
        )

    def test_requestWithNoPageNumGivenReturnsFirstPage(self):
        response = self.client.get(self.REQUEST_URL)

        ctxt = response.context

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ctxt['locations_page'].number, 1)

    def test_requestForValidPageIsOk(self):
        page_n = randint(1, self.paginator.num_pages)
        response = self.client.get(self.REQUEST_URL, {'page': page_n})
        ctxt = response.context

        self.assertEqual(ctxt['locations_page'].number, page_n)

    def test_requestWithPageNumMoreThanOverallNumReturnsLastPage(self):
        response = self.client.get(self.REQUEST_URL, {'page': self.paginator.num_pages + 1})
        self.assertEqual(response.context['locations_page'].number, self.paginator.num_pages)

    def test_requestWithPageNumWhichIsNotAPositiveDecimal(self):
        for page_n in [1.1, 'a', -1]:
            with self.subTest(page_n=page_n):
                response = self.client.get(self.REQUEST_URL, {'page': page_n})
                self.assertEqual(response.context['locations_page'].number, 1)


class LocationViewTest(WeatherAppBaseViewTestCase):
    REQUEST_URL = reverse('weather:locations')
    fixtures = ['weatherapp-testdata.json']
    LOCATIONS_PAGE_TMPL_NAME = 'weather/locations.html'
    _mocked_method_name = 'get_locations_by_name'
    _mock_return_value = list

    def test_requestForLocationIsSuccessful(self):
        self.login_user(username='Gevorji')
        for name in ['Moscow', 'moscow']:
            with self.subTest(name=name):
                setattr(self.mock_openweathermap, self._mocked_method_name, Mock(return_value=list()))
                response = self.client.get(self.REQUEST_URL, query_params={'name': name})
                self.assertEqual(response.status_code, 200)
                self.assertQuerySetEqual(
                    Location.objects.filter(name__icontains=name), response.context.get('locations_list')
                )

    def test_redirectsOnRequestFromUnauthorizedUser(self):
        response = self.client.get(self.REQUEST_URL)
        self.assertRedirects(response, self.get_login_url(self.REQUEST_URL))

    def test_requestWithNoLocationNameIsOk(self):
        self.login_user(username='Gevorji')
        response = self.client.get(self.REQUEST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['locations_list'])

    def test_requestPopulatesSessionsLatelyRequestedLocations(self):
        self.login_user(username='Gevorji')
        self.client.get(self.REQUEST_URL, query_params={'name': 'Moscow'})
        lately_requested = self.client.session.get('lately_requested_locations')
        self.assertTrue(lately_requested)
        self.assertQuerySetEqual(
            Location.objects.filter(name__icontains='Moscow').values_list('id', flat=True), lately_requested
        )

    def test_commonApiAndDbLocationExcludedFromResultLocationsList(self):
        self.login_user(username='Gevorji')

        api_locations = [
            GeocodingLocationDto(
                name='Moscow', latitude=55.7504461, longitude=37.6174943, country='RU', local_names={}, state='Moscow'
            ),
            GeocodingLocationDto(
                name='Moscow', latitude=46.7323875, longitude=-117.0001651, country='US', local_names={}, state='Idaho'
            )
        ]
        another_moscow_m = Location(
            name=api_locations[1].name, local_names=api_locations[1].local_names,
            latitude=api_locations[1].latitude, longitude=api_locations[1].longitude,
        )

        setattr(self.mock_openweathermap, self._mocked_method_name, Mock(return_value=api_locations))

        response = self.client.get(self.REQUEST_URL, query_params={'name': 'mo'})
        locations_list = response.context.get('locations_list')
        correct_locations_list = list(Location.objects.filter(name__icontains='mo')) + [another_moscow_m]

        self.assertCountEqual(
            [(loc.name, loc.latitude, loc.longitude) for loc in locations_list],
            [(loc.name, loc.latitude, loc.longitude) for loc in correct_locations_list]
        )

    def test_additionOfNewLocationThatExistedInDbIsSuccessful(self):
        user = self.login_user(username='Mitrandir')

        self.client.get(self.REQUEST_URL, query_params={'name': 'Mo'})
        added_location_pk = self.client.session.get('lately_requested_locations')[0]
        response = self.client.post(self.REQUEST_URL, {'location': 0})

        self.assertRedirects(response, '/')
        self.assertTrue(UserLocation.objects.filter(user=user, location_id=added_location_pk))
        self.assertFalse(self.client.session.get('lately_requested_locations'))

    def test_additionOfNewLocationRetainedFromApiIsSuccessful(self):
        user = self.login_user(username='Mitrandir')
        api_locations = [
            GeocodingLocationDto(
                name='Saint Petersburg', latitude=59.938732, longitude=30.316229, country='RU', local_names={}
            )
        ]
        setattr(self.mock_openweathermap, self._mocked_method_name, Mock(return_value=api_locations))
        self.client.get(self.REQUEST_URL, query_params={'name': 'Saint Petersburg'})

        response = self.client.post(self.REQUEST_URL, {'location': 0})

        self.assertRedirects(response, '/')
        self.assertTrue(UserLocation.objects.filter(user=user, location=Location.objects.get(name='Saint Petersburg')))
        self.assertFalse(self.client.session.get('lately_requested_locations'))

    def test_additionOfAlreadyAddedLocationDoesNothing(self):
        user = self.login_user(username='Gevorji')

        self.client.get(self.REQUEST_URL, query_params={'name': 'Mozdok'})
        added_location_pk = self.client.session.get('lately_requested_locations')[0]
        response = self.client.post(self.REQUEST_URL, {'location': 0})

        self.assertRedirects(response, '/')
        self.assertEqual(UserLocation.objects.filter(user=user, location_id=added_location_pk).count(), 1)
        self.assertFalse(self.client.session.get('lately_requested_locations'))

    def test_additionWhenNoLocationWasRequestedRespondsWithOk(self):
        user = self.login_user(username='Gevorji')

        response = self.client.post(self.REQUEST_URL, {'location': 0})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.LOCATIONS_PAGE_TMPL_NAME)
        self.assertFalse(self.client.session.get('lately_requested_locations'))

    def test_addedLocationNumberIsInappropriate(self):
        user = self.login_user(username='Gevorji')

        for selected_loc in [1, -1, 'a']:
            with self.subTest(selected_loc=selected_loc):
                self.client.get(self.REQUEST_URL, query_params={'name': 'Mozdok'})
                response = self.client.post(self.REQUEST_URL, {'location': selected_loc})
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, self.LOCATIONS_PAGE_TMPL_NAME)
                self.assertFalse(self.client.session.get('lately_requested_locations'))

    def test_externalServiceRaisesAnErrorIsOk(self):
        user = self.login_user(username='Gevorji')

        setattr(
            self.mock_openweathermap, self._mocked_method_name, Mock(
                side_effect=OpenweathermapApiHTTPResponseError(500, 'Internal server bla bla')
            )
        )

        response = self.client.get(self.REQUEST_URL, query_params={'name': 'Moscow'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.LOCATIONS_PAGE_TMPL_NAME)


class LocationRemoveView(WeatherAppBaseViewTestCase):
    fixtures = ['weatherapp-testdata.json']
    REQUEST_URL = reverse('weather:locations-remove')

    def test_deletionIsSuccessful(self):
        user = self.login_user(username='Gevorji')

        deleted_user_location_id = Location.objects.get(name='Mozdok').id

        response = self.client.post(self.REQUEST_URL, {'id': deleted_user_location_id})

        self.assertRedirects(response, '/')
        self.assertFalse(UserLocation.objects.filter(pk=deleted_user_location_id))

    def test_redirectsOnRequestFromUnauthorizedUser(self):
        response = self.client.post(self.REQUEST_URL, {'id': '1'})

        self.assertRedirects(response, reverse('users:login'))

    def test_respondsWith400OnRequestWithoutOrWithWrongUserLocationId(self):
        user = self.login_user(username='Gevorji')
        for _id in ('', 'a'):
            with self.subTest(_id=_id):
                if not _id:
                    response = self.client.post(self.REQUEST_URL)
                else:
                    response = self.client.post(self.REQUEST_URL, {'id': _id})
                self.assertEquals(response.status_code, 400)

    def test_raisesHttp404OnNonExistingUserLocation(self):
        user = self.login_user(username='Gevorji')

        non_existing_ul_id = UserLocation.objects.exclude(user=user).values_list('id', flat=True).first()
        response = self.client.post(self.REQUEST_URL, {'id': non_existing_ul_id})
        self.assertEqual(response.status_code, 404)
