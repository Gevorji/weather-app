import os

from weatherapp.external_services.openweathermap.com.baseclient import BaseClient
from weatherapp.external_services.openweathermap.com.constants_enums import MeasurementUnits, ResponseLanguages
from weatherapp.external_services.openweathermap.currentweatherdata.responsedto import CurrentWeatherDto
from weatherapp.external_services.openweathermap import settings


class CurrentWeatherDataClient(BaseClient):
    _api_url = settings.OPENWEATHERMAP_CURRENTWEATHERDATA_API_URL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_current_weather_data(
            self, *, latitude: float, longitude: float, units: MeasurementUnits = MeasurementUnits.STANDARD,
            lang: ResponseLanguages = ResponseLanguages.ENGLISH
    ):
        response_d = self._call_api(
            {
                'lat': latitude,
                'lon': longitude,
                'appid': self._api_key,
                'units': units.value,
                'lang': lang.value
            }
        )

        return CurrentWeatherDto.from_dict(response_d)
