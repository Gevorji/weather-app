from typing import List

from weatherapp.external_services.openweathermap.com.baseclient import BaseClient
from weatherapp.external_services.openweathermap.geocodingapi.responsedto import GeocodingLocationDto
from weatherapp.external_services.openweathermap import settings


class GeocodingApiClient(BaseClient):
    _api_url = settings.OPENWEATHERMAP_GEOCODINGAPI_URL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_location_data_by_name(
            self, location_name, *,  limit=settings.GEOCODING_LOCATIONS_RESPONSE_LIM
    ) -> List[GeocodingLocationDto]:
        locations_d = self._call_api({'q': location_name, 'limit': limit, 'appid': self._api_key})
        return [GeocodingLocationDto.from_dict(location_d) for location_d in locations_d]

