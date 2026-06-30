import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backend.db.models import IngestionRun, IngestionRunSource, JobSource, utc_now
from app.backend.ingestion.fetcher import Fetcher, FetchError, FetchFailureKind
from app.backend.ingestion.registry import ParserRegistry, registry
from app.backend.ingestion.schemas import DiscoveredJob, ManualImportRequest
from app.backend.ingestion.url_utils import canonicalize_url
from app.backend.jobs.repository import JobRepository


@dataclass
class RunCounts:
    new_jobs_count: int = 0
    updated_jobs_count: int = 0
    skipped_jobs_count: int = 0
    error_count: int = 0
    errors: list[dict] = field(default_factory=list)


class IngestionService:
    def __init__(self, db: Session, parser_registry: ParserRegistry | None = None, fetcher: Fetcher | None = None):
        self.db = db
        self.registry = parser_registry or registry
        self.fetcher = fetcher or Fetcher()
        self.jobs = JobRepository(db)

    async def run(self, source_id: str | None = None, max_pages_per_source: int | None = None) -> IngestionRun:
        run = IngestionRun(status="running")
        self.db.add(run)
        self.db.commit()
        page_limit = self._page_limit(max_pages_per_source)

        stmt = select(JobSource).where(JobSource.enabled == True)  # noqa: E712
        if source_id:
            stmt = stmt.where(JobSource.id == source_id)
        sources = list(self.db.scalars(stmt))

        total = RunCounts()
        for source in sources:
            if source.ingestion_mode != "html_scraper":
                total.skipped_jobs_count += 1
                continue
            counts = await self._run_source(run.run_id, source, page_limit)
            self._merge_counts(total, counts)

        self._finish_run(run, total)
        self.db.commit()
        return run

    async def import_job(self, request: ManualImportRequest) -> tuple[IngestionRun, str | None, str]:
        source = self.db.get(JobSource, request.source_id)
        if not source:
            raise ValueError("Manual import source not found")
        if not source.enabled or source.ingestion_mode != "manual_import":
            raise ValueError("Source is not enabled for manual import")
        if source.provider != request.provider:
            raise ValueError("Provider does not match source")

        run = IngestionRun(status="running")
        self.db.add(run)
        self.db.commit()
        child = self._start_source_run(run.run_id, source)
        counts = RunCounts()
        action = "skipped"
        job_id: str | None = None

        try:
            parser = self.registry.get(source.provider)
            discovered = type("ManualDiscovered", (), {})()
            from app.backend.ingestion.schemas import DiscoveredJob

            fetched = await self.fetcher.fetch(str(request.job_url))
            parsed = parser.parse_job_detail(
                DiscoveredJob(provider=source.provider, source_id=source.id, job_url=str(request.job_url)),
                fetched.text,
                fetched.final_url,
            )
            job, action = self.jobs.upsert_from_parsed(parsed)
            self.db.flush()
            job_id = job.id
            if action == "created":
                counts.new_jobs_count += 1
            else:
                counts.updated_jobs_count += 1
            child.status = "success"
        except Exception as exc:
            counts.error_count += 1
            counts.errors.append({"error_code": "MANUAL_IMPORT_FAILED", "message": str(exc), "source_id": source.id})
            child.status = "failed"

        self._finish_source_run(child, counts)
        self._finish_run(run, counts)
        self.db.commit()
        return run, job_id, action

    async def _run_source(self, run_id: str, source: JobSource, max_pages_per_source: int) -> RunCounts:
        child = self._start_source_run(run_id, source)
        self.db.commit()
        counts = RunCounts()
        try:
            parser = self.registry.get(source.provider)
            parser.validate_source(source)
            if not source.search_url:
                raise ValueError("html_scraper source requires search_url")
            fetched = await self.fetcher.fetch(source.search_url)
            discovered = self._dedupe_discovered(parser.discover_job_links(source, fetched.text, fetched.final_url))
            for page_url in self._search_page_urls(parser, source, fetched.text, fetched.final_url, max_pages_per_source):
                if len(discovered) >= self.fetcher.settings.max_discovered_jobs_per_source:
                    break
                await self._polite_delay()
                page = await self.fetcher.fetch(page_url)
                discovered.update(self._dedupe_discovered(parser.discover_job_links(source, page.text, page.final_url)))
            for item in self._items_needing_detail_fetch(discovered.values(), counts):
                try:
                    await self._polite_delay()
                    detail = await self.fetcher.fetch(item.job_url)
                    parsed = parser.parse_job_detail(item, detail.text, detail.final_url)
                    _, action = self.jobs.upsert_from_parsed(parsed)
                    self.db.commit()
                    if action == "created":
                        counts.new_jobs_count += 1
                    else:
                        counts.updated_jobs_count += 1
                except Exception as exc:
                    self.db.rollback()
                    if self._should_stop_source(exc):
                        counts.error_count += 1
                        counts.errors.append(
                            {
                                "error_code": "SOURCE_STOPPED",
                                "message": str(exc),
                                "job_url": item.job_url,
                            }
                        )
                        break
                    counts.error_count += 1
                    counts.errors.append({"error_code": "PARSE_FAILED", "message": str(exc), "job_url": item.job_url})
            source.last_success_at = utc_now()
            child.status = "success" if counts.error_count == 0 else "partial_failure"
        except Exception as exc:
            self.db.rollback()
            counts.error_count += 1
            counts.errors.append({"error_code": "SOURCE_FAILED", "message": str(exc), "source_id": source.id})
            child = self.db.get(IngestionRunSource, child.id) or child
            child.status = "failed"
        finally:
            source = self.db.get(JobSource, source.id) or source
            child = self.db.get(IngestionRunSource, child.id) or child
            source.last_run_at = utc_now()
            self._finish_source_run(child, counts)
            self.db.commit()
        return counts

    def _search_page_urls(
        self,
        parser: Any,
        source: JobSource,
        first_page_html: str,
        final_url: str,
        max_pages_per_source: int,
    ) -> list[str]:
        if hasattr(parser, "search_page_urls"):
            return parser.search_page_urls(source, first_page_html, final_url, max_pages_per_source)
        return []

    def _items_needing_detail_fetch(self, discovered: Any, counts: RunCounts) -> list[DiscoveredJob]:
        items = []
        for item in discovered:
            if self.jobs.find_existing_discovered(item):
                counts.skipped_jobs_count += 1
                continue
            items.append(item)
            if len(items) >= self.fetcher.settings.max_detail_fetches_per_source_run:
                break
        return items

    async def _polite_delay(self) -> None:
        delay = self.fetcher.settings.default_request_delay_seconds
        if delay > 0:
            await asyncio.sleep(delay)

    def _should_stop_source(self, exc: Exception) -> bool:
        return isinstance(exc, FetchError) and exc.kind in {FetchFailureKind.BLOCKED, FetchFailureKind.RATE_LIMITED}

    def _page_limit(self, requested_max_pages: int | None) -> int:
        configured_max = self.fetcher.settings.max_pages_per_source
        if requested_max_pages is None:
            return max(1, min(self.fetcher.settings.default_pages_per_source, configured_max))
        return max(1, min(requested_max_pages, configured_max))

    def _dedupe_discovered(self, discovered: list[DiscoveredJob]) -> dict[str, DiscoveredJob]:
        deduped: dict[str, DiscoveredJob] = {}
        for item in discovered:
            key = f"{item.provider}:{item.external_job_id}" if item.external_job_id else canonicalize_url(item.job_url)
            deduped[key] = item
        return deduped

    def _start_source_run(self, run_id: str, source: JobSource) -> IngestionRunSource:
        child = IngestionRunSource(
            run_id=run_id,
            source_id=source.id,
            provider=source.provider,
            ingestion_mode=source.ingestion_mode,
            status="running",
        )
        self.db.add(child)
        self.db.flush()
        return child

    def _finish_source_run(self, child: IngestionRunSource, counts: RunCounts) -> None:
        child.finished_at = utc_now()
        child.new_jobs_count = counts.new_jobs_count
        child.updated_jobs_count = counts.updated_jobs_count
        child.skipped_jobs_count = counts.skipped_jobs_count
        child.error_count = counts.error_count
        child.errors = json.dumps(counts.errors) if counts.errors else None

    def _finish_run(self, run: IngestionRun, counts: RunCounts) -> None:
        run.finished_at = utc_now()
        run.new_jobs_count = counts.new_jobs_count
        run.updated_jobs_count = counts.updated_jobs_count
        run.skipped_jobs_count = counts.skipped_jobs_count
        run.error_count = counts.error_count
        run.errors = json.dumps(counts.errors) if counts.errors else None
        run.status = "success" if counts.error_count == 0 else "partial_failure"

    def _merge_counts(self, target: RunCounts, source: RunCounts) -> None:
        target.new_jobs_count += source.new_jobs_count
        target.updated_jobs_count += source.updated_jobs_count
        target.skipped_jobs_count += source.skipped_jobs_count
        target.error_count += source.error_count
        target.errors.extend(source.errors)
