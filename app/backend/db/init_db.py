from pathlib import Path

import yaml
from sqlalchemy import inspect, text
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backend.config.settings import get_settings
from app.backend.db.models import JobSource
from app.backend.db.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()


def ensure_sqlite_schema() -> None:
    if not engine.url.drivername.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return
    job_columns = {column["name"] for column in inspector.get_columns("jobs")}
    with engine.begin() as connection:
        if "generated_cv_path" not in job_columns:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN generated_cv_path TEXT"))


def seed_sources(db: Session, seed_path: Path | None = None) -> int:
    path = seed_path or get_settings().seed_sources_path
    if not path.exists():
        return 0

    payload = yaml.safe_load(path.read_text()) or {}
    created = 0
    for item in payload.get("sources", []):
        exists = db.scalar(select(JobSource).where(JobSource.search_url == item.get("search_url")))
        if not exists:
            exists = db.scalar(select(JobSource).where(JobSource.name == item["name"], JobSource.provider == item["provider"]))
        if exists:
            changed = False
            for key in ["description", "enabled", "ingestion_mode", "search_url", "schedule_minutes"]:
                value = item.get(key)
                if key == "enabled":
                    value = item.get(key, True)
                if key == "schedule_minutes":
                    value = item.get(key, 60)
                if getattr(exists, key) != value:
                    setattr(exists, key, value)
                    changed = True
            if changed:
                created += 0
            continue
        db.add(
            JobSource(
                name=item["name"],
                provider=item["provider"],
                description=item.get("description"),
                enabled=item.get("enabled", True),
                ingestion_mode=item["ingestion_mode"],
                search_url=item.get("search_url"),
                schedule_minutes=item.get("schedule_minutes", 60),
            )
        )
        created += 1
    db.commit()
    return created
