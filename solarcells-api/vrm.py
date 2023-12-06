from http import HTTPStatus
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends, HTTPException
from config.config import VRM_TOKEN, SITE_ID
import httpx
import time
import csv
from io import StringIO

from database import get_tempsensor_collection, save_temp_log_to_database
from models import TempSensorData, TempSensorLog

router = APIRouter()
sensor_scheduler = AsyncIOScheduler()
sensor_scheduler_started = False


@router.get("/logs", response_model=List[TempSensorLog], status_code=HTTPStatus.OK)
async def get_temp_sensor_data(temp_sens_collection=Depends(get_tempsensor_collection)):
    logs_list = await temp_sens_collection.find().to_list(1000)
    return logs_list


async def get_vrm_sensor_data():
    time_start = int(time.time()) - 300
    vrm_url = f"https://vrmapi.victronenergy.com/v2/installations/{SITE_ID}/data-download?start={time_start}"
    headers = {
        "x-authorization": f"Bearer {VRM_TOKEN}"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url=vrm_url, headers=headers)

    if response.status_code == 200:
        csv_text = response.text
        csv_data = csv.reader(StringIO(csv_text))

        sensor_data = list(csv_data)[-1]
        sensor1 = TempSensorData(
            tempsensorID=29,
            sensor_timestamp=sensor_data[0],
            temperature=sensor_data[16],
            humidity=sensor_data[18]
        )

        sensor2 = TempSensorData(
            tempsensorID=30,
            sensor_timestamp=sensor_data[0],
            temperature=sensor_data[19],
            humidity=sensor_data[21],
            pressure=sensor_data[22]
        )

        return [sensor1, sensor2]
    else:
        raise HTTPException(status_code=400, detail=response.text)


@router.post("/start-logging", status_code=HTTPStatus.OK)
async def start_sensor_logging(
        temp_sens_collection=Depends(get_tempsensor_collection)
):
    global sensor_scheduler_started
    if not sensor_scheduler_started:
        async def job():
            await save_temp_log_to_database(get_vrm_sensor_data, temp_sens_collection)

        sensor_scheduler.add_job(job, 'interval', minutes=1)
        sensor_scheduler.start()
        sensor_scheduler_started = True
        return {"message": "Temperature sensor logger started"}
    else:
        raise HTTPException(status_code=400, detail="Temperature sensor logger is already running")


@router.post('/stop-logging')
async def stop_scheduler():
    global sensor_scheduler_started
    if not sensor_scheduler_started:
        raise HTTPException(status_code=400, detail="Temperature sensor logger is not running")
    sensor_scheduler.shutdown()
    sensor_scheduler.remove_all_jobs()
    sensor_scheduler_started = False
    return {"message": "Temperature sensor logger shutdown"}
