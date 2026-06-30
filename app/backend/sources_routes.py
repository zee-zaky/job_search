from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backend.db.models import JobSource
from app.backend.db.session import get_db


api_router = APIRouter(prefix="/api/sources", tags=["sources"])


class SourceCreate(BaseModel):
    name: str
    provider: str
    description: str | None = None
    enabled: bool = True
    ingestion_mode: str
    search_url: str | None = None
    schedule_minutes: int = 60


class SourceUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    description: str | None = None
    enabled: bool | None = None
    ingestion_mode: str | None = None
    search_url: str | None = None
    schedule_minutes: int | None = None


@api_router.get("")
def list_sources(db: Session = Depends(get_db)):
    return list(db.scalars(select(JobSource).order_by(JobSource.name)))


@api_router.post("")
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    source = JobSource(**payload.model_dump())
    db.add(source)
    db.commit()
    return source


@api_router.patch("/{source_id}")
def update_source(source_id: str, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(JobSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail={"error_code": "SOURCE_NOT_FOUND", "message": "Source not found"})
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.commit()
    return source


@api_router.post("/{source_id}/disable")
def disable_source(source_id: str, db: Session = Depends(get_db)):
    source = db.get(JobSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail={"error_code": "SOURCE_NOT_FOUND", "message": "Source not found"})
    source.enabled = False
    db.commit()
    return source

