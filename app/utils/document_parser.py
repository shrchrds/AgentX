"""Document parser utility for extracting text from common legal document formats.

Supports:
- PDF (.pdf) via PyPDF2
- Microsoft Word (.docx) via python-docx
- Plain text / Markdown (.txt, .md) with multiple encoding fallbacks
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path

try:
    import docx
except ImportError:  # pragma: no cover
    docx = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

# Maximum allowed file size for document uploads (10 MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
# Maximum characters allowed per task in AgentX
MAX_EXTRACTED_CHARS = 50_000

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class DocumentParsingError(Exception):
    """Raised when document parsing fails due to invalid format, corruption, or encryption."""


@dataclass
class ExtractedDocument:
    """Represents the parsed text and metadata of an uploaded document."""

    filename: str
    content: str
    char_count: int
    format: str
    truncated: bool = False
    metadata: dict = field(default_factory=dict)


def parse_pdf(file_bytes: bytes) -> tuple[str, dict]:
    """Extract text from PDF file bytes.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        tuple of (extracted_text, metadata_dict).

    Raises:
        DocumentParsingError: If PDF is encrypted, corrupted, or unreadable.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            try:
                # Attempt empty password decryption (standard PDF permissions allow reading)
                reader.decrypt("")
            except Exception as err:
                raise DocumentParsingError(
                    "The PDF document is password-protected and cannot be processed."
                ) from err

        pages_text: list[str] = []
        try:
            total_pages = len(reader.pages)
        except Exception as err:
            raise DocumentParsingError(
                "The PDF document is password-protected or unreadable."
            ) from err

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
            except Exception as page_err:
                logger.warning("Failed to extract text from page %d: %s", page_num, page_err)
                continue
            if page_text:
                pages_text.append(page_text.strip())

        full_text = "\n\n".join(pages_text).strip()
        if not full_text:
            raise DocumentParsingError(
                "No readable text found in PDF. Scanned image PDFs require OCR before processing."
            )

        return full_text, {"page_count": total_pages}
    except DocumentParsingError:
        raise
    except Exception as exc:
        err_msg = str(exc)
        if "PyCryptodome is required" in err_msg or "cryptography" in err_msg.lower():
            logger.error("Missing cryptographic library for PDF parsing: %s", exc)
            raise DocumentParsingError(
                "Cryptographic library required for AES-encrypted PDFs is not available. "
                "Please install pycryptodome or cryptography."
            ) from exc
        logger.error("Failed to parse PDF: %s", exc)
        raise DocumentParsingError(f"Failed to parse PDF document: {exc}") from exc


def parse_docx(file_bytes: bytes) -> tuple[str, dict]:
    """Extract text from Word (.docx) file bytes.

    Args:
        file_bytes: Raw bytes of the DOCX file.

    Returns:
        tuple of (extracted_text, metadata_dict).

    Raises:
        DocumentParsingError: If DOCX is corrupted or invalid.
    """
    if docx is None:
        raise DocumentParsingError(
            "python-docx is not installed. Please install it with: pip install python-docx"
        )
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs: list[str] = []

        # Extract text from paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                paragraphs.append(text)

        # Extract text from tables if any
        table_count = len(doc.tables)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    paragraphs.append(" | ".join(row_cells))

        full_text = "\n\n".join(paragraphs).strip()
        if not full_text:
            raise DocumentParsingError("Word document contains no readable text.")

        return full_text, {
            "paragraph_count": len(doc.paragraphs),
            "table_count": table_count,
        }
    except DocumentParsingError:
        raise
    except Exception as exc:
        logger.error("Failed to parse DOCX: %s", exc)
        raise DocumentParsingError(f"Failed to parse Word (.docx) document: {exc}") from exc


def parse_plaintext(file_bytes: bytes) -> tuple[str, dict]:
    """Extract text from plain text or markdown files.

    Args:
        file_bytes: Raw bytes of the text file.

    Returns:
        tuple of (extracted_text, metadata_dict).

    Raises:
        DocumentParsingError: If file cannot be decoded.
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"]
    for enc in encodings:
        try:
            text = file_bytes.decode(enc).strip()
            if not text:
                raise DocumentParsingError("Text file is empty.")
            return text, {"encoding": enc}
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise DocumentParsingError("Unable to decode text file with supported character encodings.")


def extract_document_text(
    filename: str,
    file_bytes: bytes,
    max_chars: int = MAX_EXTRACTED_CHARS,
) -> ExtractedDocument:
    """Extract and sanitize text from an uploaded legal document.

    Args:
        filename: Name of the uploaded file (including extension).
        file_bytes: Raw binary content of the file.
        max_chars: Maximum character limit for the extracted text.

    Returns:
        ExtractedDocument containing content and metadata.

    Raises:
        DocumentParsingError: On unsupported format, excessive size, or parse error.
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise DocumentParsingError(
            f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported_str = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise DocumentParsingError(
            f"Unsupported file format '{ext}'. Supported formats: {supported_str}"
        )

    if ext == ".pdf":
        text, meta = parse_pdf(file_bytes)
        file_format = "pdf"
    elif ext == ".docx":
        text, meta = parse_docx(file_bytes)
        file_format = "docx"
    elif ext in {".txt", ".md"}:
        text, meta = parse_plaintext(file_bytes)
        file_format = "txt" if ext == ".txt" else "markdown"
    else:
        raise DocumentParsingError(f"Unsupported file extension: {ext}")

    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True
        logger.warning("Document %s truncated to %d characters.", filename, max_chars)

    return ExtractedDocument(
        filename=filename,
        content=text,
        char_count=len(text),
        format=file_format,
        truncated=truncated,
        metadata=meta,
    )
