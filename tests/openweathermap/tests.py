import os
import json
from io import BytesIO
from pathlib import Path
from typing import Collection
from urllib.parse import urlparse, parse_qs, urlunparse, ParseResult
from urllib.error import HTTPError
from unittest import TestCase
from unittest.mock import Mock, patch
from importlib import reload

from dotenv import dotenv_values

tests_dir = Path(__file__).parent
os.environ.update(dotenv_values(str(tests_dir / '.env.test')))

from weatherapp.external_services import openweathermap
from weatherapp.external_services.openweathermap.currentweatherdata.responsedto import CurrentWeatherDto
from weatherapp.external_services.openweathermap.geocodingapi.responsedto import GeocodingLocationDto
from weatherapp.external_services.openweathermap.errors import OpenweathermapApiHTTPResponseError

reload(openweathermap)

print(openweathermap.settings.OPENWEATHERMAP_CURRENTWEATHERDATA_API_URL)

response_fixtures = json.load(open(tests_dir / 'response-fixtures.json', 'rb'))

config = {**dotenv_values('.env'), **dotenv_values('.env.test'), **os.environ}
APP_ID = config.get('OPENWEATHERMAP_API_KEY')


def to_json_as_bytes_stream(obj):
    return BytesIO(json.dumps(obj).encode())


class BaseOpenweathermapApiTestCase(TestCase):
    mock_requester: Mock

    def setUp(self) -> None:
        self.mock_requester = Mock(return_value=self.mock_response)
        patcher = patch('weatherapp.external_services.openweathermap.com.requestclients.urlopen', self.mock_requester)
        patcher.start()
        self.addCleanup(patcher.stop)

    def do_post_api_call_base_assertions(self, response, mock: Mock, url_base, url_query, *, response_is_inst=None):
        if response_is_inst is not None:
            if isinstance(response, Collection):
                for item in response:
                    self.assertIsInstance(item, response_is_inst)
            else:
                self.assertIsInstance(response, response_is_inst)
        actual_urlp = urlparse(mock.call_args.args[0])
        actual_request_params = {k: v[0] for k, v in parse_qs(actual_urlp.query).items()}
        self.assertEqual(
            urlunparse(
                ParseResult(
                    scheme=actual_urlp.scheme, netloc=actual_urlp.netloc, path=actual_urlp.path,
                    params='', query='', fragment=''
                ),
            ), url_base
        )
        self.assertEqual(actual_request_params, url_query)

    def do_requester_error_response_base_test(self, api_caller, args, kwargs, exc):
        self.mock_requester.configure_mock(side_effect=exc)

        with self.assertRaises(OpenweathermapApiHTTPResponseError) as cm:
            api_caller(*args, **kwargs)
        client_exc = cm.exception

        self.assertEqual(client_exc.code, exc.code)
        self.assertEqual(client_exc.phrase, exc.reason)
        self.mock_requester.reset_mock(side_effect=True)


class CurrentWeatherDataApiTestWithStlibRequestClientTest(BaseOpenweathermapApiTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.mock_response = to_json_as_bytes_stream(response_fixtures['CurrentWeatherDto'])
        cls.call_params = {
            'latitude': '20.1234', 'longitude': '20.1234',
            'language': openweathermap.ResponseLanguages.ENGLISH,
            'units': openweathermap.MeasurementUnits.METRIC
        }
        cls.request_query_params = {
            'lat': cls.call_params['latitude'], 'lon': cls.call_params['longitude'],
            'appid': APP_ID, 'units': cls.call_params['units'].value,
            'lang': cls.call_params['language'].value
        }

    def test_requestIsSuccessful(self):
        response = openweathermap.get_current_weather_data(**self.call_params)

        self.do_post_api_call_base_assertions(
            response, self.mock_requester, config.get('OPENWEATHERMAP_CURRENTWEATHERDATA_API_URL'),
            self.request_query_params, response_is_inst=CurrentWeatherDto
        )

    def test_requestClientGotHttpError(self):
        self.do_requester_error_response_base_test(
            openweathermap.get_current_weather_data, args=tuple(), kwargs=self.call_params,
            exc=HTTPError(
                code=500, msg='Internal server error', fp=BytesIO(b''), hdrs=[], url=''
            )
        )


class GeocodingApiWithStlibRequestClientTest(BaseOpenweathermapApiTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.mock_response = to_json_as_bytes_stream(response_fixtures['GeocodingLocationDto'])
        cls.call_params = {
            'name': 'Moscow',
            'limit': 3
        }
        cls.request_query_params = {'q': 'Moscow', 'limit': '3', 'appid': APP_ID}

    def test_requestIsSuccessful(self):
        response = openweathermap.get_locations_by_name(**self.call_params)

        self.do_post_api_call_base_assertions(
            response, self.mock_requester, config.get('OPENWEATHERMAP_GEOCODINGAPI_URL'), self.request_query_params,
            response_is_inst=GeocodingLocationDto
        )

    def test_requestClientGotHttpError(self):
        self.do_requester_error_response_base_test(
            openweathermap.get_locations_by_name, args=tuple(), kwargs=self.call_params,
            exc=HTTPError(
                code=500, msg='Internal server error', fp=BytesIO(b''), hdrs=[], url=''
            )
        )


