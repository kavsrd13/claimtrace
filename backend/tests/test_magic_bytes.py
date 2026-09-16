"""
Tests for magic byte inspection and filename sanitization in ClaimTrace security module.
"""

import pytest

from services.security import (
    SecurityError,
    sanitize_filename,
    validate_file_bytes,
)


def test_valid_pdf_magic_bytes():
    pdf_content = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj"
    validate_file_bytes(pdf_content, "contract.pdf")  # Should not raise


def test_spoofed_pdf_raises():
    spoofed_content = b"This is plain text disguised as a PDF file"
    with pytest.raises(SecurityError) as exc_info:
        validate_file_bytes(spoofed_content, "contract.pdf")
    assert exc_info.value.code == "INVALID_FILE_HEADER"


def test_valid_docx_magic_bytes():
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
    docx_content = buf.getvalue()
    validate_file_bytes(docx_content, "agreement.docx")  # Should not raise


def test_spoofed_docx_raises():
    fake_docx = b"%PDF-1.4 Fake header inside docx"
    with pytest.raises(SecurityError) as exc_info:
        validate_file_bytes(fake_docx, "agreement.docx")
    assert exc_info.value.code == "INVALID_FILE_HEADER"


def test_valid_txt_file():
    txt_content = b"Master Services Agreement between Company A and Company B."
    validate_file_bytes(txt_content, "notes.txt")  # Should not raise


def test_disguised_executable_as_txt_raises():
    pe_header = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00" + b"\x00" * 50
    with pytest.raises(SecurityError) as exc_info:
        validate_file_bytes(pe_header, "malware.txt")
    assert exc_info.value.code == "FORBIDDEN_FILE_CONTENT"


def test_disguised_elf_as_txt_raises():
    elf_header = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 50
    with pytest.raises(SecurityError) as exc_info:
        validate_file_bytes(elf_header, "payload.txt")
    assert exc_info.value.code == "FORBIDDEN_FILE_CONTENT"


def test_null_bytes_in_txt_raises():
    null_corrupted = b"Normal header line\n\x00\x00\x00binaryblob"
    with pytest.raises(SecurityError) as exc_info:
        validate_file_bytes(null_corrupted, "corrupt.txt")
    assert exc_info.value.code == "FORBIDDEN_FILE_CONTENT"


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("contract:draft*1?2.pdf") == "contract_draft_1_2.pdf"
    assert sanitize_filename("   simple_name.txt   ") == "simple_name.txt"
    assert sanitize_filename("") == "unnamed_document"
