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
        extra_body={"max_completion_tokens": 4096, "reasoning_effort": "low"},
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
    system_prompt = """You are ClaimTrace, a legal document analysis assistant.
Compare Document A and Document B. You must return a valid JSON object strictly matching this schema:
{
  "summary": "Concise 2-3 sentence overview of differences",
  "similarities": ["bullet 1", "bullet 2"],
  "differences": [
    {
      "aspect": "Clause or topic name, e.g. Uptime SLA",
      "doc_a": "What Document A specifies",
      "doc_b": "What Document B specifies"
    }
  ],
  "claims": [
    {
      "id": "C001",
      "claim": "Specific statement or obligation",
      "source_a": "Excerpt from Doc A or null",
      "source_b": "Excerpt from Doc B or null",
      "verdict": "agree | disagree | only_in_a | only_in_b"
    }
  ]
}

CRITICAL FORMATTING RULES:
1. 'differences' MUST be an array of JSON objects with keys 'aspect', 'doc_a', and 'doc_b'. NEVER return strings in 'differences'.
2. 'claims' MUST be an array of JSON objects with keys 'id', 'claim', 'source_a', 'source_b', and 'verdict'. NEVER return strings in 'claims'.
3. 'verdict' must be one of: 'agree', 'disagree', 'only_in_a', 'only_in_b'.
4. Identify all distinct differences between the documents (e.g. SLA targets, fees, payment terms, liability caps, notice periods, breach response windows, governing law).
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
        response_format={"type": "json_object"},
        extra_body={"max_completion_tokens": 8192, "reasoning_effort": "low"},
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
