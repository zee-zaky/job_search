from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backend.config.settings import get_settings
from app.backend.db.models import JobSource
from app.backend.db.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed_sources(db: Session, seed_path: Path | None = None) -> int:
    path = seed_path or get_settings().seed_sources_path
    if not path.exists():
        return 0

    payload = yaml.safe_load(path.read_text()) or {}
    created = 0
    for item in payload.get("sources", []):
        exists = db.scalar(select(JobSource).where(JobSource.name == item["name"], JobSource.provider == item["provider"]))
        if exists:
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

