"""
Tests for rate limiting quota headers, CSP, and sliding-window calculation.
"""

import pytest

from main import RateLimiter


@pytest.mark.asyncio
async def test_rate_limit_headers_in_response(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200

    headers = resp.headers
    assert "X-RateLimit-Limit" in headers
    assert "X-RateLimit-Remaining" in headers
    assert "X-RateLimit-Reset" in headers
    assert int(headers["X-RateLimit-Limit"]) == 120
    assert int(headers["X-RateLimit-Remaining"]) >= 0


@pytest.mark.asyncio
async def test_content_security_policy_header(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp


def test_rate_limiter_check_decrements_remaining():
    limiter = RateLimiter(requests_per_minute=3, window_sec=60)
    allowed1, rem1, _ = limiter.check("user-1", now=100.0)
    assert allowed1 is True
    assert rem1 == 2

    allowed2, rem2, _ = limiter.check("user-1", now=101.0)
    assert allowed2 is True
    assert rem2 == 1

    allowed3, rem3, _ = limiter.check("user-1", now=102.0)
    assert allowed3 is True
    assert rem3 == 0

    # 4th request: exceeded
    allowed4, rem4, reset_sec = limiter.check("user-1", now=103.0)
    assert allowed4 is False
    assert rem4 == 0
    assert reset_sec > 0
