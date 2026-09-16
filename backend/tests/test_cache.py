"""
Tests for embedding cache behavior in services.llm.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.llm as llm_module
from services.llm import _EMBEDDING_CACHE, _text_hash, embed_texts


@pytest.fixture(autouse=True)
def clear_embedding_cache():
    """Clear in-memory cache before and after each test."""
    _EMBEDDING_CACHE.clear()
    yield
    _EMBEDDING_CACHE.clear()


def test_text_hash_is_deterministic():
    text = "Payment is due net-30 days."
    h1 = _text_hash(text)
    h2 = _text_hash(text)
    assert h1 == h2
    assert len(h1) == 64  # SHA256 hex length
    # Leading/trailing whitespace trimmed
    assert _text_hash("  " + text + " \n") == h1


@pytest.mark.asyncio
async def test_embed_texts_uses_cache():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_item = MagicMock()
    mock_item.embedding = [0.1, 0.2, 0.3]
    mock_response.data = [mock_item]
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    with patch.object(llm_module, "_get_client", return_value=mock_client):
        # First call: cache miss
        result1 = await embed_texts(["Clause 1: Confidentiality"])
        assert result1 == [[0.1, 0.2, 0.3]]
        assert mock_client.embeddings.create.call_count == 1

        # Second call: cache hit - should NOT call client.embeddings.create again
        result2 = await embed_texts(["Clause 1: Confidentiality"])
        assert result2 == [[0.1, 0.2, 0.3]]
        assert mock_client.embeddings.create.call_count == 1  # Still 1!


@pytest.mark.asyncio
async def test_embed_empty_list_returns_empty():
    res = await embed_texts([])
    assert res == []
