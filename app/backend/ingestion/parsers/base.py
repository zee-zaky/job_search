from typing import Protocol

from app.backend.db.models import JobSource
from app.backend.ingestion.schemas import DiscoveredJob, ParsedJob


class JobSourceParser(Protocol):
    provider: str

    def validate_source(self, source: JobSource) -> None:
        ...

    def discover_job_links(self, source: JobSource, html: str, final_url: str) -> list[DiscoveredJob]:
        ...

    def parse_job_detail(self, discovered_job: DiscoveredJob, html: str, final_url: str) -> ParsedJob:
        ...

