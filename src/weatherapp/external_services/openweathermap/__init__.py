from .com.constants_enums import ResponseLanguages, MeasurementUnits
from .currentweatherdata.client import CurrentWeatherDataClient
from .geocodingapi.client import GeocodingApiClient
from . import settings

_geo_client = GeocodingApiClient()
_cur_weather_client = CurrentWeatherDataClient()


def get_locations_by_name(name: str, limit: int = settings.GEOCODING_LOCATIONS_RESPONSE_LIM):
    return _geo_client.get_location_data_by_name(name, limit=limit)


def get_current_weather_data(
        latitude: float, longitude: float, *,
        language: ResponseLanguages = ResponseLanguages.ENGLISH, units: MeasurementUnits = MeasurementUnits.STANDARD
):
    return _cur_weather_client.get_current_weather_data(
        latitude=latitude, longitude=longitude, units=units, lang=language
    )

