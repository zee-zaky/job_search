from datetime import datetime

from pydantic import BaseModel, HttpUrl


class DiscoveredJob(BaseModel):
    provider: str
    source_id: str
    job_url: str
    external_job_id: str | None = None
    title_hint: str | None = None
    employer_hint: str | None = None
    location_hint: str | None = None
    raw_payload: dict | None = None


class ParsedJob(BaseModel):
    provider: str
    source_id: str
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
    raw_payload: dict | None = None


class ManualImportRequest(BaseModel):
    source_id: str
    provider: str
    job_url: HttpUrl


class IngestionRunRequest(BaseModel):
    source_id: str | None = None

