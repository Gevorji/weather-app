import os

from external_services.openweathermap.com.baseclient import BaseClient
from external_services.openweathermap.com.constants_enums import MeasurementUnits, ResponseLanguages
from external_services.openweathermap.onecallapi.responsedto import CurrentWeatherDto


class OneCallApiClient(BaseClient):
    _api_url = os.getenv('OPENWEATHERMAP_ONECALLAPI_URL')

    def __init__(self, request_client=None):
        if request_client:
            self._request_client=request_client

    def get_current_weather(
            self, *, latitude: float, longitude: float, units: MeasurementUnits, lang: ResponseLanguages
    ) -> CurrentWeatherDto:
        response_d = self._call_api(
            {
                'lat': latitude,
                'lon': longitude,
                'units': units.value,
                'appid': self._api_key,
                'exclude': 'minutely,hourly,daily,alerts',
                'lang': lang.value
            }
        )

        return CurrentWeatherDto.from_dict(response_d)



