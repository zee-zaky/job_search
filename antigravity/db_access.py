#!/usr/bin/env python3
"""Database access module for antigravity CV tailoring agent.

Since antigravity runs independently in a separate IDE with limited folder access,
this module provides database connectivity using environment variables or absolute paths.

Usage:
    export JOB_SEARCH_DB_PATH="/absolute/path/to/job_search.db"
    # Then use this module to query and update jobs
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def get_db_path() -> Path:
    """Get database path from environment or defaults to workspace var folder."""
    db_env = os.environ.get("JOB_SEARCH_DB_PATH")
    if db_env:
        db_path = Path(db_env)
    else:
        # Try to find it relative to workspace root
        workspace_root = Path(__file__).resolve().parents[1]
        db_path = workspace_root / "var" / "job_search.db"

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}\n"
                                f"Set JOB_SEARCH_DB_PATH environment variable or ensure "
                                f"database exists at: {db_path}")
    return db_path


def get_connection() -> sqlite3.Connection:
    """Get a connection to the job search database."""
    db_path = get_db_path()
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def get_starred_jobs() -> list[dict[str, Any]]:
    """Load all starred/favourite jobs for CV tailoring.
    
    Returns:
        List of job records with all relevant fields.
    """
    connection = get_connection()
    try:
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
                generated_cv_path,
                user_comments
            FROM jobs
            WHERE is_favorite = 1
            ORDER BY posted_at IS NULL, posted_at DESC, last_seen_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_job_by_id(job_id: str) -> dict[str, Any] | None:
    """Get a single job record by ID.
    
    Args:
        job_id: The job ID to query.
        
    Returns:
        Job record dict or None if not found.
    """
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (job_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def update_job_cv_status(job_id: str, cv_path: str, status: str = "cv_generated") -> bool:
    """Update a job record after CV generation.
    
    Args:
        job_id: The job ID to update.
        cv_path: Path to the generated CV DOCX file.
        status: Status to set (default: "cv_generated").
        
    Returns:
        True if updated successfully, False if job not found.
    """
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            UPDATE jobs
            SET generated_cv_path = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (cv_path, status, job_id),
        )
        connection.commit()
        return cursor.rowcount == 1
    finally:
        connection.close()


def update_job_status(job_id: str, status: str, comments: str | None = None) -> bool:
    """Update job status and optionally add user comments.
    
    Args:
        job_id: The job ID to update.
        status: New status value.
        comments: Optional user comments to add.
        
    Returns:
        True if updated successfully, False if job not found.
    """
    connection = get_connection()
    try:
        if comments is not None:
            cursor = connection.execute(
                """
                UPDATE jobs
                SET status = ?, user_comments = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, comments, job_id),
            )
        else:
            cursor = connection.execute(
                """
                UPDATE jobs
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, job_id),
            )
        connection.commit()
        return cursor.rowcount == 1
    finally:
        connection.close()


def list_jobs_by_status(status: str) -> list[dict[str, Any]]:
    """Get all jobs with a specific status.
    
    Args:
        status: Status value to filter by.
        
    Returns:
        List of job records.
    """
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT * FROM jobs
            WHERE status = ?
            ORDER BY posted_at IS NULL, posted_at DESC, last_seen_at DESC
            """,
            (status,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
