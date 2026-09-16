"""
Tests for vectorized cosine similarity and retrieval mathematics in services.comparator.
"""

import pytest

from services.comparator import retrieve_top_k
from services.extractor import Chunk


def _make_chunk(text: str, label: str = "p.1 ¶1") -> Chunk:
    return Chunk(text=text, page=1, paragraph=1, source_label=label)


def test_retrieve_top_k_identical_vectors():
    query_vec = [1.0, 0.0, 0.0]
    doc_embs = [[1.0, 0.0, 0.0], [0.5, 0.5, 0.0]]
    chunks = [_make_chunk("Identical match"), _make_chunk("Partial match")]

    results = retrieve_top_k(query_vec, doc_embs, chunks, "Doc A", k=2)
    assert len(results) == 2
    assert results[0]["text"] == "Identical match"
    assert pytest.approx(results[0]["score"], rel=1e-3) == 1.0


def test_retrieve_top_k_orthogonal_vectors():
    query_vec = [1.0, 0.0, 0.0]
    doc_embs = [[0.0, 1.0, 0.0]]
    chunks = [_make_chunk("Orthogonal clause")]

    results = retrieve_top_k(query_vec, doc_embs, chunks, "Doc A", k=1)
    assert len(results) == 1
    assert pytest.approx(results[0]["score"], abs=1e-5) == 0.0


def test_retrieve_top_k_zero_query_vector_returns_empty():
    query_vec = [0.0, 0.0, 0.0]
    doc_embs = [[1.0, 0.0, 0.0]]
    chunks = [_make_chunk("Some clause")]

    results = retrieve_top_k(query_vec, doc_embs, chunks, "Doc A", k=1)
    assert results == []


def test_retrieve_top_k_empty_chunks_returns_empty():
    query_vec = [1.0, 2.0, 3.0]
    assert retrieve_top_k(query_vec, [], [], "Doc A") == []


def test_retrieve_top_k_limits_to_k():
    query_vec = [1.0, 1.0]
    doc_embs = [[1.0, 0.9], [0.9, 1.0], [0.5, 0.5], [0.1, 0.1]]
    chunks = [_make_chunk(f"Clause {i}") for i in range(4)]

    results = retrieve_top_k(query_vec, doc_embs, chunks, "Doc A", k=2)
    assert len(results) == 2
