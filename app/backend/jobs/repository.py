import hashlib
import json
from datetime import datetime

from sqlalchemy import Select, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.backend.db.models import Job, utc_now
from app.backend.ingestion.schemas import ParsedJob


def content_hash(parsed: ParsedJob) -> str:
    payload = "|".join(
        [
            parsed.job_title or "",
            parsed.employer_name or "",
            parsed.city_location or "",
            parsed.description or "",
            parsed.posted_at.isoformat() if parsed.posted_at else "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def query_jobs(
        self,
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
    ) -> list[Job]:
        stmt: Select[tuple[Job]] = select(Job)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Job.job_title.ilike(like), Job.employer_name.ilike(like), Job.description.ilike(like)))
        if provider:
            stmt = stmt.where(Job.provider == provider)
        if source_id:
            stmt = stmt.where(Job.source_id == source_id)
        if city_location:
            stmt = stmt.where(Job.city_location == city_location)
        if employment_type:
            stmt = stmt.where(Job.employment_type == employment_type)
        if status:
            stmt = stmt.where(Job.status == status)
        if is_applied is not None:
            stmt = stmt.where(Job.is_applied == is_applied)
        if is_favorite is not None:
            stmt = stmt.where(Job.is_favorite == is_favorite)
        stmt = (
            stmt.order_by(Job.posted_at.is_(None), Job.posted_at.desc(), Job.last_seen_at.desc())
            .offset(max(page - 1, 0) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt))

    def count_jobs(
        self,
        q: str | None = None,
        provider: str | None = None,
        source_id: str | None = None,
        city_location: str | None = None,
        employment_type: str | None = None,
        status: str | None = None,
        is_applied: bool | None = None,
        is_favorite: bool | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Job)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Job.job_title.ilike(like), Job.employer_name.ilike(like), Job.description.ilike(like)))
        if provider:
            stmt = stmt.where(Job.provider == provider)
        if source_id:
            stmt = stmt.where(Job.source_id == source_id)
        if city_location:
            stmt = stmt.where(Job.city_location == city_location)
        if employment_type:
            stmt = stmt.where(Job.employment_type == employment_type)
        if status:
            stmt = stmt.where(Job.status == status)
        if is_applied is not None:
            stmt = stmt.where(Job.is_applied == is_applied)
        if is_favorite is not None:
            stmt = stmt.where(Job.is_favorite == is_favorite)
        return self.db.scalar(stmt) or 0

    def list_locations(self) -> list[str]:
        stmt = select(distinct(Job.city_location)).where(Job.city_location.is_not(None)).order_by(Job.city_location)
        return [location for location in self.db.scalars(stmt) if location]

    def list_employment_types(self) -> list[str]:
        stmt = select(distinct(Job.employment_type)).where(Job.employment_type.is_not(None)).order_by(Job.employment_type)
        return [employment_type for employment_type in self.db.scalars(stmt) if employment_type]

    def get(self, job_id: str) -> Job | None:
        return self.db.get(Job, job_id)

    def upsert_from_parsed(self, parsed: ParsedJob) -> tuple[Job, str]:
        now = utc_now()
        lookup = [Job.canonical_url == parsed.canonical_url]
        if parsed.external_job_id:
            lookup.append(Job.external_job_id == parsed.external_job_id)
        job = self.db.scalar(select(Job).where(Job.provider == parsed.provider, or_(*lookup)))
        action = "updated"
        if not job:
            job = Job(
                source_id=parsed.source_id,
                provider=parsed.provider,
                job_url=parsed.job_url,
                canonical_url=parsed.canonical_url,
                job_title=parsed.job_title,
                first_seen_at=now,
                last_seen_at=now,
            )
            self.db.add(job)
            action = "created"

        job.source_id = parsed.source_id
        job.job_url = parsed.job_url
        job.external_job_id = parsed.external_job_id
        job.city_location = parsed.city_location
        job.job_title = parsed.job_title
        job.employer_name = parsed.employer_name
        job.employment_type = parsed.employment_type
        job.salary_range = parsed.salary_range
        job.description = parsed.description
        job.posted_at = parsed.posted_at
        job.last_seen_at = now
        job.content_hash = content_hash(parsed)
        job.raw_payload = json.dumps(parsed.raw_payload) if parsed.raw_payload is not None else None
        return job, action

    def update_user_fields(self, job: Job, is_applied: bool | None, is_favorite: bool | None, user_comments: str | None, status: str | None) -> Job:
        if is_favorite is not None:
            job.is_favorite = is_favorite
        if user_comments is not None:
            job.user_comments = user_comments
        if status is not None:
            job.status = status
        if is_applied is not None:
            job.is_applied = is_applied
            if is_applied:
                job.applied_at = job.applied_at or utc_now()
                job.status = "applied"
            else:
                job.applied_at = None
                if job.status == "applied":
                    job.status = "viewed"
        self._enforce_status_invariants(job)
        return job

    def _enforce_status_invariants(self, job: Job) -> None:
        if job.status == "applied":
            job.is_applied = True
            job.applied_at = job.applied_at or utc_now()
