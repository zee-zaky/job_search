from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    provider: str
    job_url: str
    canonical_url: str
    external_job_id: str | None = None
    city_location: str | None = None
    job_title: str
    employer_name: str | None = None
    employment_type: str | None = None
    salary_range: str | None = None
    description: str | None = None
    posted_at: datetime | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    is_applied: bool
    applied_at: datetime | None = None
    is_favorite: bool
    generated_cv_path: str | None = None
    user_comments: str | None = None
    status: str


class JobUpdate(BaseModel):
    is_applied: bool | None = None
    is_favorite: bool | None = None
    generated_cv_path: str | None = None
    user_comments: str | None = None
    status: str | None = None
