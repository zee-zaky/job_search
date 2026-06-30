from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

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
    repo.update_user_fields(job, payload.is_applied, payload.is_favorite, payload.user_comments, payload.status)
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
    city_location: str | None = None,
    employment_type: str | None = None,
    db: Session = Depends(get_db),
):
    repo = JobRepository(db)
    jobs = repo.query_jobs(city_location=city_location, employment_type=employment_type, page_size=1000)
    job_count = repo.count_jobs(city_location=city_location, employment_type=employment_type)
    locations = repo.list_locations()
    employment_types = repo.list_employment_types()
    return templates.TemplateResponse(
        request,
        "jobs.html",
        {
            "jobs": jobs,
            "job_count": job_count,
            "locations": locations,
            "employment_types": employment_types,
            "selected_location": city_location or "",
            "selected_employment_type": employment_type or "",
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
    return templates.TemplateResponse(request, "job_detail.html", {"job": job})


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
