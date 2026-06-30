from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backend.db.models import IngestionRun, JobSource
from app.backend.db.session import get_db
from app.backend.ingestion.schemas import IngestionRunRequest, ManualImportRequest
from app.backend.ingestion.service import IngestionService


templates = Jinja2Templates(directory="app/backend/ui/templates")
api_router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])
ui_router = APIRouter(tags=["ui"])


@api_router.post("/run")
async def trigger_ingestion(payload: IngestionRunRequest | None = None, db: Session = Depends(get_db)):
    run = await IngestionService(db).run(payload.source_id if payload else None)
    return run


@api_router.post("/import-job")
async def import_job(payload: ManualImportRequest, db: Session = Depends(get_db)):
    try:
        run, job_id, action = await IngestionService(db).import_job(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error_code": "MANUAL_IMPORT_INVALID", "message": str(exc)}) from exc
    return {"run_id": run.run_id, "job_id": job_id, "action": action, "status": run.status, "errors": run.errors}


@api_router.get("/status")
def ingestion_status(db: Session = Depends(get_db)):
    return db.scalar(select(IngestionRun).order_by(IngestionRun.started_at.desc()))


@api_router.get("/runs")
def ingestion_runs(db: Session = Depends(get_db)):
    return list(db.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(50)))


@ui_router.get("/import", response_class=HTMLResponse)
def import_page(request: Request, db: Session = Depends(get_db)):
    sources = list(db.scalars(select(JobSource).where(JobSource.enabled == True, JobSource.ingestion_mode == "manual_import")))  # noqa: E712
    return templates.TemplateResponse(request, "import.html", {"sources": sources, "result": None})


@ui_router.post("/ingestion/run")
async def trigger_ingestion_form(db: Session = Depends(get_db)):
    await IngestionService(db).run()
    return RedirectResponse("/", status_code=303)


@ui_router.post("/import", response_class=HTMLResponse)
async def import_job_form(
    request: Request,
    source_id: str = Form(...),
    provider: str = Form(...),
    job_url: str = Form(...),
    db: Session = Depends(get_db),
):
    sources = list(db.scalars(select(JobSource).where(JobSource.enabled == True, JobSource.ingestion_mode == "manual_import")))  # noqa: E712
    result = None
    try:
        payload = ManualImportRequest(source_id=source_id, provider=provider, job_url=job_url)
        run, job_id, action = await IngestionService(db).import_job(payload)
        result = {"status": run.status, "job_id": job_id, "action": action, "errors": run.errors}
    except Exception as exc:
        result = {"status": "failed", "job_id": None, "action": "failed", "errors": str(exc)}
    return templates.TemplateResponse(request, "import.html", {"sources": sources, "result": result})
