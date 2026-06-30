#!/usr/bin/env python3
"""Mark a job as CV-generated after generated files exist."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import yaml


def require_file(path: str, label: str) -> Path:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise SystemExit(f"{label} does not exist: {file_path}")
    return file_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Update a job record after CV and cover letter generation.")
    parser.add_argument("job_id")
    parser.add_argument("--cv-docx", required=True)
    parser.add_argument("--cover-letter-docx", required=True)
    parser.add_argument("--cv-pdf", required=True)
    parser.add_argument("--cover-letter-pdf", required=True)
    parser.add_argument("--db", default="var/job_search.db")
    parser.add_argument("--config", default="antigravity/resources/output-locations.yaml")
    args = parser.parse_args()

    cv_docx = require_file(args.cv_docx, "CV DOCX")
    require_file(args.cover_letter_docx, "Cover letter DOCX")
    require_file(args.cv_pdf, "CV PDF")
    require_file(args.cover_letter_pdf, "Cover letter PDF")

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    status = config["database"]["generated_status"]

    connection = sqlite3.connect(args.db)
    cursor = connection.execute(
        """
        UPDATE jobs
        SET generated_cv_path = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (str(cv_docx), status, args.job_id),
    )
    if cursor.rowcount != 1:
        connection.rollback()
        raise SystemExit(f"Job not found or not updated: {args.job_id}")
    connection.commit()
    print(f"Marked job {args.job_id} as {status}")


if __name__ == "__main__":
    main()

