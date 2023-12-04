from fastapi import FastAPI
from routers import router as panels_router
from contextlib import asynccontextmanager
from database import connect_to_db, close_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db()
    yield
    await close_db_connection()


app = FastAPI(lifespan=lifespan)


app.include_router(panels_router, tags=["panels"], prefix="/solar-panels")
