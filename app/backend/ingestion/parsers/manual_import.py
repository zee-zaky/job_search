from app.backend.ingestion.parsers.seek import SeekParser


class ManualImportParser(SeekParser):
    """Placeholder parser alias for manual imports that use SEEK-compatible pages."""

    provider = "manual_import"

