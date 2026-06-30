from app.backend.ingestion.url_utils import canonicalize_url


def test_canonicalize_url_removes_tracking_params():
    url = "HTTPS://NZ.Seek.com/job/123/?utm_source=x&ref=y&origin=jobCard&page=2"

    assert canonicalize_url(url) == "https://nz.seek.com/job/123?page=2"
