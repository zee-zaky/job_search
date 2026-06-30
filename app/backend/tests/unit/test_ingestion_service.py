from types import SimpleNamespace

from app.backend.ingestion.fetcher import FetchError, FetchFailureKind
from app.backend.ingestion.schemas import DiscoveredJob
from app.backend.ingestion.service import IngestionService, RunCounts


class ExistingJobLookup:
    def __init__(self, existing_external_ids: set[str]):
        self.existing_external_ids = existing_external_ids

    def find_existing_discovered(self, discovered: DiscoveredJob):
        return object() if discovered.external_job_id in self.existing_external_ids else None


def test_page_limit_defaults_to_configured_default():
    service = IngestionService.__new__(IngestionService)
    service.fetcher = SimpleNamespace(settings=SimpleNamespace(default_pages_per_source=2, max_pages_per_source=10))

    assert service._page_limit(None) == 2


def test_page_limit_clamps_dashboard_override_to_configured_max():
    service = IngestionService.__new__(IngestionService)
    service.fetcher = SimpleNamespace(settings=SimpleNamespace(default_pages_per_source=2, max_pages_per_source=10))

    assert service._page_limit(3) == 3
    assert service._page_limit(99) == 10
    assert service._page_limit(0) == 1


def test_items_needing_detail_fetch_skips_existing_jobs():
    service = IngestionService.__new__(IngestionService)
    service.fetcher = SimpleNamespace(settings=SimpleNamespace(max_detail_fetches_per_source_run=10))
    service.jobs = ExistingJobLookup(existing_external_ids={"123"})
    counts = RunCounts()
    existing = DiscoveredJob(provider="seek", source_id="source", job_url="https://nz.seek.com/job/123", external_job_id="123")
    new = DiscoveredJob(provider="seek", source_id="source", job_url="https://nz.seek.com/job/456", external_job_id="456")

    assert service._items_needing_detail_fetch([existing, new], counts) == [new]
    assert counts.skipped_jobs_count == 1


def test_items_needing_detail_fetch_honors_detail_limit_after_skips():
    service = IngestionService.__new__(IngestionService)
    service.fetcher = SimpleNamespace(settings=SimpleNamespace(max_detail_fetches_per_source_run=1))
    service.jobs = ExistingJobLookup(existing_external_ids={"123"})
    counts = RunCounts()
    existing = DiscoveredJob(provider="seek", source_id="source", job_url="https://nz.seek.com/job/123", external_job_id="123")
    first_new = DiscoveredJob(provider="seek", source_id="source", job_url="https://nz.seek.com/job/456", external_job_id="456")
    second_new = DiscoveredJob(provider="seek", source_id="source", job_url="https://nz.seek.com/job/789", external_job_id="789")

    assert service._items_needing_detail_fetch([existing, first_new, second_new], counts) == [first_new]
    assert counts.skipped_jobs_count == 1


def test_should_stop_source_for_blocked_or_rate_limited_fetches():
    service = IngestionService.__new__(IngestionService)

    assert service._should_stop_source(FetchError("blocked", FetchFailureKind.BLOCKED)) is True
    assert service._should_stop_source(FetchError("rate limited", FetchFailureKind.RATE_LIMITED)) is True
    assert service._should_stop_source(FetchError("timeout", FetchFailureKind.TIMEOUT)) is False
