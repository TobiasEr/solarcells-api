from pydantic import BaseModel, Field, BeforeValidator
from fmiweather import WeatherModel
from datetime import datetime
from typing import Optional, Annotated


PyObjectId = Annotated[str, BeforeValidator(str)]


class Panel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    panelID: int = Field(..., alias="panelID")
    vertical_angle: int = Field(..., alias="vertical_angle")
    horizontal_angle: int = Field(..., alias="horizontal_angle")
    panel_location: str = Field(..., alias="panel_location")


class Metadata(BaseModel):
    effect: str = Field(..., alias="effect")
    weather: WeatherModel = Field(..., alias="weather")
    panel: Panel = Field(..., alias="panel")


class PanelLog(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    timestamp: datetime = Field(..., alias="timestamp")
    metadata: Metadata = Field(..., alias="metadata")


class CreateLogModel(BaseModel):
    effect: str = Field(..., alias="effect")


class TempSensorData(BaseModel):
    tempsensorID: int = Field(..., alias="tempsensorID")
    sensor_timestamp: datetime = Field(..., alias="sensor_timestamp")
    temperature: float = Field(..., alias="temperature")
    humidity: float = Field(..., alias="humidity")
    pressure: Optional[float] = Field(alias="pressure", default=None)


class TempSensorLog(BaseModel):
    timestamp: datetime = Field(..., alias="timestamp")
    sensordata: TempSensorData = Field(..., alias="sensordata")
    weather: WeatherModel = Field(..., alias="weather")
