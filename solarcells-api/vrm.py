import datetime
from http import HTTPStatus
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends, HTTPException
from config.config import VRM_TOKEN, SITE_ID
import httpx
import time
import csv
from io import StringIO

from database import get_tempsensordata_collection, save_temp_log_to_database, get_tempsensors_collection
from models import TempSensorData, TempSensorLog

router = APIRouter()
sensor_scheduler = AsyncIOScheduler()
sensor_scheduler_started = False


@router.get("/{temp_sensor_id}/logs", response_model=List[TempSensorLog], status_code=HTTPStatus.OK)
async def get_temp_sensor_data(
        temp_sensor_id: int,
        start: str | None = None,
        end: str | None = None,
        tempsensdata_collection=Depends(get_tempsensordata_collection),
        tempsensors_collection=Depends(get_tempsensors_collection)
):
    sensor = await tempsensors_collection.find_one({"tempsensor_ID": temp_sensor_id})
    if not sensor:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Sensor with ID {temp_sensor_id} not found")

    query = {"sensor.tempsensor_ID": temp_sensor_id}

    dateformat = "%d-%m-%Y"

    if start:
        try:
            start_date = datetime.datetime.strptime(start, dateformat)
            query["timestamp"] = {"$gte": start_date}
        except ValueError:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Start date in wrong format or invalid date. Should be dd-mm-yyyy.")

    if end:
        try:
            end_date = datetime.datetime.strptime(end, dateformat) + datetime.timedelta(minutes=1439)
            query.setdefault("timestamp", {})["$lte"] = end_date
        except ValueError:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"End date in wrong format or invalid date. Should be dd-mm-yyyy.")

    logs = await tempsensdata_collection.find(query).to_list(1000)
    return logs


async def get_vrm_sensor_data():
    time_start = int(time.time()) - 300
    vrm_url = f"https://vrmapi.victronenergy.com/v2/installations/{SITE_ID}/data-download?start={time_start}"
    headers = {
        "x-authorization": f"Bearer {VRM_TOKEN}"
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url=vrm_url, headers=headers)

    if response.status_code == 200:
        csv_text = response.text
        csv_data = csv.reader(StringIO(csv_text))

        sensor_data = list(csv_data)
        sensor_names_list, data_names_list, data_points_list = sensor_data[0], sensor_data[1], sensor_data[-1]

        def get_sensor_data(sensor_name):
            return TempSensorData(
                **{data_names_list[i].lower(): data_points_list[i] for i, x in enumerate(sensor_names_list)
                   if x == sensor_name and data_names_list[i] != "Temperature status"}
            )

        sensor_29_data = get_sensor_data("Temperature sensor [29]")
        sensor_30_data = get_sensor_data("Temperature sensor [30]")

        return [sensor_29_data, sensor_30_data]
    else:
        raise HTTPException(status_code=400, detail=response.text)


@router.post("/start-logging", status_code=HTTPStatus.OK)
async def start_sensor_logging(
        temp_sens_collection=Depends(get_tempsensordata_collection)
):
    global sensor_scheduler_started
    if sensor_scheduler_started:
        raise HTTPException(status_code=400, detail="Temperature sensor logger is already running")

    async def job():
        await save_temp_log_to_database(get_vrm_sensor_data, temp_sens_collection)

    sensor_scheduler.add_job(job, 'interval', minutes=1)
    sensor_scheduler.start()
    sensor_scheduler_started = True
    return {"message": "Temperature sensor logger started"}


async def stop_scheduler():
    global sensor_scheduler_started
    if sensor_scheduler_started:
        sensor_scheduler.shutdown(wait=False)
        sensor_scheduler.remove_all_jobs()


@router.post('/stop-logging')
async def stop_sensor_logging():
    global sensor_scheduler_started
    if not sensor_scheduler_started:
        raise HTTPException(status_code=400, detail="Temperature sensor logger is not running")
    await stop_scheduler()
    sensor_scheduler_started = False
    return {"message": "Temperature sensor logger shutdown"}
