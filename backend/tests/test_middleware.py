"""
Tests for security headers, request tracing, readiness check, and rate limiting middleware.
"""

import pytest

from main import RateLimiter


@pytest.mark.asyncio
async def test_ready_endpoint(client):
    resp = await client.get("/api/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_security_headers_present(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    headers = resp.headers

    # Verify OWASP recommended security headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "microphone=()" in headers.get("Permissions-Policy", "")

    # Tracing headers
    assert "X-Request-ID" in headers
    assert "X-Response-Time-MS" in headers


def test_rate_limiter_allows_under_limit():
    limiter = RateLimiter(requests_per_minute=5)
    for _ in range(5):
        assert limiter.is_allowed("192.168.1.1") is True


def test_rate_limiter_blocks_over_limit():
    limiter = RateLimiter(requests_per_minute=3)
    for _ in range(3):
        assert limiter.is_allowed("10.0.0.1") is True
    assert limiter.is_allowed("10.0.0.1") is False


def test_rate_limiter_tracks_different_ips_separately():
    limiter = RateLimiter(requests_per_minute=2)
    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is False

    # client-b should have its own quota
    assert limiter.is_allowed("client-b") is True
    assert limiter.is_allowed("client-b") is True
    assert limiter.is_allowed("client-b") is False
