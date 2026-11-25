"""Reads text out of uploaded files (TXT, MD, PDF, DOCX, CSV)."""
import io
from pathlib import Path

SUPPORTED = {".txt", ".md", ".pdf", ".docx", ".csv"}


def extract_text(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"Unsupported file type '{ext}'. Use: {', '.join(sorted(SUPPORTED))}")

    if ext in {".txt", ".md", ".csv"}:
        text = content.decode("utf-8", errors="ignore")
    elif ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    else:  # .docx
        import docx
        document = docx.Document(io.BytesIO(content))
        parts = [p.text for p in document.paragraphs if p.text.strip()]
        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        text = "\n".join(parts)

    text = text.strip()
    if not text:
        raise ValueError("No readable text found (a scanned PDF needs OCR first).")
    return text
