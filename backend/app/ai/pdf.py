from __future__ import annotations

PDF_MAGIC = b"%PDF-"


class PdfExtractionError(Exception):
    pass


def validate_pdf_bytes(data: bytes, max_bytes: int, filename: str, content_type: str) -> None:
    if not filename.lower().endswith(".pdf"):
        raise PdfExtractionError("Only PDF files are accepted")
    allowed_types = {"application/pdf", "application/x-pdf", "binary/octet-stream"}
    if content_type and content_type.split(";")[0].strip().lower() not in allowed_types:
        raise PdfExtractionError("Invalid content type for PDF upload")
    if not data:
        raise PdfExtractionError("Uploaded file is empty")
    if len(data) > max_bytes:
        raise PdfExtractionError(f"File exceeds the {max_bytes} byte limit")
    if not data.startswith(PDF_MAGIC):
        raise PdfExtractionError("File does not have a valid PDF signature")


def extract_pdf_text(data: bytes) -> tuple[str, dict]:
    try:
        import fitz
    except ImportError as exc:
        raise PdfExtractionError("PyMuPDF is not installed") from exc
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise PdfExtractionError("PDF could not be opened; the file may be corrupt") from exc
    try:
        pages = []
        for page in doc:
            pages.append(page.get_text("text") or "")
        text = "\n".join(pages).strip()
        meta = {
            "page_count": doc.page_count,
            "is_encrypted": bool(doc.is_encrypted),
            "metadata": dict(doc.metadata or {}),
        }
        return text, meta
    finally:
        doc.close()
