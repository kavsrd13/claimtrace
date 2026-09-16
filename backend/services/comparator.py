"""
Document comparator service.
Orchestrates extraction, embedding, and LLM comparison.
"""

import json
import logging

import numpy as np

from services.extractor import Chunk, chunks_to_full_text
from services.llm import compare_documents, embed_texts

logger = logging.getLogger(__name__)

TOP_K = 8  # chunks retrieved per question


async def build_embeddings(chunks: list[Chunk]) -> tuple[list[list[float]], list[Chunk]]:
    """
    Compute embeddings for a list of chunks.
    Returns (embeddings, chunks) – filtered to non-empty chunks.
    """
    texts = [c.text for c in chunks if c.text.strip()]
    valid_chunks = [c for c in chunks if c.text.strip()]
    if not texts:
        return [], []
    embeddings = await embed_texts(texts)
    return embeddings, valid_chunks


def serialize_embeddings(embeddings: list[list[float]]) -> str:
    """Serialise embeddings to a compact JSON string for storage."""
    return json.dumps(embeddings)


def deserialize_embeddings(data: str) -> list[list[float]]:
    """Deserialise embeddings from storage."""
    return json.loads(data)


def retrieve_top_k(
    query_embedding: list[float],
    doc_embeddings: list[list[float]],
    doc_chunks: list[Chunk],
    doc_label_prefix: str,
    k: int = TOP_K,
) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for a query using vectorized NumPy operations.
    Returns a list of {label, text, score} dicts.
    """
    if not doc_embeddings or not doc_chunks:
        return []

    matrix = np.array(doc_embeddings, dtype=np.float32)
    query = np.array(query_embedding, dtype=np.float32)
    q_norm = float(np.linalg.norm(query))
    if q_norm == 0:
        return []

    m_norms = np.linalg.norm(matrix, axis=1)
    denom = m_norms * q_norm
    denom[denom == 0] = 1.0
    scores = np.dot(matrix, query) / denom
    scores = np.nan_to_num(scores, nan=0.0)

    top_indices = np.argsort(scores)[::-1][:k]

    return [
        {
            "label": f"{doc_label_prefix} · {doc_chunks[idx].source_label}",
            "text": doc_chunks[idx].text,
            "score": float(scores[idx]),
        }
        for idx in top_indices
        if idx < len(doc_chunks)
    ]


async def compare_two_documents(
    chunks_a: list[Chunk],
    chunks_b: list[Chunk],
    filename_a: str,
    filename_b: str,
) -> dict:
    """
    Full comparison pipeline: extract full text and ask LLM to compare.
    """
    text_a = chunks_to_full_text(chunks_a)
    text_b = chunks_to_full_text(chunks_b)
    result = await compare_documents(text_a, text_b, filename_a, filename_b)
    return result
