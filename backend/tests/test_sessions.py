"""
Tests for the sessions router.
"""

import pytest


@pytest.mark.asyncio
async def test_create_session(client):
    resp = await client.post("/api/sessions", json={})
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["is_expired"] is False
    assert data["document_count"] == 0


@pytest.mark.asyncio
async def test_create_session_with_title(client):
    resp = await client.post("/api/sessions", json={"title": "My Comparison"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "My Comparison"


@pytest.mark.asyncio
async def test_get_session(client):
    create_resp = await client.post("/api/sessions", json={})
    session_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == session_id


@pytest.mark.asyncio
async def test_get_nonexistent_session(client):
    resp = await client.get("/api/sessions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(client):
    create_resp = await client.post("/api/sessions", json={})
    session_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/sessions/{session_id}")
    assert del_resp.status_code == 204

    # Subsequent GET should return 410
    get_resp = await client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 410


@pytest.mark.asyncio
async def test_delete_nonexistent_session(client):
    resp = await client.delete("/api/sessions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
