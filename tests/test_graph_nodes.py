from graph import nodes
from graph.prompts import build_user_prompt

DOCS = [{"text": "Payments are Net 45 days.", "source": "payment_terms.md", "score": 0.9}]


def test_chat_uses_semantic_search(monkeypatch):
    calls = {}
    monkeypatch.setattr(nodes.vector_store, "search", lambda q, source=None: calls.setdefault("q", q) and DOCS)
    out = nodes.retrieve({"question": "payment terms?", "task": "chat"})
    assert calls["q"] == "payment terms?" and out["documents"] == DOCS


def test_audit_tasks_read_whole_document(monkeypatch):
    monkeypatch.setattr(nodes.vector_store, "get_document_chunks", lambda source=None: DOCS)
    assert nodes.retrieve({"question": "", "task": "risks", "source": "x.pdf"})["documents"] == DOCS


def test_generate_sends_context_to_llm(monkeypatch):
    seen = {}

    def fake_llm(system, user):
        seen["prompt"] = user
        return "Net 45 days [payment_terms.md]"

    monkeypatch.setattr(nodes.llm, "ask_llm", fake_llm)
    out = nodes.generate({"question": "When is payment due?", "task": "chat", "documents": DOCS})
    assert "Net 45" in out["answer"]
    assert "payment_terms.md" in seen["prompt"] and "When is payment due?" in seen["prompt"]


def test_no_documents_skips_llm(monkeypatch):
    monkeypatch.setattr(nodes.llm, "ask_llm", lambda *a: (_ for _ in ()).throw(AssertionError("called")))
    assert nodes.generate({"question": "x", "documents": []})["answer"] == nodes.NO_DOCS_ANSWER


def test_each_task_has_its_own_instructions():
    prompts = {t: build_user_prompt(t, "q", DOCS) for t in ["chat", "summarize", "risks", "deadlines"]}
    assert len(set(prompts.values())) == 4
    assert "Severity" in prompts["risks"] and "| Term |" in prompts["deadlines"]
