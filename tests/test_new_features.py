import io
from datetime import date

import pytest

from evaluation.evaluate import run_evaluation, score_one
from graph import nodes
from graph.prompts import build_user_prompt, system_prompt
from utils.deadline_calendar import build_ics, schedule
from utils.emailer import reminder_body
from utils.highlight import best_sentences, highlight_html
from utils.json_utils import extract_json

POLICY = [{"text": "Payments are Net 45 days.", "source": "payment_terms.md", "score": None}]
CONTRACT = [{"text": "Vendor is paid in 90 days.", "source": "vendor.pdf", "score": None}]


# ---- 1. Policy check + 5. compare: the right documents reach the LLM ----
def test_compliance_sends_policy_and_contract(monkeypatch):
    def fake_chunks(source=None, doc_type=None, limit=40):
        return CONTRACT if source == "vendor.pdf" else POLICY if doc_type == "knowledge_base" else []
    monkeypatch.setattr(nodes.vector_store, "get_document_chunks", fake_chunks)
    docs = nodes.retrieve({"question": "", "task": "compliance", "source": "vendor.pdf"})["documents"]
    assert {d["role"] for d in docs} == {"TATA POLICY", "CONTRACT UNDER REVIEW"}
    assert "TATA POLICY" in build_user_prompt("compliance", "", docs)


def test_compliance_without_contract_finds_nothing():
    assert nodes.retrieve({"question": "", "task": "compliance"})["documents"] == []


def test_compare_labels_both_documents(monkeypatch):
    monkeypatch.setattr(nodes.vector_store, "get_document_chunks",
                        lambda source=None, doc_type=None, limit=40: [{"text": source, "source": source, "score": None}])
    docs = nodes.retrieve({"question": "", "task": "compare", "source": "a.pdf", "source_b": "b.pdf"})["documents"]
    assert [d["role"] for d in docs] == ["DOCUMENT A", "DOCUMENT B"]


# ---- 2. Chat memory ----
def test_follow_up_search_uses_previous_question(monkeypatch):
    seen = {}
    monkeypatch.setattr(nodes.vector_store, "search", lambda q, source=None: seen.setdefault("q", q) and POLICY)
    nodes.retrieve({"question": "and for audits?", "task": "chat",
                    "history": [{"role": "user", "content": "What notice is needed to terminate?"}]})
    assert "terminate" in seen["q"] and "audits" in seen["q"]


def test_history_goes_into_chat_prompt_only():
    hist = [{"role": "user", "content": "What about payments?"}]
    assert "What about payments?" in build_user_prompt("chat", "and late fees?", POLICY, hist)
    assert "What about payments?" not in build_user_prompt("summarize", "", POLICY, hist)


# ---- 10. Language ----
def test_language_rule():
    assert "Hindi" in system_prompt("Hindi")
    assert "Hindi" not in system_prompt("English")


# ---- 4/9. JSON from the LLM ----
def test_extract_json_handles_fences_and_text():
    assert extract_json('```json\n{"overall_score": 40}\n```')["overall_score"] == 40
    assert extract_json('Here you go: {"level": "Low"} thanks')["level"] == "Low"
    with pytest.raises(ValueError):
        extract_json("no json here")


# ---- 6. Highlight ----
def test_highlight_marks_supporting_sentence():
    chunk = "Invoices are sent monthly. Tata pays within 45 days of a valid invoice. Audits need notice."
    answer = "Tata pays vendors within 45 days of receiving a valid invoice [payment_terms.md]."
    assert best_sentences(chunk, answer) == ["Tata pays within 45 days of a valid invoice."]
    assert "<mark>Tata pays within 45 days" in highlight_html(chunk, answer)


def test_highlight_escapes_html():
    assert "<script>" not in highlight_html("<script>x</script> pays 45 days", "pays 45 days")


# ---- 9. Deadline schedule + calendar + email ----
def test_schedule_turns_periods_into_dates():
    rows = schedule([
        {"term": "Audit notice", "days": 15, "anchor": "start"},
        {"term": "Extension request", "days": 30, "anchor": "end"},
        {"term": "Breach report", "days": 1, "anchor": "event"},
    ], start=date(2026, 1, 1), end=date(2026, 12, 31), today=date(2026, 1, 5))
    by = {r["term"]: r for r in rows}
    assert by["Audit notice"]["due_date"] == "2026-01-16" and by["Audit notice"]["status"] == "Due within 30 days"
    assert by["Extension request"]["due_date"] == "2026-12-01"
    assert by["Breach report"]["due_date"] is None and by["Breach report"]["status"] == "Event-based"
    assert rows[-1]["term"] == "Breach report"  # undated last


def test_ics_has_one_event_per_dated_deadline():
    ics = build_ics([{"term": "Audit", "due_date": "2026-01-16", "source": "audit_rights.md"},
                     {"term": "Breach", "due_date": None}], "Vendor, Inc")
    assert ics.count("BEGIN:VEVENT") == 1 and "DTSTART;VALUE=DATE:20260116" in ics
    assert "Vendor\\, Inc" in ics and ics.endswith("END:VCALENDAR\r\n")


def test_reminder_body_lists_deadlines():
    body = reminder_body("NDA", [{"term": "Audit", "due_date": "2026-01-16", "description": "notice"}])
    assert "2026-01-16" in body and "Audit" in body


# ---- 3. Report ----
def test_report_is_a_valid_docx():
    docx = pytest.importorskip("docx")
    from utils.report import build_report
    content = build_report("vendor.pdf",
                           {"Summary": "**Purpose**: supply\n- Pay in 45 days",
                            "Deadlines": "| Term | Value |\n|---|---|\n| Audit | 15 days |"},
                           {"overall_score": 62, "level": "Medium", "summary": "Some one-sided terms.",
                            "risks": [{"title": "Termination", "severity": "High"}]})
    d = docx.Document(io.BytesIO(content))
    text = "\n".join(p.text for p in d.paragraphs)
    assert "Contract Review Report" in text and "62/100" in text and "Pay in 45 days" in text
    assert len(d.tables) == 2 and d.tables[1].cell(1, 1).text == "15 days"


# ---- 7. Evaluation ----
def test_scoring_rules():
    item = {"question": "q", "expect_any": [["45"]], "source": "payment_terms.md"}
    good = score_one(item, {"answer": "Net 45 days [payment_terms.md]", "documents": [{"source": "payment_terms.md"}]})
    assert good["retrieval_hit"] and good["answer_correct"] and good["citation_ok"]
    bad = score_one(item, {"answer": "30 days", "documents": [{"source": "termination.md"}]})
    assert not (bad["retrieval_hit"] or bad["answer_correct"] or bad["citation_ok"])


def test_refusal_question_passes_when_model_refuses():
    item = {"question": "CEO salary?", "expect_any": [["do not cover"]], "source": None}
    r = score_one(item, {"answer": "The documents provided do not cover this.", "documents": []})
    assert r["answer_correct"] and r["citation_ok"]


def test_run_evaluation_reports_percentages():
    qs = [{"question": "a", "expect_any": [["45"]], "source": "p.md"},
          {"question": "b", "expect_any": [["24"]], "source": "d.md"}]
    out = run_evaluation(lambda q: {"answer": "45 [p.md]", "documents": [{"source": "p.md"}]}, qs)
    assert out["total"] == 2 and out["answer_accuracy"] == 50.0


def test_question_file_loads():
    from evaluation.evaluate import load_questions
    qs = load_questions()
    assert len(qs) == 13 and all("expect_any" in q for q in qs)
