"""
Security service: prompt injection detection, file validation, session TTL.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

from services.extractor import ALLOWED_EXTENSIONS

# ── Prompt injection heuristics ────────────────────────────────────────────────

INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"ignore\s+(?:all\s+|previous\s+|above\s+|prior\s+)*(?:instructions?|context|rules?|prompts?)",
        re.I,
    ),
    re.compile(r"you are now", re.I),
    re.compile(r"forget (everything|all|your instructions)", re.I),
    re.compile(r"act as (a |an |if )?(jailbreak|dan|evil|unrestricted)", re.I),
    re.compile(r"do anything now", re.I),
    re.compile(r"disregard (your|all) (instructions?|guidelines?|safety)", re.I),
    re.compile(r"new system prompt", re.I),
    re.compile(r"override (system|safety|instructions?)", re.I),
    re.compile(r"<\|?system\|?>", re.I),
    re.compile(r"\[INST\]|\[/INST\]", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"repeat (the|your) (system|instructions?|prompt)", re.I),
    re.compile(r"reveal (your|the) (system|instructions?|prompt)", re.I),
    re.compile(r"print (the|your) (system|instructions?|prompt)", re.I),
]

# ── Forbidden file types ────────────────────────────────────────────────────────

FORBIDDEN_EXTENSIONS: set[str] = {
    ".exe",
    ".bat",
    ".sh",
    ".cmd",
    ".ps1",
    ".dll",
    ".so",
    ".dylib",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".svg",
    ".mp4",
    ".webm",
    ".avi",
    ".mov",
    ".mp3",
    ".wav",
    ".ogg",
    ".pkl",
    ".pt",
    ".pth",
    ".bin",
    ".onnx",
    ".safetensors",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".xlsx",
    ".xls",
    ".pptx",
    ".ppt",
    ".csv",  # allow if desired – blocked here for safety
    ".js",
    ".ts",
    ".html",
    ".htm",
    ".py",
    ".rb",
    ".php",
    ".go",
}


class SecurityError(Exception):
    """Raised when a security check fails."""

    def __init__(self, message: str, code: str = "SECURITY_ERROR"):
        super().__init__(message)
        self.code = code


def check_prompt_injection(text: str) -> None:
    """
    Scan `text` for prompt-injection patterns.
    Raises SecurityError if injection is detected.
    """
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            raise SecurityError(
                "Your input contains content that looks like a prompt-injection attempt "
                "and cannot be processed.",
                code="PROMPT_INJECTION",
            )


def validate_upload(filename: str, content_type: str, size_bytes: int, max_bytes: int) -> None:
    """
    Validate an uploaded file.
    Raises SecurityError if the file is not allowed.
    """
    ext = Path(filename).suffix.lower()

    if ext in FORBIDDEN_EXTENSIONS:
        raise SecurityError(
            f"File type '{ext}' is not allowed. Supported types: .txt, .pdf, .docx",
            code="FORBIDDEN_FILE_TYPE",
        )

    if ext not in ALLOWED_EXTENSIONS:
        raise SecurityError(
            f"File type '{ext}' is not supported. Supported types: .txt, .pdf, .docx",
            code="UNSUPPORTED_FILE_TYPE",
        )

    if size_bytes > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        raise SecurityError(
            f"File size {actual_mb:.1f} MB exceeds the {max_mb:.0f} MB limit.",
            code="FILE_TOO_LARGE",
        )


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def check_session_active(expires_at: datetime, deleted_at: datetime | None) -> None:
    """
    Verify a session is still active.
    Raises SecurityError if expired or deleted.
    """
    if deleted_at is not None:
        raise SecurityError("Session has been deleted.", code="SESSION_DELETED")
    if datetime.now(UTC) > _as_utc(expires_at):
        raise SecurityError("Session has expired.", code="SESSION_EXPIRED")
