import pytest

pytest.importorskip("fastapi")
pytest.importorskip("chromadb")
from fastapi.testclient import TestClient  # noqa: E402

from backend import main  # noqa: E402

client = TestClient(main.app)  # no `with` = startup indexing is skipped


@pytest.fixture(autouse=True)
def fake_rag(monkeypatch):
    def fake_run(q, t, s=None, s_b=None, history=None, language="English"):
        answers = {
            "risk_score": '{"overall_score": 70, "level": "High", "summary": "x", "risks": '
                          '[{"title": "a", "severity": "High"}, {"title": "b", "severity": "Low"}]}',
            "deadline_schedule": '{"deadlines": [{"term": "Audit", "days": 15, "anchor": "start"}]}',
        }
        return {"answer": answers.get(t, f"answer to {q}"),
                "documents": [{"text": "Net 45", "source": "payment_terms.md", "score": 0.8}]}
    monkeypatch.setattr(main, "run_graph", fake_run)
    monkeypatch.setattr(main.vector_store, "count", lambda: 11)
    monkeypatch.setattr(main.vector_store, "add_document", lambda n, t, k: 1)


def test_health():
    assert client.get("/health").json()["chunks"] == 11


def test_ask_returns_answer_and_sources():
    r = client.post("/ask", json={"question": "payment terms?"})
    assert r.status_code == 200
    assert r.json()["sources"][0]["source"] == "payment_terms.md"


def test_empty_question_rejected():
    assert client.post("/ask", json={"question": "   "}).status_code == 400


def test_button_tasks_need_no_question():
    r = client.post("/ask", json={"task": "risks"})
    assert r.status_code == 200 and "risks" in r.json()["answer"]


def test_questions_are_logged_in_history():
    client.post("/ask", json={"question": "governing law?"})
    assert any(h["question"] == "governing law?" for h in client.get("/history").json())


def test_upload_rejects_bad_type():
    assert client.post("/upload", files={"file": ("x.png", b"\x89PNG")}).status_code == 400


def test_upload_txt():
    r = client.post("/upload", files={"file": ("nda.txt", b"Confidential for 5 years")})
    assert r.status_code == 200 and r.json()["name"] == "nda.txt"


def test_compare_needs_two_different_documents():
    assert client.post("/ask", json={"task": "compare", "source": "a.pdf"}).status_code == 400
    assert client.post("/ask", json={"task": "compare", "source": "a.pdf", "source_b": "a.pdf"}).status_code == 400
    assert client.post("/ask", json={"task": "compare", "source": "a.pdf", "source_b": "b.pdf"}).status_code == 200


def test_policy_check_needs_a_contract():
    assert client.post("/ask", json={"task": "compliance"}).status_code == 400


def test_bad_language_rejected():
    assert client.post("/ask", json={"question": "hi", "language": "French"}).status_code == 400


def test_chat_accepts_history():
    r = client.post("/ask", json={"question": "and audits?", "history": [{"role": "user", "content": "payments?"}]})
    assert r.status_code == 200


def test_risk_score_counts_severities():
    data = client.post("/risk-score", json={}).json()
    assert data["overall_score"] == 70 and data["counts"] == {"High": 1, "Medium": 0, "Low": 1}


def test_deadline_schedule_and_calendar():
    rows = client.post("/deadlines/schedule", json={"start_date": "2026-01-01"}).json()["deadlines"]
    assert rows[0]["due_date"] == "2026-01-16"
    ics = client.post("/deadlines/ics", json={"deadlines": rows})
    assert ics.status_code == 200 and "BEGIN:VEVENT" in ics.text


def test_reminder_without_smtp_is_explained(monkeypatch):
    import utils.emailer
    monkeypatch.setattr(utils.emailer, "SMTP_HOST", "")
    r = client.post("/deadlines/remind", json={"email": "a@b.com", "deadlines": []})
    assert r.status_code == 400 and "SMTP" in r.json()["detail"]


def test_report_returns_docx():
    pytest.importorskip("docx")
    r = client.post("/report", json={})
    assert r.status_code == 200 and r.content[:2] == b"PK"


def test_evaluate_returns_scores():
    data = client.post("/evaluate").json()
    assert data["total"] == 13 and "answer_accuracy" in data
