"""
Azure OpenAI LLM service wrapper.
Provides chat completions and text embeddings.
"""

import json
import logging
from dataclasses import dataclass

import numpy as np
from openai import AsyncAzureOpenAI

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class Citation:
    source_label: str  # e.g. "Doc A · p.2 ¶1"
    text: str  # the relevant chunk text
    score: float  # cosine similarity score


@dataclass
class QAResponse:
    answer: str
    citations: list[Citation]
    is_supported: bool  # False if the question cannot be answered from docs


def _get_client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of text strings using Azure OpenAI embeddings.
    Returns a list of float vectors.
    """
    client = _get_client()
    response = await client.embeddings.create(
        model=settings.azure_openai_embedding_deployment,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def answer_question(
    question: str,
    chunks: list[dict],  # [{"label": str, "text": str}]
    *,
    max_citations: int = 5,
) -> QAResponse:
    """
    Answer a question grounded in the provided document chunks.
    Returns a QAResponse with answer text and ClaimTrace citations.
    """
    # Build context
    context_parts = []
    for i, chunk in enumerate(chunks[:max_citations], start=1):
        context_parts.append(f"[{i}] ({chunk['label']})\n{chunk['text']}")
    context = "\n\n---\n\n".join(context_parts)

    system_prompt = """You are ClaimTrace, an AI assistant that answers questions \
strictly based on the provided document excerpts.

Rules:
1. Only answer using information from the provided excerpts.
2. If the question cannot be answered from the excerpts, respond with exactly:
   UNSUPPORTED: <brief explanation>
3. Cite your sources using [N] notation matching the excerpt labels.
4. Be concise and factual.
5. Never invent or extrapolate beyond the provided text."""

    user_message = f"""Document excerpts:
{context}

---

Question: {question}"""

    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        max_tokens=1024,
    )

    answer_text = response.choices[0].message.content or ""
    is_supported = not answer_text.upper().startswith("UNSUPPORTED:")

    # Map citation indices to chunks
    citations = []
    for i, chunk in enumerate(chunks[:max_citations], start=1):
        if f"[{i}]" in answer_text:
            citations.append(
                Citation(
                    source_label=chunk["label"],
                    text=chunk["text"],
                    score=chunk.get("score", 1.0),
                )
            )

    return QAResponse(answer=answer_text, citations=citations, is_supported=is_supported)


async def compare_documents(
    text_a: str,
    text_b: str,
    filename_a: str,
    filename_b: str,
) -> dict:
    """
    Use the LLM to produce a structured comparison of two documents.
    Returns a dict with keys: summary, similarities, differences, claims.
    """
    system_prompt = """You are ClaimTrace, a document analysis assistant.
Compare the two documents provided and return a JSON object with this exact schema:
{
  "summary": "<2-3 sentence overall comparison>",
  "similarities": ["<point 1>", "<point 2>", ...],
  "differences": [
    {"aspect": "<topic>", "doc_a": "<what doc A says>", "doc_b": "<what doc B says>"}
  ],
  "claims": [
    {
      "id": "<unique id like C001>",
      "claim": "<a specific claim made in one or both docs>",
      "source_a": "<supporting text from doc A or null>",
      "source_b": "<supporting text from doc B or null>",
      "verdict": "agree | disagree | only_in_a | only_in_b"
    }
  ]
}
Return ONLY the JSON object, no markdown."""

    user_message = f"""Document A ({filename_a}):
{text_a[:6000]}

===

Document B ({filename_b}):
{text_b[:6000]}"""

    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON for comparison; returning raw.")
        return {"summary": raw, "similarities": [], "differences": [], "claims": []}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))
