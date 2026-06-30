#!/usr/bin/env python3
"""List starred/favourite jobs from the local job-search SQLite database.

This script queries the job_search database for all starred jobs to feed into CV tailoring workflows.

Usage:
    # Set database path (required when running from separate IDE):
    export JOB_SEARCH_DB_PATH="/absolute/path/to/job_search.db"
    
    # Then run:
    python scripts/list_starred_jobs.py
    
    # Or override database path via command line:
    python scripts/list_starred_jobs.py --db /path/to/job_search.db
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import db_access
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db_access


def main() -> None:
    parser = argparse.ArgumentParser(description="List starred jobs as JSON for CV tailoring agents.")
    parser.add_argument(
        "--db",
        default=None,
        help="Path to the SQLite database. If not provided, uses JOB_SEARCH_DB_PATH env var or defaults to workspace var/job_search.db"
    )
    args = parser.parse_args()

    # Set environment variable if provided
    if args.db:
        os.environ["JOB_SEARCH_DB_PATH"] = args.db

    try:
        jobs = db_access.get_starred_jobs()
        print(json.dumps(jobs, indent=2, ensure_ascii=False, default=str))
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

