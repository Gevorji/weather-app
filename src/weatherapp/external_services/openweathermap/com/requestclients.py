from urllib.error import HTTPError
from urllib.request import urlopen

from weatherapp.external_services.openweathermap import settings
from weatherapp.external_services.openweathermap.errors import (OpenweathermapApiHTTPResponseError,
                                                                OpenWeathermapApiConnectionTimeoutError)


class BaseRequestClient:

    def __call__(self, *args, **kwargs):
        raise TypeError(
            'Request client should provide __call__ method that receives a response from web service'
        )


class StlibHttpRequestClient(BaseRequestClient):
    def __call__(self, url: str, *args, **kwargs) -> str:
        try:
            return urlopen(url, timeout=settings.OPENWEATHERMAP_CONNECTION_TIMEOUT).read().decode()
        except HTTPError as e:
            raise OpenweathermapApiHTTPResponseError(e.code, e.reason) from e
        except TimeoutError as e:
            raise OpenWeathermapApiConnectionTimeoutError from e




def get_default_http_client_cls():
    return StlibHttpRequestClient
