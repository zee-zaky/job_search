from app.backend.db.models import JobSource
from app.backend.ingestion.parsers.seek import SeekParser
from app.backend.ingestion.schemas import DiscoveredJob


def test_seek_parser_preserves_description_html_and_posted_date():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@type": "JobPosting",
            "title": "Data Engineer",
            "datePosted": "2026-06-20",
            "hiringOrganization": {"name": "Example Co"}
          }
        </script>
      </head>
      <body>
        <h1>Data Engineer</h1>
        <div data-automation="job-detail-location">Auckland</div>
        <div data-automation="jobAdDetails"><p>Build <strong>data</strong> products.</p></div>
        <script>{"listedAt":{"dateTimeUtc":"2026-06-21T01:02:03.000Z"}}</script>
      </body>
    </html>
    """

    parsed = SeekParser().parse_job_detail(
        DiscoveredJob(provider="seek", source_id="source", job_url="https://nz.seek.com/job/123"),
        html,
        "https://nz.seek.com/job/123",
    )

    assert parsed.description == '<div data-automation="jobAdDetails"><p>Build <strong>data</strong> products.</p></div>'
    assert parsed.posted_at is not None
    assert parsed.posted_at.date().isoformat() == "2026-06-20"


def test_seek_parser_reads_listed_at_when_json_ld_date_missing():
    html = """
    <html>
      <body>
        <h1>Data Engineer</h1>
        <div data-automation="jobAdDetails"><p>Build <strong>data</strong> products.</p></div>
        <script>{"listedAt":{"__typename":"SeekDateTime","label":"1h ago","dateTimeUtc":"2026-06-30T01:46:01.735Z"}}</script>
      </body>
    </html>
    """

    parsed = SeekParser().parse_job_detail(
        DiscoveredJob(provider="seek", source_id="source", job_url="https://nz.seek.com/job/123"),
        html,
        "https://nz.seek.com/job/123",
    )

    assert parsed.posted_at is not None
    assert parsed.posted_at.isoformat() == "2026-06-30T01:46:01.735000+00:00"


def test_seek_discovery_dedupes_origin_tracking_param():
    source = JobSource(id="source", name="SEEK", provider="seek", ingestion_mode="html_scraper", search_url="https://nz.seek.com/jobs")
    html = """
    <a href="/job/123?type=standard&ref=search-standalone">One</a>
    <a href="/job/123?type=standard&ref=search-standalone&origin=jobCard">One duplicate</a>
    """

    discovered = SeekParser().discover_job_links(source, html, "https://nz.seek.com/jobs")

    assert len(discovered) == 1
    assert discovered[0].external_job_id == "123"
