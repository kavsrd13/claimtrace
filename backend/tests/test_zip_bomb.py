"""
Tests for DOCX zip-bomb defense and archive safety checks.
"""

import io
import zipfile

import pytest

from services.security import SecurityError, check_docx_zip_bomb, validate_file_bytes


def _create_fake_docx(file_contents: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, data in file_contents.items():
            zf.writestr(filename, data)
    return buf.getvalue()


def test_valid_small_docx_passes():
    docx_bytes = _create_fake_docx({
        "word/document.xml": b"<w:document><w:body><w:p><w:t>Agreement</w:t></w:p></w:body></w:document>",
        "[Content_Types].xml": b"<Types></Types>",
    })
    check_docx_zip_bomb(docx_bytes)  # Should not raise
    validate_file_bytes(docx_bytes, "agreement.docx")  # Should not raise


def test_corrupt_docx_archive_raises():
    bad_bytes = b"PK\x03\x04corrupted_header_data_not_a_valid_zip"
    with pytest.raises(SecurityError) as exc_info:
        check_docx_zip_bomb(bad_bytes)
    assert exc_info.value.code == "INVALID_FILE_HEADER"


def test_docx_exceeding_uncompressed_limit_raises():
    # Simulate a zip bomb where uncompressed exceeds limit
    docx_bytes = _create_fake_docx({
        "word/huge_file.xml": b"0" * 2000,
    })
    # Set limit very low (1000 bytes) to test threshold enforcement
    with pytest.raises(SecurityError) as exc_info:
        check_docx_zip_bomb(docx_bytes, max_uncompressed_bytes=1000)
    assert exc_info.value.code == "ZIP_BOMB_DETECTED"
