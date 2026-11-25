"""ChromaDB vector store: save document chunks and search them by meaning."""
from collections import defaultdict
from typing import Optional

from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, MAX_FULL_CHUNKS, TOP_K
from utils.chunking import chunk_text

_collection = None


def get_collection():
    """Open (or create) the Chroma collection once and reuse it."""
    global _collection
    if _collection is None:
        import chromadb
        from chromadb.utils import embedding_functions

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_document(name: str, text: str, doc_type: str = "upload") -> int:
    """Chunk + embed a document. Re-adding the same name replaces it."""
    chunks = chunk_text(text)
    if not chunks:
        return 0
    col = get_collection()
    col.delete(where={"source": name})
    col.add(
        ids=[f"{name}::{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": name, "type": doc_type, "chunk": i} for i in range(len(chunks))],
    )
    return len(chunks)


def delete_document(name: str) -> None:
    get_collection().delete(where={"source": name})


def list_documents() -> list[dict]:
    data = get_collection().get(include=["metadatas"])
    docs = defaultdict(lambda: {"chunks": 0, "type": ""})
    for meta in data["metadatas"]:
        docs[meta["source"]]["chunks"] += 1
        docs[meta["source"]]["type"] = meta.get("type", "")
    return [{"name": n, **info} for n, info in sorted(docs.items())]


def count() -> int:
    return get_collection().count()


def search(query: str, source: Optional[str] = None, k: int = TOP_K) -> list[dict]:
    """Find the k chunks closest in meaning to the query."""
    col = get_collection()
    if col.count() == 0:
        return []
    res = col.query(
        query_texts=[query],
        n_results=min(k, col.count()),
        where={"source": source} if source else None,
    )
    return [
        {"text": doc, "source": meta["source"], "score": round(1 - dist, 3)}
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def get_document_chunks(source: Optional[str] = None, limit: int = MAX_FULL_CHUNKS,
                        doc_type: Optional[str] = None) -> list[dict]:
    """Return a whole document (or all documents / all of one type) in reading order."""
    where = {"source": source} if source else ({"type": doc_type} if doc_type else None)
    data = get_collection().get(where=where, include=["documents", "metadatas"])
    rows = sorted(
        zip(data["documents"], data["metadatas"]),
        key=lambda r: (r[1]["source"], r[1].get("chunk", 0)),
    )
    return [{"text": d, "source": m["source"], "score": None} for d, m in rows[:limit]]
