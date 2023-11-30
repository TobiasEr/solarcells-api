from fastapi import FastAPI
from routers import router as panels_router
from database import connect_to_db, close_db_connection


app = FastAPI()


@app.on_event("startup")
async def startup_db_client():
    await connect_to_db()


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_db_connection()


app.include_router(panels_router, tags=["panels"], prefix="/solar-panels")
