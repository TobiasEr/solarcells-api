from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import HTTPException, APIRouter, Depends
from datetime import datetime
from models import PanelLog, Panel, CreateLogModel
from database import get_logs_collection, get_panels_collection, save_log_to_database
from http import HTTPStatus
from typing import List
import datetime as dt

router = APIRouter()
scheduler = AsyncIOScheduler()
scheduler_started = False


@router.get("/logs", response_model=List[PanelLog], status_code=HTTPStatus.OK)
async def get_all_panel_logs(logs_collection=Depends(get_logs_collection)):
    panellist = await logs_collection.find().to_list(1000)
    return panellist


@router.post("/{panel_id}/logs", response_model=PanelLog, status_code=HTTPStatus.CREATED)
async def create_panel_log(
        log: CreateLogModel,
        panel_id: int,
        logs_collection=Depends(get_logs_collection),
        panel_collection=Depends(get_panels_collection)
):
    panel = await save_log_to_database(log, panel_id, logs_collection, panel_collection)
    if panel is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Panel with ID {panel_id} not found")
    return panel


@router.get("/{panel_id}/logs", response_model=List[PanelLog], status_code=HTTPStatus.OK)
async def get_panel_logs(
        panel_id: int,
        start: str | None = None,
        end: str | None = None,
        logs_collection=Depends(get_logs_collection),
        panels_collection=Depends(get_panels_collection)
):
    panel = await panels_collection.find_one({"panelID": panel_id})
    if not panel:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Panel with ID {panel_id} not found")

    query = {"metadata.panel.panelID": panel_id}

    dateformat = "%d-%m-%Y"

    if start:
        try:
            start_date = datetime.strptime(start, dateformat)
            query["timestamp"] = {"$gte": start_date}
        except ValueError:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Start date in wrong format or invalid date. Should be dd-mm-yyyy.")

    if end:
        try:
            end_date = datetime.strptime(end, dateformat) + dt.timedelta(minutes=1439)
            if "timestamp" in query:
                query["timestamp"].update({"$lte": end_date})
            else:
                query["timestamp"] = {"$lte": end_date}
        except ValueError:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"End date in wrong format or invalid date. Should be dd-mm-yyyy.")

    logs = await logs_collection.find(query).to_list(1000)
    return logs


@router.get("/{panel_id}", response_model=Panel, status_code=HTTPStatus.OK)
async def get_panel(panel_id: int, panels_collection=Depends(get_panels_collection)):
    panel = await panels_collection.find_one({"panelID": panel_id})
    if panel:
        return panel
    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Panel with ID {panel_id} not found")


@router.post("", response_model=Panel, status_code=HTTPStatus.CREATED)
async def create_panel(panel: Panel, panels_collection=Depends(get_panels_collection)):
    if await panels_collection.count_documents({"panelID": panel.panelID}) > 0:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Panel with ID {panel.panelID} already exists.")
    new_panel = await panels_collection.insert_one(panel.model_dump())
    created_panel = await panels_collection.find_one({"_id": new_panel.inserted_id})
    return created_panel


@router.get("", response_model=List[Panel], status_code=HTTPStatus.OK)
async def get_all_panels(panels_collection=Depends(get_panels_collection)):
    panellist = await panels_collection.find().to_list(1000)
    return panellist


@router.post('/start-logging')
async def start_scheduler(
        logs_collection=Depends(get_logs_collection),
        panel_collection=Depends(get_panels_collection)
):
    log = CreateLogModel(
        effect="123W"
    )
    panel_id = 1
    global scheduler_started
    if not scheduler_started:
        async def job():
            await save_log_to_database(log, panel_id, logs_collection, panel_collection)
        scheduler.add_job(job, 'interval', minutes=2)
        scheduler.start()
        scheduler_started = True
        return {"message": "Logger started"}
    else:
        raise HTTPException(status_code=400, detail="Logger is already running")


@router.post('/stop-logging')
async def stop_scheduler():
    global scheduler_started
    if not scheduler_started:
        raise HTTPException(status_code=400, detail="Logger is not running")
    scheduler.shutdown()
    scheduler.remove_all_jobs()
    scheduler_started = False
    return {"message": "Logger shutdown"}
