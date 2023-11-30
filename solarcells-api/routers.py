from fmiweather import get_latest_weather
from fastapi import HTTPException, APIRouter, Depends
from datetime import datetime
from models import PanelLog, Panel, CreateLogModel, Metadata
from database import get_logs_collection, get_panels_collection
from http import HTTPStatus
from typing import List

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
    await logs_collection.insert_one(panel_log.model_dump())
    return panel_log


@router.get("/{panel_id}/logs", response_model=List[PanelLog], status_code=HTTPStatus.OK)
async def get_panel_logs(
        panel_id: int,
        logs_collection=Depends(get_logs_collection),
        panels_collection=Depends(get_panels_collection)
):
    panel = await panels_collection.find_one({"panelID": panel_id})

    if not panel:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Panel with ID {panel_id} not found")

    logs = await logs_collection.find({"metadata.panel.panelID": panel_id}).to_list(1000)
    return logs


@router.get("/{panel_id}", response_model=Panel, status_code=HTTPStatus.OK)
async def get_panel(panel_id: int, panels_collection=Depends(get_panels_collection)):
    panel = await panels_collection.find_one({"panelID": panel_id})
    if panel:
        return panel
    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Panel with ID {panel_id} not found")


@router.post("", response_model=Panel, status_code=HTTPStatus.CREATED)
async def create_panel(panel: Panel, panels_collection=Depends(get_panels_collection)):
    await panels_collection.insert_one(panel.model_dump())
    return panel


@router.get("", response_model=List[Panel], status_code=HTTPStatus.OK)
async def get_all_panels(panels_collection=Depends(get_panels_collection)):
    panellist = await panels_collection.find().to_list(1000)
    return panellist
