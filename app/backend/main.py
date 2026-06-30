from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.backend.db.init_db import init_db, seed_sources
from app.backend.db.session import SessionLocal
from app.backend.ingestion.parsers.seek import SeekParser
from app.backend.ingestion.registry import registry
from app.backend.ingestion.routes import api_router as ingestion_api_router
from app.backend.ingestion.routes import ui_router as ingestion_ui_router
from app.backend.jobs.routes import api_router as jobs_api_router
from app.backend.jobs.routes import ui_router as jobs_ui_router
from app.backend.sources_routes import api_router as sources_api_router


def register_parsers() -> None:
    registry.register(SeekParser())


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_parsers()
    init_db()
    with SessionLocal() as db:
        seed_sources(db)
    yield


app = FastAPI(title="Job Search Tracker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/backend/ui/static"), name="static")
app.include_router(jobs_api_router)
app.include_router(sources_api_router)
app.include_router(ingestion_api_router)
app.include_router(jobs_ui_router)
app.include_router(ingestion_ui_router)

