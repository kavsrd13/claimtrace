"""
Tests for the documents router, including security checks.
"""

import io

import pytest


async def _create_session(client) -> str:
    resp = await client.post("/api/sessions", json={})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_upload_txt_document(client):
    session_id = await _create_session(client)
    content = b"This is document A.\n\nIt has two paragraphs."
    resp = await client.post(
        f"/api/sessions/{session_id}/documents",
        data={"slot": "0"},
        files={"file": ("doc_a.txt", io.BytesIO(content), "text/plain")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "doc_a.txt"
    assert data["slot"] == 0
    assert data["has_text"] is True


@pytest.mark.asyncio
async def test_upload_two_documents(client):
    session_id = await _create_session(client)
    for slot, name in [(0, "a.txt"), (1, "b.txt")]:
        content = f"Document {name} content paragraph one.\n\nParagraph two.".encode()
        resp = await client.post(
            f"/api/sessions/{session_id}/documents",
            data={"slot": str(slot)},
            files={"file": (name, io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 201

    list_resp = await client.get(f"/api/sessions/{session_id}/documents")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2


@pytest.mark.asyncio
async def test_prohibited_upload_exe(client):
    """Verify that uploading an .exe file is rejected."""
    session_id = await _create_session(client)
    content = b"MZ\x90\x00" + b"\x00" * 100  # fake PE header
    resp = await client.post(
        f"/api/sessions/{session_id}/documents",
        data={"slot": "0"},
        files={"file": ("malware.exe", io.BytesIO(content), "application/octet-stream")},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "FORBIDDEN_FILE_TYPE"


@pytest.mark.asyncio
async def test_prohibited_upload_zip(client):
    """Verify that uploading a .zip file is rejected."""
    session_id = await _create_session(client)
    resp = await client.post(
        f"/api/sessions/{session_id}/documents",
        data={"slot": "0"},
        files={"file": ("archive.zip", io.BytesIO(b"PK\x03\x04"), "application/zip")},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "FORBIDDEN_FILE_TYPE"


@pytest.mark.asyncio
async def test_upload_to_deleted_session(client):
    session_id = await _create_session(client)
    await client.delete(f"/api/sessions/{session_id}")

    resp = await client.post(
        f"/api/sessions/{session_id}/documents",
        data={"slot": "0"},
        files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_upload_replaces_same_slot(client):
    session_id = await _create_session(client)
    for content in [b"First version.", b"Second version."]:
        await client.post(
            f"/api/sessions/{session_id}/documents",
            data={"slot": "0"},
            files={"file": ("doc.txt", io.BytesIO(content), "text/plain")},
        )
    list_resp = await client.get(f"/api/sessions/{session_id}/documents")
    docs = list_resp.json()
    slot0_docs = [d for d in docs if d["slot"] == 0]
    assert len(slot0_docs) == 1
