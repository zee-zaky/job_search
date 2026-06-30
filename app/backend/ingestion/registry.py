from app.backend.ingestion.parsers.base import JobSourceParser


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, JobSourceParser] = {}

    def register(self, parser: JobSourceParser) -> None:
        self._parsers[parser.provider] = parser

    def get(self, provider: str) -> JobSourceParser:
        try:
            return self._parsers[provider]
        except KeyError as exc:
            raise KeyError(f"No parser registered for provider {provider}") from exc


registry = ParserRegistry()

