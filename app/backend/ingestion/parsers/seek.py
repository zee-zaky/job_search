import json
import re
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from app.backend.db.models import JobSource
from app.backend.ingestion.schemas import DiscoveredJob, ParsedJob
from app.backend.ingestion.url_utils import canonicalize_url


class SeekParser:
    provider = "seek"

    def validate_source(self, source: JobSource) -> None:
        if source.ingestion_mode == "html_scraper" and not source.search_url:
            raise ValueError("SEEK html_scraper sources require search_url")

    def discover_job_links(self, source: JobSource, html: str, final_url: str) -> list[DiscoveredJob]:
        soup = BeautifulSoup(html, "html.parser")
        discovered: dict[str, DiscoveredJob] = {}
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "")
            if "/job/" not in href:
                continue
            job_url = urljoin(final_url, href)
            canonical = canonicalize_url(job_url)
            external_id = self._extract_job_id(canonical)
            discovered[canonical] = DiscoveredJob(
                provider=self.provider,
                source_id=source.id,
                job_url=job_url,
                external_job_id=external_id,
                title_hint=anchor.get_text(" ", strip=True) or None,
                raw_payload={"href": href},
            )
        return list(discovered.values())

    def search_page_urls(self, source: JobSource, first_page_html: str, final_url: str, max_pages: int) -> list[str]:
        if not source.search_url or max_pages <= 1:
            return []
        return [self._with_page(source.search_url, page) for page in range(2, max_pages + 1)]

    def parse_job_detail(self, discovered_job: DiscoveredJob, html: str, final_url: str) -> ParsedJob:
        soup = BeautifulSoup(html, "html.parser")
        json_ld = self._json_ld(soup)
        title = self._first_text(soup, ["h1", '[data-automation="job-detail-title"]'])
        employer = self._first_text(soup, ['[data-automation="advertiser-name"]'])
        location = self._first_text(soup, ['[data-automation="job-detail-location"]'])
        description = self._first_html(soup, ['[data-automation="jobAdDetails"]', "article"])
        posted_at = self._parse_posted_at(json_ld.get("datePosted")) if json_ld else None
        posted_at = posted_at or self._parse_listed_at(html)
        employment_type = self._parse_work_type(html)

        if json_ld:
            title = title or json_ld.get("title")
            org = json_ld.get("hiringOrganization") or {}
            employer = employer or org.get("name")
            location = location or self._location_from_json_ld(json_ld)
            description = description or json_ld.get("description")
            posted_at = posted_at or self._parse_posted_at(json_ld.get("validThrough"))
            employment_type = employment_type or self._normalize_work_type(json_ld.get("employmentType"))

        title = title or discovered_job.title_hint
        if not title:
            raise ValueError("Could not parse job title")

        return ParsedJob(
            provider=self.provider,
            source_id=discovered_job.source_id,
            job_url=discovered_job.job_url,
            canonical_url=canonicalize_url(final_url or discovered_job.job_url),
            external_job_id=discovered_job.external_job_id or self._extract_job_id(final_url),
            city_location=location or discovered_job.location_hint,
            job_title=title,
            employer_name=employer or discovered_job.employer_hint,
            employment_type=employment_type,
            salary_range=None,
            description=description,
            posted_at=posted_at,
            raw_payload={"json_ld": json_ld} if json_ld else discovered_job.raw_payload,
        )

    def _first_text(self, soup: BeautifulSoup, selectors: list[str]) -> str | None:
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                value = node.get_text(" ", strip=True)
                if value:
                    return value
        return None

    def _first_html(self, soup: BeautifulSoup, selectors: list[str]) -> str | None:
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                for unsafe in node.select("script, style"):
                    unsafe.decompose()
                value = str(node)
                if value:
                    return value
        return None

    def _json_ld(self, soup: BeautifulSoup) -> dict:
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or "{}")
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("@type") == "JobPosting":
                return payload
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        return item
        return {}

    def _location_from_json_ld(self, payload: dict) -> str | None:
        location = payload.get("jobLocation")
        if isinstance(location, list):
            location = location[0] if location else None
        if not isinstance(location, dict):
            return None
        address = location.get("address")
        if not isinstance(address, dict):
            return None
        parts = [address.get("addressLocality"), address.get("addressRegion"), address.get("addressCountry")]
        return ", ".join(part for part in parts if part) or None

    def _extract_job_id(self, url: str) -> str | None:
        match = re.search(r"/job/(\d+)", url)
        return match.group(1) if match else None

    def _parse_posted_at(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _parse_listed_at(self, html: str) -> datetime | None:
        match = re.search(r'"listedAt":\{.*?"dateTimeUtc":"([^"]+)"', html)
        return self._parse_posted_at(match.group(1)) if match else None

    def _parse_work_type(self, html: str) -> str | None:
        list_match = re.search(r'"workTypes":\{[^{}]*"label":\["([^"]+)"\]', html)
        if list_match:
            return self._normalize_work_type(list_match.group(1))
        text_match = re.search(r'"workTypes":\{[^{}]*"label":"([^"]+)"', html)
        if text_match:
            return self._normalize_work_type(text_match.group(1))
        return None

    def _normalize_work_type(self, value: str | list | None) -> str | None:
        if isinstance(value, list):
            value = value[0] if value else None
        if not isinstance(value, str) or not value:
            return None
        normalized = value.replace("_", " ").replace("-", " ").strip().lower()
        return " ".join(normalized.split()).capitalize()

    def _parse_total_jobs(self, html: str) -> int | None:
        candidates = [int(value) for value in re.findall(r'"totalCount":(\d+)', html)]
        candidates.extend(int(value.replace(",", "")) for value in re.findall(r'(\d[\d,]*)\s+jobs?', html, re.IGNORECASE))
        return max(candidates) if candidates else None

    def _with_page(self, url: str, page: int) -> str:
        parts = urlsplit(url)
        query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "page"]
        query.append(("page", str(page)))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
