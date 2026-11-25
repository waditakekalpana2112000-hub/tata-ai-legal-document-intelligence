"""Build a downloadable Word (.docx) contract report from the AI's markdown answers."""
import io
import re
from datetime import date

INLINE = re.compile(r"(\*\*[^*]+\*\*)")


def _add_runs(paragraph, text: str) -> None:
    for part in INLINE.split(text):
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            paragraph.add_run(part[2:-2]).bold = True
        elif part:
            paragraph.add_run(part)


def _table(doc, rows: list[list[str]]) -> None:
    width = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=width)
    table.style = "Table Grid"
    for i, row in enumerate(rows):
        for j in range(width):
            cell = table.cell(i, j)
            cell.text = ""
            _add_runs(cell.paragraphs[0], (row[j] if j < len(row) else "").replace("**", "") if i else "")
            if i == 0:
                cell.paragraphs[0].add_run(row[j] if j < len(row) else "").bold = True


def add_markdown(doc, md: str) -> None:
    """Very small markdown -> docx converter: headings, bullets, numbers, tables, bold."""
    lines = (md or "").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            if rows:
                _table(doc, rows)
            continue
        stripped = line.strip()
        if not stripped:
            pass
        elif m := re.match(r"(#{1,4})\s+(.*)", stripped):
            doc.add_heading(m.group(2).replace("**", ""), level=min(len(m.group(1)) + 1, 4))
        elif m := re.match(r"[-*•]\s+(.*)", stripped):
            _add_runs(doc.add_paragraph(style="List Bullet"), m.group(1))
        elif m := re.match(r"\d+[.)]\s+(.*)", stripped):
            _add_runs(doc.add_paragraph(style="List Number"), m.group(1))
        else:
            _add_runs(doc.add_paragraph(), stripped)
        i += 1


def build_report(contract: str, sections: dict[str, str], risk: dict | None = None) -> bytes:
    """sections: {"Summary": md, "Risks": md, ...}; risk: the risk-score JSON (optional)."""
    import docx

    doc = docx.Document()
    doc.add_heading("Contract Review Report", level=0)
    doc.add_paragraph(f"Document: {contract}")
    doc.add_paragraph(f"Generated: {date.today().isoformat()} by Tata AI Legal Document Intelligence System")
    if risk:
        doc.add_heading("Risk score", level=1)
        p = doc.add_paragraph()
        p.add_run(f"{risk.get('overall_score', '?')}/100 ({risk.get('level', '?')} risk)").bold = True
        if risk.get("summary"):
            doc.add_paragraph(risk["summary"])
        items = risk.get("risks") or []
        if items:
            _table(doc, [["Risk", "Severity", "Why it matters", "Suggested fix", "Source"]] + [
                [r.get("title", ""), r.get("severity", ""), r.get("why", ""), r.get("fix", ""), r.get("source", "")]
                for r in items
            ])
    for title, md in sections.items():
        doc.add_heading(title, level=1)
        add_markdown(doc, md)
    doc.add_paragraph("")
    doc.add_paragraph().add_run("AI-generated review. Verify with a qualified lawyer before acting on it.").italic = True
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
