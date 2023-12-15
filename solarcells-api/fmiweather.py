import datetime as dt
from fmiopendata.wfs import download_stored_query
from pydantic import BaseModel
import pytz


class WeatherModel(BaseModel):
    # weather_time: dt.datetime
    air_temperature: float
    wind_speed: float
    wind_direction: float
    relative_humidity: float
    cloud_amount: float


def get_latest_weather():
    end_time = dt.datetime.utcnow()
    start_time = end_time - dt.timedelta(minutes=10)
    start_time = start_time.isoformat(timespec="seconds") + "Z"
    end_time = end_time.isoformat(timespec="seconds") + "Z"

    observations = download_stored_query("fmi::observations::weather::multipointcoverage",
                                         args=["fmisid=100907",
                                               "starttime=" + start_time,
                                               "endtime=" + end_time])

    latest_airport_weather = observations.data[sorted(observations.data.keys())[-1]]['Jomala Maarianhamina lentoasema']

    weather = WeatherModel(
        # weather_time=sorted(observations.data.keys())[-1] + dt.timedelta(minutes=120),
        air_temperature=latest_airport_weather['Air temperature']['value'],
        wind_speed=latest_airport_weather['Wind speed']['value'],
        wind_direction=latest_airport_weather['Wind direction']['value'],
        relative_humidity=latest_airport_weather['Relative humidity']['value'],
        cloud_amount=latest_airport_weather['Cloud amount']['value']
    )
    return weather
