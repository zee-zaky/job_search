# Job Search Tracker

This repository contains a local job-search tracking app that scrapes jobs from configured search sources and stores them in SQLite.

## Quick Start

1. Install dependencies (Python 3.11+).
2. Configure sources in the database or seed from `config/sources.yaml`.
3. Run the FastAPI backend.

## CLI Commands

The application should expose stable module-based commands so cron jobs and local scripts do not depend on file paths.

```bash
python -m app.backend.cli serve
python -m app.backend.cli ingest
python -m app.backend.cli cleanup-stale
```

If port `8000` is already in use, run:

```bash
python -m app.backend.cli serve --port 8001
```

## Scheduling on WSL

The app supports scheduled ingestion via a periodic command. In WSL, you can use `cron`.

### Example cron setup

1. Open WSL.
2. Install `cron` if needed:

```bash
sudo apt update
sudo apt install cron
sudo service cron start
```

3. Edit the crontab:

```bash
crontab -e
```

4. Add a line to run ingestion every hour:

```cron
0 * * * * cd /mnt/d/workspace/job_search && /usr/bin/env python -m app.backend.cli ingest >> /mnt/d/workspace/job_search/var/ingestion.log 2>&1
```

### Optional: daily stale cleanup

To run a daily stale-job cleanup or status refresh, add another cron entry:

```cron
0 2 * * * cd /mnt/d/workspace/job_search && /usr/bin/env python -m app.backend.cli cleanup-stale >> /mnt/d/workspace/job_search/var/cleanup.log 2>&1
```

## Notes

- The app is designed to use SQLite as the local database backend.
- The initial UI version uses server-rendered FastAPI templates.
- The scheduler respects `schedule_minutes` per source, so a single cron-driven ingestion command can evaluate each source and decide whether it should poll.
