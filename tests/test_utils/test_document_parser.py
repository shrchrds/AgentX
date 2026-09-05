"""Unit tests for document parser utility."""

import io

import docx
import pytest

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    from PyPDF2 import PdfReader, PdfWriter

from app.utils.document_parser import (
    DocumentParsingError,
    extract_document_text,
    parse_docx,
    parse_pdf,
    parse_plaintext,
)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Provide a minimal valid PDF with extractable text."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
        b"/Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj\n"
        b"4 0 obj <</Length 55>> stream\n"
        b"BT /F1 18 Tf 50 100 Td (Confidential Settlement Agreement) Tj ET\n"
        b"endstream\n"
        b"endobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000060 00000 n \n"
        b"0000000117 00000 n \n"
        b"0000000227 00000 n \n"
        b"0000000332 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\n"
        b"startxref\n"
        b"408\n"
        b"%%EOF\n"
    )


@pytest.fixture
def sample_docx_bytes() -> bytes:
    """Provide a minimal valid DOCX document with text and table."""
    doc = docx.Document()
    doc.add_paragraph("This Non-Disclosure Agreement governs confidential information.")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Term"
    table.rows[0].cells[1].text = "2 Years"
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestPDFParser:
    """Tests for PDF text parsing."""

    def test_parse_valid_pdf(self, sample_pdf_bytes: bytes) -> None:
        text, meta = parse_pdf(sample_pdf_bytes)
        assert "Confidential Settlement Agreement" in text
        assert meta["page_count"] == 1

    def test_parse_empty_pdf_raises_error(self) -> None:
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        buf = io.BytesIO()
        writer.write(buf)
        with pytest.raises(DocumentParsingError, match="No readable text found"):
            parse_pdf(buf.getvalue())

    def test_parse_corrupted_pdf_raises_error(self) -> None:
        with pytest.raises(DocumentParsingError):
            parse_pdf(b"not a real pdf content")

    def test_parse_password_protected_pdf_raises_error(self, sample_pdf_bytes: bytes) -> None:
        reader = PdfReader(io.BytesIO(sample_pdf_bytes))
        writer = PdfWriter()
        writer.append(reader)
        writer.encrypt("secret123")
        buf = io.BytesIO()
        writer.write(buf)
        with pytest.raises(DocumentParsingError, match="password-protected"):
            parse_pdf(buf.getvalue())

    def test_parse_encrypted_empty_password_pdf(self, sample_pdf_bytes: bytes) -> None:
        reader = PdfReader(io.BytesIO(sample_pdf_bytes))
        writer = PdfWriter()
        writer.append(reader)
        # Encrypt with empty user password and non-empty owner password (standard PDF permissions)
        writer.encrypt(user_password="", owner_password="ownerpassword")
        buf = io.BytesIO()
        writer.write(buf)
        text, meta = parse_pdf(buf.getvalue())
        assert "Confidential Settlement Agreement" in text
        assert meta["page_count"] == 1


class TestDocxParser:
    """Tests for Word (.docx) text parsing."""

    def test_parse_valid_docx(self, sample_docx_bytes: bytes) -> None:
        text, meta = parse_docx(sample_docx_bytes)
        assert "This Non-Disclosure Agreement" in text
        assert "Term | 2 Years" in text
        assert meta["paragraph_count"] >= 1
        assert meta["table_count"] == 1

    def test_parse_empty_docx_raises_error(self) -> None:
        doc = docx.Document()
        buf = io.BytesIO()
        doc.save(buf)
        with pytest.raises(DocumentParsingError, match="no readable text"):
            parse_docx(buf.getvalue())

    def test_parse_corrupted_docx_raises_error(self) -> None:
        with pytest.raises(DocumentParsingError):
            parse_docx(b"corrupted bytes for word document")


class TestPlaintextParser:
    """Tests for text and markdown parsing."""

    def test_parse_utf8_text(self) -> None:
        content = "Governing Law: This agreement is governed by the laws of California."
        text, meta = parse_plaintext(content.encode("utf-8"))
        assert text == content
        assert meta["encoding"] == "utf-8"

    def test_parse_latin1_text(self) -> None:
        content = "Liquidated damages clause with special symbol: £500,000 penalty."
        text, meta = parse_plaintext(content.encode("latin-1"))
        assert "£500,000" in text

    def test_parse_empty_text_raises_error(self) -> None:
        with pytest.raises(DocumentParsingError, match="empty"):
            parse_plaintext(b"")


class TestExtractDocumentText:
    """Tests for high-level extract_document_text dispatcher."""

    def test_extract_pdf(self, sample_pdf_bytes: bytes) -> None:
        result = extract_document_text("contract.pdf", sample_pdf_bytes)
        assert result.filename == "contract.pdf"
        assert result.format == "pdf"
        assert "Confidential Settlement Agreement" in result.content
        assert result.char_count > 0
        assert not result.truncated

    def test_extract_docx(self, sample_docx_bytes: bytes) -> None:
        result = extract_document_text("nda_draft.docx", sample_docx_bytes)
        assert result.filename == "nda_draft.docx"
        assert result.format == "docx"
        assert "Non-Disclosure" in result.content
        assert not result.truncated

    def test_extract_markdown(self) -> None:
        raw = b"# Dispute Resolution\n\nAll disputes shall be arbitrated."
        result = extract_document_text("terms.md", raw)
        assert result.filename == "terms.md"
        assert result.format == "markdown"
        assert "Dispute Resolution" in result.content

    def test_unsupported_format_raises_error(self) -> None:
        with pytest.raises(DocumentParsingError, match="Unsupported file format"):
            extract_document_text("contract.exe", b"binary content")

    def test_oversized_file_raises_error(self) -> None:
        large_bytes = b"0" * (11 * 1024 * 1024)
        with pytest.raises(DocumentParsingError, match="exceeds maximum allowed limit"):
            extract_document_text("huge.txt", large_bytes)

    def test_truncation_when_exceeds_max_chars(self) -> None:
        raw = ("A" * 600).encode("utf-8")
        result = extract_document_text("long.txt", raw, max_chars=200)
        assert result.char_count == 200
        assert result.truncated is True
