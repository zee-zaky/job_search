from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.backend.config.settings import get_settings
from app.backend.db.models import IngestionRunSource, Job, JobSource
from app.backend.db.session import get_db
from app.backend.jobs.repository import JobRepository
from app.backend.jobs.schemas import JobRead, JobUpdate


templates = Jinja2Templates(directory="app/backend/ui/templates")
router = APIRouter()
api_router = APIRouter(prefix="/api/jobs", tags=["jobs"])
ui_router = APIRouter(tags=["ui"])


@api_router.get("", response_model=list[JobRead])
def list_jobs(
    q: str | None = None,
    provider: str | None = None,
    source_id: str | None = None,
    city_location: str | None = None,
    employment_type: str | None = None,
    status: str | None = None,
    is_applied: bool | None = None,
    is_favorite: bool | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    return JobRepository(db).query_jobs(
        q, provider, source_id, city_location, employment_type, status, is_applied, is_favorite, page, page_size
    )


@api_router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = JobRepository(db).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found"})
    return job


@api_router.patch("/{job_id}", response_model=JobRead)
def update_job(job_id: str, payload: JobUpdate, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found"})
    repo.update_user_fields(
        job,
        payload.is_applied,
        payload.is_favorite,
        payload.user_comments,
        payload.status,
        payload.generated_cv_path,
    )
    db.commit()
    return job


@api_router.post("/{job_id}/mark-applied", response_model=JobRead)
def mark_applied(job_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found"})
    repo.update_user_fields(job, True, None, None, "applied")
    db.commit()
    return job


@api_router.post("/{job_id}/archive", response_model=JobRead)
def archive_job(job_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found"})
    repo.update_user_fields(job, None, None, None, "archived")
    db.commit()
    return job


@api_router.post("/{job_id}/favorite", response_model=JobRead)
def favorite_job(job_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found"})
    repo.update_user_fields(job, None, True, None, None)
    db.commit()
    return job


@api_router.delete("/{job_id}/favorite", response_model=JobRead)
def unfavorite_job(job_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found"})
    repo.update_user_fields(job, None, False, None, None)
    db.commit()
    return job


@ui_router.get("/", response_class=HTMLResponse)
def jobs_page(
    request: Request,
    source_id: str | None = None,
    city_location: str | None = None,
    employment_type: str | None = None,
    favorite_filter: str = "",
    db: Session = Depends(get_db),
):
    repo = JobRepository(db)
    is_favorite = _favorite_filter_value(favorite_filter)
    jobs = repo.query_jobs(
        source_id=source_id,
        city_location=city_location,
        employment_type=employment_type,
        is_favorite=is_favorite,
        page_size=1000,
    )
    job_count = repo.count_jobs(
        source_id=source_id,
        city_location=city_location,
        employment_type=employment_type,
        is_favorite=is_favorite,
    )
    sources = repo.list_sources()
    locations = repo.list_locations()
    employment_types = repo.list_employment_types()
    source_summaries = _source_summaries(db, sources)
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "jobs.html",
        {
            "jobs": jobs,
            "job_count": job_count,
            "sources": sources,
            "source_summaries": source_summaries,
            "locations": locations,
            "employment_types": employment_types,
            "selected_source_id": source_id or "",
            "selected_location": city_location or "",
            "selected_employment_type": employment_type or "",
            "selected_favorite_filter": favorite_filter,
            "default_pages_per_source": settings.default_pages_per_source,
            "max_pages_per_source": settings.max_pages_per_source,
        },
    )


@ui_router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail_page(request: Request, job_id: str, db: Session = Depends(get_db)):
    job = JobRepository(db).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "new":
        job.status = "viewed"
        db.commit()
    cv_directory_uri = _cv_directory_uri(job.generated_cv_path)
    return templates.TemplateResponse(request, "job_detail.html", {"job": job, "cv_directory_uri": cv_directory_uri})


@ui_router.post("/jobs/{job_id}/comments")
def update_comments(job_id: str, user_comments: str = Form(default=""), db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    repo.update_user_fields(job, None, None, user_comments, None)
    db.commit()
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


@ui_router.post("/jobs/{job_id}/mark-applied")
def mark_applied_form(job_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    repo.update_user_fields(job, True, None, None, "applied")
    db.commit()
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


@ui_router.post("/jobs/{job_id}/archive")
def archive_job_form(job_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    repo.update_user_fields(job, None, None, None, "archived")
    db.commit()
    return RedirectResponse("/", status_code=303)


@ui_router.post("/jobs/{job_id}/favorite")
def favorite_job_form(job_id: str, request: Request, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    repo.update_user_fields(job, None, True, None, None)
    db.commit()
    return RedirectResponse(_redirect_back(request), status_code=303)


@ui_router.post("/jobs/{job_id}/unfavorite")
def unfavorite_job_form(job_id: str, request: Request, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    repo.update_user_fields(job, None, False, None, None)
    db.commit()
    return RedirectResponse(_redirect_back(request), status_code=303)


def _favorite_filter_value(value: str) -> bool | None:
    if value == "favorites":
        return True
    if value == "hide_favorites":
        return False
    return None


def _redirect_back(request: Request) -> str:
    target = request.headers.get("referer")
    return target or "/"


def _cv_directory_uri(generated_cv_path: str | None) -> str | None:
    if not generated_cv_path:
        return None
    path = Path(generated_cv_path).expanduser()
    directory = path if path.is_dir() else path.parent
    return directory.resolve().as_uri()


def _source_summaries(db: Session, sources: list[JobSource]) -> list[dict]:
    summaries = []
    for source in sources:
        latest = db.scalar(
            select(IngestionRunSource)
            .where(IngestionRunSource.source_id == source.id)
            .order_by(IngestionRunSource.started_at.desc())
            .limit(1)
        )
        summaries.append(
            {
                "source": source,
                "job_count": db.scalar(select(func.count()).select_from(Job).where(Job.source_id == source.id)) or 0,
                "last_status": latest.status if latest else "never run",
                "last_error": latest.errors if latest and latest.errors else None,
                "last_run_at": latest.started_at if latest else None,
            }
        )
    return summaries
