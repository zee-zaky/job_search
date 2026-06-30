import asyncio
from dataclasses import dataclass
from enum import StrEnum

import httpx

from app.backend.config.settings import Settings, get_settings


class FetchFailureKind(StrEnum):
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    TRANSIENT = "transient"
    PERMANENT = "permanent"


class FetchError(RuntimeError):
    def __init__(self, message: str, kind: FetchFailureKind, status_code: int | None = None):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    text: str
    elapsed_ms: int
    retry_count: int


class Fetcher:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    async def fetch(self, url: str) -> FetchResult:
        timeout = httpx.Timeout(
            timeout=self.settings.request_timeout_seconds,
            connect=self.settings.connect_timeout_seconds,
        )
        headers = {"User-Agent": self.settings.user_agent, "Accept": "text/html,application/xhtml+xml"}
        last_error: FetchError | None = None

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            for attempt in range(self.settings.max_retries + 1):
                try:
                    response = await client.get(url)
                    body = response.text
                    if len(response.content) > self.settings.max_response_bytes:
                        raise FetchError("Response exceeded configured maximum size", FetchFailureKind.PERMANENT)
                    if response.status_code in {401, 403}:
                        raise FetchError("Fetch blocked by provider", FetchFailureKind.BLOCKED, response.status_code)
                    if response.status_code == 429:
                        raise FetchError("Fetch rate-limited by provider", FetchFailureKind.RATE_LIMITED, 429)
                    if 500 <= response.status_code < 600:
                        raise FetchError("Provider returned a transient server error", FetchFailureKind.TRANSIENT, response.status_code)
                    if response.status_code >= 400:
                        raise FetchError("Provider returned a permanent fetch error", FetchFailureKind.PERMANENT, response.status_code)
                    return FetchResult(
                        url=url,
                        final_url=str(response.url),
                        status_code=response.status_code,
                        text=body,
                        elapsed_ms=int(response.elapsed.total_seconds() * 1000),
                        retry_count=attempt,
                    )
                except httpx.TimeoutException as exc:
                    last_error = FetchError(str(exc) or "Fetch timed out", FetchFailureKind.TIMEOUT)
                except httpx.HTTPError as exc:
                    last_error = FetchError(str(exc), FetchFailureKind.TRANSIENT)
                except FetchError as exc:
                    last_error = exc
                    if exc.kind not in {FetchFailureKind.RATE_LIMITED, FetchFailureKind.TRANSIENT, FetchFailureKind.TIMEOUT}:
                        raise

                if attempt < self.settings.max_retries:
                    await asyncio.sleep(self._backoff_seconds(attempt))

        raise last_error or FetchError("Fetch failed", FetchFailureKind.TRANSIENT)

    def _backoff_seconds(self, attempt: int) -> float:
        return min(30.0, self.settings.default_request_delay_seconds * (2**attempt))

