from dataclasses import dataclass
from typing import Dict, Optional

from weatherapp.external_services.openweathermap.com.dtobase import DtoBase


@dataclass
class GeocodingLocationDto(DtoBase):
    PARAM_NAMES_MAP = {
        'lat': 'latitude',
        'lon': 'longitude'
    }

    name: str
    latitude: float
    longitude: float
    country: str
    local_names: Optional[Dict[str, str]] = None
    state: Optional[str] = None


