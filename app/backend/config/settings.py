from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JOB_TRACKER_", env_file=".env", extra="ignore")

    database_url: str = Field(default=f"sqlite:///{BASE_DIR / 'var' / 'job_search.db'}")
    seed_sources_path: Path = Field(default=BASE_DIR / "config" / "sources.yaml")
    stale_days: int = 14
    request_timeout_seconds: float = 20
    connect_timeout_seconds: float = 5
    max_retries: int = 2
    default_request_delay_seconds: float = 5
    default_pages_per_source: int = 2
    max_pages_per_source: int = 10
    max_discovered_jobs_per_source: int = 300
    max_detail_fetches_per_source_run: int = 300
    max_response_bytes: int = 5 * 1024 * 1024
    user_agent: str = "JobSearchTracker/0.1 (+local personal job tracking app)"


@lru_cache
def get_settings() -> Settings:
    return Settings()
