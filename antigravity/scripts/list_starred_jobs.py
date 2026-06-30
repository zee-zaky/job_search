#!/usr/bin/env python3
"""List starred/favourite jobs from the local job-search SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="List starred jobs as JSON for CV tailoring agents.")
    parser.add_argument("--db", default="var/job_search.db", help="Path to the SQLite database.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        SELECT
            id,
            provider,
            source_id,
            job_title,
            employer_name,
            city_location,
            employment_type,
            job_url,
            description,
            posted_at,
            status,
            is_favorite,
            is_applied,
            generated_cv_path
        FROM jobs
        WHERE is_favorite = 1
        ORDER BY posted_at IS NULL, posted_at DESC, last_seen_at DESC
        """
    ).fetchall()
    print(json.dumps([dict(row) for row in rows], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

