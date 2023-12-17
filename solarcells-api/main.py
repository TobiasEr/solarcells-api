from fastapi import FastAPI
from routers import router as panels_router
from vrm import router as vrm_router
from contextlib import asynccontextmanager
from database import connect_to_db, close_db_connection
from vrm import stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db()
    yield
    await close_db_connection()
    await stop_scheduler()


app = FastAPI(lifespan=lifespan)


# app.include_router(panels_router, tags=["panels"], prefix="/solar-panels")
app.include_router(vrm_router, tags=["temp-sensor"], prefix="/temp-sensors")
