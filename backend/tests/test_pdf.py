import pytest

from app.ai.pdf import PdfExtractionError, validate_pdf_bytes


def test_reject_non_pdf():
    with pytest.raises(PdfExtractionError):
        validate_pdf_bytes(b"hello", 10000, "resume.pdf", "application/pdf")
    with pytest.raises(PdfExtractionError):
        validate_pdf_bytes(b"%PDF-1.4 hi", 10000, "resume.exe", "application/pdf")
    with pytest.raises(PdfExtractionError):
        validate_pdf_bytes(b"", 10000, "resume.pdf", "application/pdf")
    with pytest.raises(PdfExtractionError):
        validate_pdf_bytes(b"%PDF-1.4" + b"x" * 50, 10, "resume.pdf", "application/pdf")


def test_extract_real_pdf_text():
    fitz = pytest.importorskip("fitz")
    from app.ai.pdf import extract_pdf_text

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Python FastAPI PostgreSQL resume text")
    data = doc.tobytes()
    doc.close()
    text, meta = extract_pdf_text(data)
    assert "Python" in text
    assert meta["page_count"] == 1
