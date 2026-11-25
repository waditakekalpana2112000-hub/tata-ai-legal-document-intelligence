"""Loads the Knowledge_base/*.md policy files into ChromaDB.

Run manually from the project root:   python -m rag.kb_loader
(The backend also runs this automatically on first start.)
"""
from config import KB_DIR
from rag import vector_store


def build_knowledge_base() -> int:
    files = sorted(KB_DIR.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No .md files found in {KB_DIR}")
    total = 0
    for path in files:
        n = vector_store.add_document(path.name, path.read_text(encoding="utf-8"), "knowledge_base")
        print(f"  {path.name}: {n} chunks")
        total += n
    return total


def ensure_knowledge_base() -> None:
    """Build the index only if the knowledge base isn't loaded yet."""
    loaded = {d["name"] for d in vector_store.list_documents() if d["type"] == "knowledge_base"}
    if not {p.name for p in KB_DIR.glob("*.md")} <= loaded:
        build_knowledge_base()


if __name__ == "__main__":
    print(f"Loading legal documents from {KB_DIR} ...")
    print(f"SUCCESS: {build_knowledge_base()} chunks stored in ChromaDB")
