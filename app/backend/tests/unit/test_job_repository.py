from app.backend.db.models import Job
from app.backend.jobs.repository import JobRepository


def test_applied_status_sets_applied_fields():
    repo = JobRepository(db=None)
    job = Job(
        source_id="source",
        provider="seek",
        job_url="https://example.com/job/1",
        canonical_url="https://example.com/job/1",
        job_title="Engineer",
    )

    repo.update_user_fields(job, True, None, None, None)

    assert job.status == "applied"
    assert job.is_applied is True
    assert job.applied_at is not None


def test_clearing_applied_moves_status_to_viewed():
    repo = JobRepository(db=None)
    job = Job(
        source_id="source",
        provider="seek",
        job_url="https://example.com/job/1",
        canonical_url="https://example.com/job/1",
        job_title="Engineer",
        status="applied",
        is_applied=True,
    )

    repo.update_user_fields(job, False, None, None, None)

    assert job.status == "viewed"
    assert job.is_applied is False
    assert job.applied_at is None

