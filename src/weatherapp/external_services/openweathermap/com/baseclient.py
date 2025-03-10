from urllib.parse import urljoin, urlencode
import json

from weatherapp.external_services.openweathermap import settings
from weatherapp.external_services.openweathermap.com.requestclients import get_default_http_client_cls


class BaseClient:
    _api_key = settings.OPENWEATHERMAP_API_KEY

    def __init__(self, request_client=get_default_http_client_cls()()):
        self._request_client = request_client

    def _get_request_url(self, parameters: dict) -> str:
        try:
            return urljoin(self._api_url, '?' + urlencode(parameters))
        except AttributeError as e:
            raise AttributeError('No base api url was set to construct a request url') from e

    def _call_api(self, parameters: dict):
        request_url = self._get_request_url(parameters)
        data = self._request_client(request_url)
        return json.loads(data)
