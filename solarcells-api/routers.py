from fmiweather import get_latest_weather
from fastapi import HTTPException, APIRouter, Depends
from datetime import datetime
from models import PanelLog, Panel, CreateLogModel, Metadata
from database import get_logs_collection, get_panels_collection
from http import HTTPStatus
from typing import List
import datetime as dt

router = APIRouter()


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
    panel = await panel_collection.find_one({"panelID": panel_id})
    if not panel:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Panel with ID {panel_id} not found")
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
