from datetime import datetime
from http import HTTPStatus

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from config.config import MONGO_DB, MONGO_URL
from fmiweather import get_latest_weather
from models import CreateLogModel, PanelLog, Metadata, TempSensorLog, TemperatureSensor


class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[MONGO_DB]

    async def close(self):
        if self.client:
            self.client.close()

    async def get_collection(self, collection: str):
        if self.db is None:
            await self.connect()
        return self.db[collection]


mongodb = MongoDB()


async def get_logs_collection():
    return await mongodb.get_collection("test-collection")


async def get_tempsensordata_collection():
    return await mongodb.get_collection("temp-sensor-data")


async def get_panels_collection():
    return await mongodb.get_collection("panels")


async def get_tempsensors_collection():
    return await mongodb.get_collection("tempsensors")


async def connect_to_db():
    await mongodb.connect()


async def close_db_connection():
    await mongodb.close()


async def save_log_to_database(
        log: CreateLogModel,
        panel_id: int,
        logs_collection: AsyncIOMotorCollection,
        panel_collection: AsyncIOMotorCollection
):
    panel = await panel_collection.find_one({"panelID": panel_id})
    if not panel:
        return None
    panel_log = PanelLog(
        timestamp=datetime.now().replace(microsecond=0),
        metadata=Metadata(
            effect=log.effect,
            weather=get_latest_weather(),
            panel=panel
        )
    )
    new_log = await logs_collection.insert_one(panel_log.model_dump())
    created_log = await logs_collection.find_one({"_id": new_log.inserted_id})
    return created_log


async def save_temp_log_to_database(
        vrm_sensor_data,
        tempsensorlogs_collection: AsyncIOMotorCollection
):
    sensor_logs = await vrm_sensor_data()
    time_now = datetime.now().replace(microsecond=0)
    weather = get_latest_weather()
    sensor_logs = [
        TempSensorLog(
            timestamp=time_now,
            sensor=TemperatureSensor(
              tempsensor_ID=29,
              sensor_location="inside"
            ),
            sensordata=sensor_logs[0],
            weather=weather
        ),
        TempSensorLog(
            timestamp=time_now,
            sensor=TemperatureSensor(
                tempsensor_ID=30,
                sensor_location="outside"
            ),
            sensordata=sensor_logs[1],
            weather=weather
        )
    ]
    inserted_logs = await tempsensorlogs_collection.insert_many([sensordata.model_dump() for sensordata in sensor_logs])
    created_logs = [tempsensorlogs_collection.find_one({"_id": db_id}) for db_id in inserted_logs.inserted_ids]
    return created_logs


async def get_tempsensor(
        sensor_id,
        tempsens_collection: AsyncIOMotorCollection
):
    sensor = tempsens_collection.find_one({"tempsensor_ID": sensor_id})
    if not sensor:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Sensor with ID {sensor_id} not found")

    return TemperatureSensor(**sensor)
