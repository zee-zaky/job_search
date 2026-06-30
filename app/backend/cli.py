import argparse
import asyncio

import uvicorn

from app.backend.db.init_db import init_db, seed_sources
from app.backend.db.session import SessionLocal
from app.backend.ingestion.parsers.seek import SeekParser
from app.backend.ingestion.registry import registry
from app.backend.ingestion.service import IngestionService


def bootstrap() -> None:
    registry.register(SeekParser())
    init_db()
    with SessionLocal() as db:
        seed_sources(db)


async def run_ingestion() -> None:
    bootstrap()
    with SessionLocal() as db:
        run = await IngestionService(db).run()
        print(f"run_id={run.run_id} status={run.status} new={run.new_jobs_count} updated={run.updated_jobs_count} errors={run.error_count}")


def cleanup_stale() -> None:
    bootstrap()
    print("cleanup-stale command is reserved; stale policy is specified but not implemented in the first skeleton.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Search Tracker CLI")
    subcommands = parser.add_subparsers(dest="command", required=True)
    serve_parser = subcommands.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    subcommands.add_parser("ingest")
    subcommands.add_parser("cleanup-stale")
    args = parser.parse_args()

    if args.command == "serve":
        bootstrap()
        uvicorn.run("app.backend.main:app", host=args.host, port=args.port, reload=False)
    elif args.command == "ingest":
        asyncio.run(run_ingestion())
    elif args.command == "cleanup-stale":
        cleanup_stale()


if __name__ == "__main__":
    main()
