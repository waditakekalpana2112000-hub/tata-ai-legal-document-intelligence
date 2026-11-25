"""Lightweight in-memory document store and keyword-overlap retriever (low RAM)."""
from collections import defaultdict
import re
from typing import Optional

from config import MAX_FULL_CHUNKS, TOP_K
from utils.chunking import chunk_text

# _store[doc_name] = {"type": str, "chunks": list[str]}
_store: dict[str, dict] = {}


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9_]+", text.lower()) if len(w) > 1}


def add_document(name: str, text: str, doc_type: str = "upload") -> int:
    """Chunk a document in memory. Re-adding the same name replaces it."""
    chunks = chunk_text(text)
    if not chunks:
        return 0
    _store[name] = {
        "type": doc_type,
        "chunks": chunks,
    }
    return len(chunks)


def delete_document(name: str) -> None:
    _store.pop(name, None)


def list_documents() -> list[dict]:
    docs = defaultdict(lambda: {"chunks": 0, "type": ""})
    for name, info in _store.items():
        docs[name]["chunks"] = len(info["chunks"])
        docs[name]["type"] = info.get("type", "")
    return [{"name": n, **info} for n, info in sorted(docs.items())]


def count() -> int:
    return sum(len(info["chunks"]) for info in _store.values())


def search(query: str, source: Optional[str] = None, k: int = TOP_K) -> list[dict]:
    """Find the top-k chunks matching query keywords."""
    q_tokens = _tokenize(query)
    scored: list[tuple[float, str, str]] = []

    target_items = (
        [(source, _store[source])] if (source and source in _store) else list(_store.items())
    )

    for doc_name, info in target_items:
        for chunk in info["chunks"]:
            c_tokens = _tokenize(chunk)
            if not c_tokens:
                continue
            overlap = len(q_tokens & c_tokens)
            score = round(overlap / max(len(q_tokens), 1), 3) if q_tokens else 0.0
            scored.append((score, doc_name, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {"text": chunk, "source": doc_name, "score": score}
        for score, doc_name, chunk in scored[:k]
    ]


def get_document_chunks(
    source: Optional[str] = None,
    limit: int = MAX_FULL_CHUNKS,
    doc_type: Optional[str] = None,
) -> list[dict]:
    """Return document chunks in reading order."""
    rows: list[tuple[str, str]] = []
    for doc_name, info in sorted(_store.items()):
        if source and doc_name != source:
            continue
        if doc_type and info.get("type") != doc_type:
            continue
        for chunk in info["chunks"]:
            rows.append((doc_name, chunk))

    return [{"text": chunk, "source": doc_name, "score": None} for doc_name, chunk in rows[:limit]]