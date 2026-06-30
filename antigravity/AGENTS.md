# Antigravity CV Tailoring Workspace

Use this folder for agent-driven CV tailoring only. Keep generated CVs faithful to the candidate evidence in `references/`, the source DOCX templates in `templates/docx/`, and the job advert text stored in the application database.

## Running from a Separate IDE

Since antigravity only has access to its own folder, it must connect to the parent `job_search` database via environment variables. 

### Configuration

Before running any scripts that access the database, set:

```bash
export JOB_SEARCH_DB_PATH="/absolute/path/to/job_search.db"
```

Example on Linux/Mac:
```bash
export JOB_SEARCH_DB_PATH="/mnt/d/workspace/job_search/var/job_search.db"
```

If not set, the scripts will try to find the database at the default location relative to the workspace.

## Database Access for Agents

Antigravity has a dedicated `db_access.py` module for querying and updating the job database. This is already integrated into the CLI scripts.

### Available Database Operations

#### 1. **Load Starred Jobs** (Step 1 of workflow)

```bash
python scripts/list_starred_jobs.py [--db /path/to/job_search.db]
```

Returns JSON with all starred jobs. Sample fields:
- `id`: Job ID (required for updates)
- `job_title`, `employer_name`, `city_location`
- `job_url`: Link to apply
- `description`: Job posting text
- `status`: Current status (e.g., "new", "cv_generated", "applied")
- `generated_cv_path`: Path if CV already generated

#### 2. **Classify Jobs** (Step 2 of workflow)

Use the classifier script with loaded jobs:

```bash
python scripts/classify_job.py <job_id> <category> [--db /path/to/job_search.db]
```

Supported categories: `Integration`, `AI`, `BA`, `Sales`, `Dynamics 365`

#### 3. **Query Specific Job Status**

From within an agent or script, import and use:

```python
from db_access import get_job_by_id, list_jobs_by_status

# Get a single job
job = get_job_by_id("job_id_here")

# Get all jobs with a specific status
pending_jobs = list_jobs_by_status("new")
cv_generated = list_jobs_by_status("cv_generated")
```

#### 4. **Update Job Status** (Step 10 of workflow)

After generating CV/cover letter files, mark the job:

```bash
python scripts/mark_cv_generated.py <job_id> \
    --cv-docx /path/to/cv.docx \
    --cover-letter-docx /path/to/cover_letter.docx \
    --cv-pdf /path/to/cv.pdf \
    --cover-letter-pdf /path/to/cover_letter.pdf \
    [--db /path/to/job_search.db]
```

Or from Python:

```python
from db_access import update_job_cv_status, update_job_status

# After files are generated:
update_job_cv_status(
    job_id="job_id_here",
    cv_path="/path/to/cv.docx",
    status="cv_generated"
)

# Or update status with comments:
from db_access import update_job_status
update_job_status(
    job_id="job_id_here",
    status="applied",
    comments="Applied via company careers portal"
)
```

## Required Workflow

1. Load starred jobs only.
2. Classify each job into one or more supported categories: `Integration`, `AI`, `BA`, `Sales`, `Dynamics 365`.
3. Select the closest DOCX template from `resources/template-map.yaml`.
4. Use `references/cv-format-and-faithfulness.md` before writing or editing CV content.
5. Use the relevant `references/category-guides/*.md` file before tailoring title, summary, capabilities, career summary, and project examples.
6. Do not invent employers, dates, certifications, degrees, technologies, metrics, or project outcomes.
7. Adjust role titles only when the underlying duties and project evidence support the wording.
8. Store each generated CV package under `/mnt/d/OneDrive/Work Related/Career Related/CV/Generated/{Employer}/{yyyymmdd - Job Title}/`.
9. Generate four files per job: tailored CV DOCX, cover letter DOCX, CV PDF, and cover letter PDF.
10. After all four files exist, call `mark_cv_generated.py` or use `db_access.update_job_cv_status()` to update the job record with `status = cv_generated` and `generated_cv_path` pointing to the CV DOCX.
