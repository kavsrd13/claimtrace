"""
Text extraction service.
Supports: PDF (pdfplumber), DOCX (python-docx), TXT.
Returns a list of Chunk objects with text and page/paragraph metadata.
"""

import io
from dataclasses import dataclass

import pdfplumber
from docx import Document as DocxDocument


@dataclass
class Chunk:
    text: str
    page: int  # 1-indexed; 0 = unknown
    paragraph: int  # 1-indexed within page/section; 0 = unknown
    source_label: str  # human-readable reference e.g. "p.3 ¶2"


ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/octet-stream",  # some browsers send this for txt
}

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}


class ExtractionError(Exception):
    pass


def extract_text(content: bytes, filename: str, content_type: str) -> list[Chunk]:
    """
    Extract text from a file and return a list of Chunk objects.
    Raises ExtractionError on failure or unsupported type.
    """
    ext = _get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ExtractionError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if ext == ".pdf":
        return _extract_pdf(content)
    if ext in (".docx",):
        return _extract_docx(content)
    if ext == ".txt":
        return _extract_txt(content)

    raise ExtractionError(f"Cannot extract text from '{filename}'")


def chunks_to_full_text(chunks: list[Chunk]) -> str:
    return "\n\n".join(c.text for c in chunks)


def _get_extension(filename: str) -> str:
    from pathlib import Path

    return Path(filename).suffix.lower()


def _extract_pdf(content: bytes) -> list[Chunk]:
    chunks: list[Chunk] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if "\n\n" in text:
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            else:
                raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
                paragraphs = []
                current_para: list[str] = []
                for line in raw_lines:
                    if current_para and (
                        (line[0].isdigit() and "." in line[:5])
                        or (line.isupper() and len(line) < 50)
                    ):
                        paragraphs.append(" ".join(current_para))
                        current_para = [line]
                    else:
                        current_para.append(line)
                if current_para:
                    paragraphs.append(" ".join(current_para))

            for para_num, para in enumerate(paragraphs, start=1):
                chunks.append(
                    Chunk(
                        text=para,
                        page=page_num,
                        paragraph=para_num,
                        source_label=f"p.{page_num} ¶{para_num}",
                    )
                )
    if not chunks:
        raise ExtractionError("PDF appears to be empty or unreadable.")
    return chunks


def _extract_docx(content: bytes) -> list[Chunk]:
    doc = DocxDocument(io.BytesIO(content))
    chunks: list[Chunk] = []
    for para_num, para in enumerate(doc.paragraphs, start=1):
        text = para.text.strip()
        if not text:
            continue
        chunks.append(
            Chunk(
                text=text,
                page=0,
                paragraph=para_num,
                source_label=f"¶{para_num}",
            )
        )
    if not chunks:
        raise ExtractionError("DOCX appears to be empty.")
    return chunks


def _extract_txt(content: bytes) -> list[Chunk]:
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception as exc:
        raise ExtractionError(f"Cannot decode text file: {exc}") from exc

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        raise ExtractionError("Text file appears to be empty.")

    return [
        Chunk(
            text=para,
            page=0,
            paragraph=i + 1,
            source_label=f"¶{i + 1}",
        )
        for i, para in enumerate(paragraphs)
    ]
