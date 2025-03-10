from dataclasses import dataclass, InitVar
from typing import Optional

from external_services.openweathermap.com.dtobase import DtoBase


@dataclass
class ResponseCommonData:
    PARAM_NAMES_MAP = {
        'lat': 'latitude',
        'lon': 'longitude'
    }

    latitude: float
    longitude: float
    timezone: str
    timezone_offset: int


@dataclass
class WeatherData:
    PARAM_NAMES_MAP = {
        'dt': 'current_time',
        'temp': 'temperature',
        'uvi': 'uv_index',
    }

    current_time: int
    sunrise: int
    sunset: int
    temperature: float
    feels_like: float
    pressure: float
    humidity: float
    dew_point: float
    clouds: float
    uv_index: float
    visibility: int
    wind_speed: float
    wind_gust: Optional[float]
    wind_direction: int
    weather_id: int
    weather_main: str
    weather_description: str
    weather_icon_id: int
    rain_i: Optional[InitVar[dict]]
    snow_i: Optional[InitVar[dict]]


@dataclass
class CurrentWeatherDto(ResponseCommonData, WeatherData, DtoBase):
    rain_1h: Optional[float]
    snow_1h: Optional[float]

    def __post_init__(self):
        self.rain_1h = self.rain.get('1h')
        self.snow_1h = self.snow.get('1h')
