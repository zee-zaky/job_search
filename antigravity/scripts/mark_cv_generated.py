#!/usr/bin/env python3
"""Mark a job as CV-generated after generated files exist.

Usage:
    # Set database path (required when running from separate IDE):
    export JOB_SEARCH_DB_PATH="/absolute/path/to/job_search.db"
    
    # Then run:
    python scripts/mark_cv_generated.py <job_id> \\
        --cv-docx /path/to/cv.docx \\
        --cover-letter-docx /path/to/cover_letter.docx \\
        --cv-pdf /path/to/cv.pdf \\
        --cover-letter-pdf /path/to/cover_letter.pdf
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import db_access
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db_access


def require_file(path: str, label: str) -> Path:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise SystemExit(f"{label} does not exist: {file_path}")
    return file_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Update a job record after CV and cover letter generation.")
    parser.add_argument("job_id", help="The job ID to update")
    parser.add_argument("--cv-docx", required=True, help="Path to generated CV DOCX file")
    parser.add_argument("--cover-letter-docx", required=True, help="Path to generated cover letter DOCX file")
    parser.add_argument("--cv-pdf", required=True, help="Path to generated CV PDF file")
    parser.add_argument("--cover-letter-pdf", required=True, help="Path to generated cover letter PDF file")
    parser.add_argument("--db", default=None, help="Path to database. Uses JOB_SEARCH_DB_PATH env var if not provided")
    args = parser.parse_args()

    # Validate all files exist
    cv_docx = require_file(args.cv_docx, "CV DOCX")
    require_file(args.cover_letter_docx, "Cover letter DOCX")
    require_file(args.cv_pdf, "CV PDF")
    require_file(args.cover_letter_pdf, "Cover letter PDF")

    # Set environment variable if provided
    if args.db:
        os.environ["JOB_SEARCH_DB_PATH"] = args.db

    try:
        # Update the job record with CV path and status
        success = db_access.update_job_cv_status(
            job_id=args.job_id,
            cv_path=str(cv_docx),
            status="cv_generated"
        )

        if success:
            print(f"✓ Job {args.job_id} updated with CV path: {cv_docx}")
        else:
            print(f"✗ Job not found: {args.job_id}", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
    connection.commit()
    print(f"Marked job {args.job_id} as {status}")


if __name__ == "__main__":
    main()

