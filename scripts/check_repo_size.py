#!/usr/bin/env python3
"""
check_repo_size.py – Repository hygiene checker for ClaimTrace.

Checks:
  1. Total size of tracked Git files (fails above 9 MB).
  2. Lists the 20 largest tracked files.
  3. Scans tracked text files for common secret patterns.
  4. Verifies forbidden paths are not tracked.

Usage:
    python scripts/check_repo_size.py
"""

import re
import subprocess
import sys
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 9 * 1024 * 1024  # 9 MB

FORBIDDEN_PATTERNS = [
    "uploads/",
    ".venv/",
    "venv/",
    "node_modules/",
    "__pycache__/",
    "coverage/",
    "htmlcov/",
    "playwright-report/",
    "test-results/",
    "backend/static/assets/",
    ".env",
]

FORBIDDEN_EXTENSIONS = {
    ".db", ".sqlite", ".sqlite3",   # local databases
    ".exe", ".dll", ".so", ".dylib",  # binaries
    ".pdf", ".docx", ".doc",          # document fixtures
    ".png", ".jpg", ".jpeg", ".gif",  # screenshots
    ".mp4", ".webm", ".avi",          # recordings
    ".tar", ".gz", ".zip",            # archives
    ".pt", ".pth", ".bin", ".pkl", ".onnx", ".safetensors",  # models
}

SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AWS Access Key",      re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret",          re.compile(r"(?i)aws[_\-\s]?secret[_\-\s]?access[_\-\s]?key\s*=\s*\S+")),
    ("Generic API key",     re.compile(r"(?i)api[_\-]?key\s*=\s*['\"]?[A-Za-z0-9_\-]{20,}")),
    ("Bearer token",        re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*")),
    ("Private key header",  re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) PRIVATE KEY-----")),
    ("Password literal",    re.compile(r"(?i)password\s*=\s*['\"][^'\"]{6,}['\"]")),
    ("Azure OpenAI key",    re.compile(r"(?i)azure[_\-]openai[_\-]api[_\-]key\s*=\s*[A-Za-z0-9]{20,}")),
    ("Generic secret",      re.compile(r"(?i)secret[_\-]?key\s*=\s*['\"]?[A-Za-z0-9_\-]{16,}")),
    ("GitHub token",        re.compile(r"gh[ps]_[A-Za-z0-9]{36}")),
    ("Slack token",         re.compile(r"xox[baprs]-[0-9A-Za-z\-]+")),
    ("Stripe key",          re.compile(r"sk_live_[0-9a-zA-Z]{24}")),
    ("JWT",                 re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
]

# Extensions we treat as binary (skip secret scanning)
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".webm", ".pdf", ".docx", ".doc",
    ".xlsx", ".zip", ".tar", ".gz", ".bin", ".pkl", ".pt",
    ".pth", ".onnx", ".safetensors", ".exe", ".dll", ".so",
    ".db", ".sqlite", ".sqlite3",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
RED    = "\033[31m"
YELLOW = "\033[33m"
GREEN  = "\033[32m"
BOLD   = "\033[1m"
CYAN   = "\033[36m"


def run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=REPO_ROOT, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0 and result.stderr:
        # Non-fatal – git may return non-zero in some edge cases
        pass
    return result.stdout


def get_tracked_files() -> list[Path]:
    """Return absolute paths of all files tracked by git."""
    raw = run(["git", "ls-files"])
    return [REPO_ROOT / f.strip() for f in raw.splitlines() if f.strip()]


def sizeof_fmt(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num) < 1024.0:
            return f"{num:,.1f} {unit}"
        num /= 1024.0
    return f"{num:,.1f} TB"


# ── Checks ────────────────────────────────────────────────────────────────────

def check_repo_size(files: list[Path]) -> tuple[int, list[tuple[int, Path]]]:
    """Return (total_bytes, sorted list of (size, path))."""
    file_sizes: list[tuple[int, Path]] = []
    for f in files:
        if f.exists():
            size = f.stat().st_size
            file_sizes.append((size, f))
    file_sizes.sort(reverse=True)
    total = sum(s for s, _ in file_sizes)
    return total, file_sizes


def check_forbidden_paths(files: list[Path]) -> list[str]:
    """Return list of violation messages for forbidden paths."""
    violations: list[str] = []
    for f in files:
        rel = f.relative_to(REPO_ROOT).as_posix()
        # Check forbidden path prefixes
        for pat in FORBIDDEN_PATTERNS:
            if pat == ".env":
                if (rel == ".env" or rel.startswith(".env.")) and rel != ".env.example":
                    violations.append(f"Forbidden file tracked: {rel}  (matches '{pat}')")
                    break
            elif pat.endswith("/"):
                if rel.startswith(pat) or f"/{pat}" in f"/{rel}":
                    violations.append(f"Forbidden path tracked: {rel}  (matches '{pat}')")
                    break
            else:
                # exact filename / glob-like
                if rel == pat or rel.startswith(pat):
                    violations.append(f"Forbidden file tracked: {rel}  (matches '{pat}')")
                    break
        # Check forbidden extensions
        ext = Path(rel).suffix.lower()
        if ext in FORBIDDEN_EXTENSIONS:
            violations.append(f"Forbidden extension tracked: {rel}  (ext: {ext})")
    return violations


def check_secrets(files: list[Path]) -> list[str]:
    """Scan text files for common secret patterns. Return list of findings."""
    findings: list[str] = []
    for f in files:
        if not f.exists():
            continue
        ext = f.suffix.lower()
        if ext in BINARY_EXTENSIONS:
            continue
        # Skip .env.example and check_repo_size.py itself (contains scanner regex definitions)
        rel = f.relative_to(REPO_ROOT).as_posix()
        if rel in (".env.example", "scripts/check_repo_size.py"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                # Calculate line number
                lineno = text[: match.start()].count("\n") + 1
                findings.append(
                    f"{rel}:{lineno}  [{name}]  →  {match.group()[:60]!r}"
                )
    return findings


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(f"\n{BOLD}{CYAN}== ClaimTrace Repository Checker =={RESET}\n")

    # Verify we're inside a git repo
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print(f"{RED}✗ Not inside a git repository.{RESET}")
        return 1

    files = get_tracked_files()
    if not files:
        print(f"{YELLOW}⚠ No tracked files found. Did you run 'git add'?{RESET}")
        return 0

    print(f"Tracked files: {len(files)}\n")

    # ── 1. Repo size ────────────────────────────────────────────────────────
    print(f"{BOLD}[1/4] Repository size{RESET}")
    total_bytes, file_sizes = check_repo_size(files)
    print(f"  Total tracked size: {sizeof_fmt(total_bytes)}")

    size_ok = total_bytes <= MAX_BYTES
    if size_ok:
        print(f"  {GREEN}✓ Under {sizeof_fmt(MAX_BYTES)} limit.{RESET}")
    else:
        print(
            f"  {RED}✗ EXCEEDS limit! {sizeof_fmt(total_bytes)} > {sizeof_fmt(MAX_BYTES)}.{RESET}"
        )

    print(f"\n  Top 20 largest tracked files:")
    for i, (size, path) in enumerate(file_sizes[:20], 1):
        rel = path.relative_to(REPO_ROOT).as_posix()
        color = RED if size > 1 * 1024 * 1024 else YELLOW if size > 100 * 1024 else RESET
        print(f"  {i:>3}. {color}{sizeof_fmt(size):>10}{RESET}  {rel}")

    # ── 2. Forbidden paths ──────────────────────────────────────────────────
    print(f"\n{BOLD}[2/4] Forbidden paths{RESET}")
    violations = check_forbidden_paths(files)
    if violations:
        for v in violations:
            print(f"  {RED}✗ {v}{RESET}")
        paths_ok = False
    else:
        print(f"  {GREEN}✓ No forbidden paths tracked.{RESET}")
        paths_ok = True

    # ── 3. Secret scan ──────────────────────────────────────────────────────
    print(f"\n{BOLD}[3/4] Secret scan{RESET}")
    findings = check_secrets(files)
    if findings:
        for f in findings:
            print(f"  {RED}✗ {f}{RESET}")
        secrets_ok = False
    else:
        print(f"  {GREEN}✓ No secrets detected.{RESET}")
        secrets_ok = True

    # ── 4. Summary ──────────────────────────────────────────────────────────
    print(f"\n{BOLD}[4/4] Summary{RESET}")
    all_ok = size_ok and paths_ok and secrets_ok
    checks = [
        ("Repo size", size_ok),
        ("Forbidden paths", paths_ok),
        ("Secret scan", secrets_ok),
    ]
    for name, ok in checks:
        status = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {name:<22} {status}")

    print()
    if all_ok:
        print(f"{GREEN}{BOLD}✓ All checks passed.{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}✗ One or more checks failed. Fix the issues above before committing.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
