import datetime
from dataclasses import dataclass, InitVar, field, fields
from typing import Optional

from weatherapp.external_services.openweathermap.com.dtobase import DtoBase


@dataclass
class CurrentWeatherDto(DtoBase):
    PARAM_NAMES_MAP = {
        'dt': 'current_time',
        'main_temp': 'main_temperature',
        'timezone': 'tz',
        'main_sea_level': 'main_pressure_sea_level',
        'main_grnd_level': 'main_pressure_grnd_level',
        'coord_lat': 'coord_latitude',
        'coord_lon': 'coord_longitude'
    }

    coord: InitVar[dict]
    coord_latitude: float = field(init=False, default=None)
    coord_longitude: float = field(init=False, default=None)
    weather: InitVar[dict]
    weather_id: int = field(init=False, default=None)
    weather_main: str = field(init=False, default=None)
    weather_description: str = field(init=False, default=None)
    weather_icon: str = field(init=False)
    base: str
    main: InitVar[dict]
    main_temperature: float = field(init=False, default=None)
    main_temp_min: float = field(init=False, default=None)
    main_temp_max: float = field(init=False, default=None)
    main_feels_like: float = field(init=False, default=None)
    main_pressure: float = field(init=False, default=None)
    main_pressure_sea_level: float = field(init=False, default=None)
    main_pressure_grnd_level: float = field(init=False, default=None)
    main_humidity: float = field(init=False, default=None)
    visibility: int
    wind: InitVar[dict]
    wind_speed: float = field(init=False, default=None)
    wind_deg: float = field(init=False, default=None)
    wind_gust: float = field(init=False, default=None)
    clouds: InitVar[dict]
    clouds_all: float = field(init=False, default=None)
    current_time: datetime.datetime
    sys: InitVar[dict]
    sys_type: str = field(init=False, default=None)
    sys_id: int = field(init=False, default=None)
    sys_message: str = field(init=False, default=None)
    sys_country: str = field(init=False, default=None)
    sys_sunrise: datetime.datetime = field(init=False, default=None)
    sys_sunset: datetime.datetime = field(init=False, default=None)
    tz: int
    id: int
    name: str
    cod: int
    rain_1h: float = field(init=False, default=None)
    snow_1h: float = field(init=False, default=None)
    rain: Optional[InitVar[dict]] = None
    snow: Optional[InitVar[dict]] = None

    def __post_init__(self, coord: dict, weather: dict, main: dict, wind: dict, clouds: dict, sys: dict):
        weather = weather[0]
        for dname, d in locals().items():
            if dname == 'self':
                continue
            for key in d:
                attr_name = self.PARAM_NAMES_MAP.get(f'{dname}_{key}', f'{dname}_{key}')
                setattr(self, attr_name, d.get(key))

        for f in fields(self):
            if f.type is datetime.datetime:
                tz = datetime.timezone(datetime.timedelta(seconds=self.tz))
                setattr(self, f.name, datetime.datetime.fromtimestamp(getattr(self, f.name), tz))



