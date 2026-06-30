#!/usr/bin/env python3
"""Prepare the employer/job output folder for generated CV artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import yaml


RESERVED_CHARS = r'[<>:"/\\|?*\x00-\x1f]'


def safe_name(value: str | None, fallback: str) -> str:
    cleaned = re.sub(RESERVED_CHARS, " ", value or fallback)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or fallback


def load_job(db_path: Path, job_id: str) -> dict:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    row = connection.execute(
        """
        SELECT id, job_title, employer_name, posted_at
        FROM jobs
        WHERE id = ?
        """,
        (job_id,),
    ).fetchone()
    if row is None:
        raise SystemExit(f"Job not found: {job_id}")
    return dict(row)


def job_date(value: str | None) -> str:
    if not value:
        return datetime.now().strftime("%Y%m%d")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y%m%d")
    except ValueError:
        return datetime.now().strftime("%Y%m%d")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the generated-CV output folder for a job.")
    parser.add_argument("job_id")
    parser.add_argument("--db", default="var/job_search.db")
    parser.add_argument("--config", default="antigravity/resources/output-locations.yaml")
    parser.add_argument("--no-create", action="store_true", help="Print paths without creating directories.")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    job = load_job(Path(args.db), args.job_id)
    employer = safe_name(job.get("employer_name"), "Unknown Employer")
    title = safe_name(job.get("job_title"), "Untitled Job")
    yyyymmdd = job_date(job.get("posted_at"))

    output_dir = Path(config["base_generated_folder"]) / employer / config["job_folder"].format(
        yyyymmdd=yyyymmdd,
        job_title=title,
    )
    if not args.no_create:
        output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        key: str(output_dir / pattern.format(job_title=title))
        for key, pattern in config["files"].items()
    }
    print(json.dumps({"job_id": args.job_id, "output_dir": str(output_dir), "files": files}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

