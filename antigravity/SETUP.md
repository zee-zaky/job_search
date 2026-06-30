# Antigravity Setup Guide

This guide explains how to run the antigravity CV tailoring agent from a separate IDE with limited folder access.

## Prerequisites

- Python 3.11+ (same as main job_search app)
- Access to the job_search database file (`var/job_search.db`)

## Installation

1. Copy the `antigravity/` folder to your separate IDE workspace.

2. Install dependencies (if any):
   ```bash
   # The main app dependencies are required for database access
   pip install pyyaml
   ```

3. Configure the database path:
   ```bash
   # On Linux/Mac/WSL:
   export JOB_SEARCH_DB_PATH="/mnt/d/workspace/job_search/var/job_search.db"
   
   # On Windows PowerShell:
   $env:JOB_SEARCH_DB_PATH = "C:\path\to\job_search\var\job_search.db"
   ```

## Usage Examples

### Load Starred Jobs

```bash
python scripts/list_starred_jobs.py
```

This outputs JSON with all starred jobs. Use this to feed into your CV tailoring pipeline.

### Classify a Job

```bash
python scripts/classify_job.py <job_id> Integration
```

### Mark Job as CV Generated

After your agent generates the CV, cover letter, and PDFs:

```bash
python scripts/mark_cv_generated.py <job_id> \
    --cv-docx "/path/to/generated/cv.docx" \
    --cover-letter-docx "/path/to/generated/cover_letter.docx" \
    --cv-pdf "/path/to/generated/cv.pdf" \
    --cover-letter-pdf "/path/to/generated/cover_letter.pdf"
```

## Python API

For agents or custom scripts, use the `db_access` module directly:

```python
from db_access import (
    get_starred_jobs,
    get_job_by_id,
    update_job_cv_status,
    update_job_status,
    list_jobs_by_status,
)

# Load all starred jobs
jobs = get_starred_jobs()

# Get a specific job
job = get_job_by_id("job-id-123")

# Update job status after CV generation
update_job_cv_status(
    job_id="job-id-123",
    cv_path="/path/to/cv.docx"
)

# Update status with comments
update_job_status(
    job_id="job-id-123",
    status="applied",
    comments="Sent via careers portal"
)

# List jobs by status
pending = list_jobs_by_status("new")
generated = list_jobs_by_status("cv_generated")
```

## Database Path Resolution

The `db_access` module resolves the database path in this order:

1. `JOB_SEARCH_DB_PATH` environment variable (if set)
2. Default relative path: `../var/job_search.db` (relative to antigravity folder)
3. Raises `FileNotFoundError` if not found

So if you set the environment variable, the scripts will always find the database regardless of where they're called from.

## Troubleshooting

### Database Not Found Error

```
FileNotFoundError: Database not found: /path/to/job_search.db
```

**Solution:** Set the `JOB_SEARCH_DB_PATH` environment variable to the correct absolute path.

### Job Not Found When Updating

```
✗ Job not found: <job_id>
```

**Solution:** Verify the job ID is correct. Use `python scripts/list_starred_jobs.py` to list all starred jobs and their IDs.

### Module Import Errors

If you get import errors when importing `db_access` from an agent script:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db_access
```

## Integration with Agents

When configuring your CV tailoring agent to use these scripts:

1. Ensure `JOB_SEARCH_DB_PATH` is set in the agent's environment
2. Call scripts with absolute paths or set working directory correctly
3. Parse JSON output from `list_starred_jobs.py` to get job data
4. Use the `db_access` module directly for better error handling

## Database Schema Reference

Key job fields available for querying:

- `id`: Unique job identifier
- `job_title`: Job title from posting
- `employer_name`: Company name
- `city_location`: Location
- `job_url`: Link to original posting
- `description`: Full job description HTML/text
- `status`: Current status ("new", "cv_generated", "applied", etc.)
- `is_favorite`: Boolean (1 if starred)
- `generated_cv_path`: Path to generated CV if status is "cv_generated"
- `user_comments`: Free-form notes
- `posted_at`: When job was posted
- `first_seen_at`, `last_seen_at`: Tracking dates
