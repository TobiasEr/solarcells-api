from pydantic import BaseModel, Field
from fmiweather import WeatherModel
from datetime import datetime


class Panel(BaseModel):
    panelID: int = Field(..., alias="panelID")
    vertical_angle: int = Field(..., alias="vertical_angle")
    horizontal_angle: int = Field(..., alias="horizontal_angle")
    panel_location: str = Field(..., alias="panel_location")


class Metadata(BaseModel):
    effect: str = Field(..., alias="effect")
    weather: WeatherModel = Field(..., alias="weather")
    panel: Panel = Field(..., alias="panel")


class PanelLog(BaseModel):
    timestamp: datetime = Field(..., alias="timestamp")
    metadata: Metadata = Field(..., alias="metadata")


class CreateLogModel(BaseModel):
    effect: str = Field(..., alias="effect")

