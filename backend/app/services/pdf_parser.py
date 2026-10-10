"""PDF resume text extraction via PyMuPDF."""

from __future__ import annotations

import re
from io import BytesIO

import fitz  # PyMuPDF


class PDFParseError(ValueError):
    pass


def extract_text_from_pdf(data: bytes) -> str:
    """Extract plain text from a PDF byte payload."""
    if not data:
        raise PDFParseError("Empty PDF upload.")
    try:
        doc = fitz.open(stream=BytesIO(data), filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise PDFParseError(f"Unable to open PDF: {exc}") from exc

    if doc.page_count == 0:
        doc.close()
        raise PDFParseError("PDF has no pages.")

    chunks: list[str] = []
    for page in doc:
        chunks.append(page.get_text("text") or "")
    doc.close()

    text = "\n".join(chunks)
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text.strip()) < 40:
        raise PDFParseError(
            "Could not extract enough text. Ensure the PDF is text-based (not a scanned image)."
        )
    return text.strip()
