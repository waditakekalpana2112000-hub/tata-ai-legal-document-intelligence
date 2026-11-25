"""Accuracy evaluation: run a fixed set of questions with known answers and score the system.

Three scores per question:
- retrieval_hit: the expected policy file was among the retrieved chunks
- answer_correct: the answer contains the expected fact (or refuses when it should)
- citation_ok:   the answer cites the expected file

Run from the project root:  python -m evaluation.evaluate
"""
import json
from typing import Callable

from config import EVAL_FILE


def load_questions(path=EVAL_FILE) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def score_one(item: dict, result: dict) -> dict:
    answer = result.get("answer", "")
    low = answer.lower()
    sources = {d["source"] for d in result.get("documents", [])}
    expected = item.get("source")
    correct = all(any(k.lower() in low for k in group) for group in item["expect_any"])
    return {
        "question": item["question"],
        "expected_source": expected or "(should refuse)",
        "retrieval_hit": (expected in sources) if expected else True,
        "answer_correct": correct,
        "citation_ok": (expected in answer) if expected else correct,
        "answer": answer,
    }


def run_evaluation(run_fn: Callable[[str], dict], questions: list[dict] | None = None) -> dict:
    """run_fn(question) -> {"answer": str, "documents": [...]} (the RAG pipeline)."""
    questions = questions if questions is not None else load_questions()
    rows = [score_one(q, run_fn(q["question"])) for q in questions]
    n = len(rows) or 1

    def pct(key: str) -> float:
        return round(100 * sum(r[key] for r in rows) / n, 1)

    return {
        "total": len(rows),
        "retrieval_hit_rate": pct("retrieval_hit"),
        "answer_accuracy": pct("answer_correct"),
        "citation_accuracy": pct("citation_ok"),
        "results": rows,
    }


if __name__ == "__main__":
    from graph.graph import run
    from rag.kb_loader import ensure_knowledge_base

    ensure_knowledge_base()
    report = run_evaluation(lambda q: run(q))
    for r in report["results"]:
        mark = "PASS" if r["answer_correct"] and r["citation_ok"] else "FAIL"
        print(f"[{mark}] {r['question']}")
    print(f"\nRetrieval hit rate: {report['retrieval_hit_rate']}%")
    print(f"Answer accuracy:    {report['answer_accuracy']}%")
    print(f"Citation accuracy:  {report['citation_accuracy']}%")
