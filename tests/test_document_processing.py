import io

import pytest

from rag.document_parser import extract_text


def test_txt():
    assert "Net 45" in extract_text("a.txt", b"Payment: Net 45 days")


def test_docx_paragraphs_and_tables():
    docx = pytest.importorskip("docx")
    d = docx.Document()
    d.add_paragraph("Governing law: India")
    t = d.add_table(rows=1, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text = "Notice", "30 days"
    buf = io.BytesIO()
    d.save(buf)
    text = extract_text("contract.docx", buf.getvalue())
    assert "Governing law: India" in text and "30 days" in text


def test_pdf():
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, "Arbitration in Mumbai")
    c.save()
    assert "Arbitration in Mumbai" in extract_text("nda.pdf", buf.getvalue())


def test_unsupported_type_rejected():
    with pytest.raises(ValueError):
        extract_text("photo.png", b"\x89PNG")


def test_empty_file_rejected():
    with pytest.raises(ValueError):
        extract_text("empty.txt", b"   ")
