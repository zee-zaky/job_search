from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class JobSource(Base, TimestampMixin):
    __tablename__ = "job_sources"
    __table_args__ = (
        CheckConstraint(
            "(ingestion_mode = 'html_scraper' AND search_url IS NOT NULL) "
            "OR ingestion_mode IN ('manual_import', 'disabled')",
            name="ck_job_sources_search_url_mode",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ingestion_mode: Mapped[str] = mapped_column(String, nullable=False)
    search_url: Mapped[str | None] = mapped_column(Text)
    schedule_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    jobs: Mapped[list["Job"]] = relationship(back_populates="source")


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("idx_jobs_provider_canonical_url", "provider", "canonical_url", unique=True),
        Index("idx_jobs_provider_external_id", "provider", "external_job_id", unique=True),
        Index("idx_jobs_source_id", "source_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_last_seen_at", "last_seen_at"),
        Index("idx_jobs_first_seen_at", "first_seen_at"),
        Index("idx_jobs_is_favorite", "is_favorite"),
        Index("idx_jobs_is_applied", "is_applied"),
        Index("idx_jobs_provider", "provider"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("job_sources.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    job_url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    external_job_id: Mapped[str | None] = mapped_column(String)
    city_location: Mapped[str | None] = mapped_column(String)
    job_title: Mapped[str] = mapped_column(String, nullable=False)
    employer_name: Mapped[str | None] = mapped_column(String)
    employment_type: Mapped[str | None] = mapped_column(String)
    salary_range: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String)
    raw_payload: Mapped[str | None] = mapped_column(Text)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generated_cv_path: Mapped[str | None] = mapped_column(Text)
    user_comments: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="new", nullable=False)

    source: Mapped[JobSource] = relationship(back_populates="jobs")


class IngestionRun(Base, TimestampMixin):
    __tablename__ = "ingestion_runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, default="running", nullable=False)
    new_jobs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_jobs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_jobs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[str | None] = mapped_column(Text)

    source_runs: Mapped[list["IngestionRunSource"]] = relationship(back_populates="run")


class IngestionRunSource(Base, TimestampMixin):
    __tablename__ = "ingestion_run_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.run_id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("job_sources.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    ingestion_mode: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, default="running", nullable=False)
    new_jobs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_jobs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_jobs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[str | None] = mapped_column(Text)

    run: Mapped[IngestionRun] = relationship(back_populates="source_runs")
