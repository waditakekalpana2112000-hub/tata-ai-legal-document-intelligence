"""The two steps of the RAG pipeline: retrieve -> generate."""
from graph.prompts import build_user_prompt, system_prompt
from graph.state import GraphState
from rag import llm, vector_store

NO_DOCS_ANSWER = "No relevant documents were found. Upload a document or check the knowledge base."


def _search_query(state: GraphState) -> str:
    """Chat memory: add the previous user question so follow-ups like
    'and what about the vendor?' still find the right clauses."""
    previous = [m["content"] for m in state.get("history", []) if m.get("role") == "user"]
    return f"{previous[-1]} {state['question']}" if previous else state["question"]


def _tag(docs: list[dict], role: str) -> list[dict]:
    return [{**d, "role": role} for d in docs]


def retrieve(state: GraphState) -> dict:
    task = state.get("task", "chat")
    source = state.get("source")

    if task == "chat":
        docs = vector_store.search(_search_query(state), source=source)
    elif task == "compliance":
        # The selected contract + every Tata policy clause.
        if not source:
            return {"documents": []}
        contract = _tag(vector_store.get_document_chunks(source=source), "CONTRACT UNDER REVIEW")
        policy = _tag(vector_store.get_document_chunks(doc_type="knowledge_base"), "TATA POLICY")
        docs = policy + contract
    elif task == "compare":
        source_b = state.get("source_b")
        if not source or not source_b:
            return {"documents": []}
        docs = (_tag(vector_store.get_document_chunks(source=source), "DOCUMENT A")
                + _tag(vector_store.get_document_chunks(source=source_b), "DOCUMENT B"))
    else:  # summarize, risks, deadlines, risk_score, deadline_schedule: read the whole document
        docs = vector_store.get_document_chunks(source=source)
    return {"documents": docs}


def generate(state: GraphState) -> dict:
    docs = state.get("documents", [])
    if not docs:
        return {"answer": NO_DOCS_ANSWER}
    task = state.get("task", "chat")
    prompt = build_user_prompt(task, state.get("question", ""), docs, state.get("history"))
    return {"answer": llm.ask_llm(system_prompt(state.get("language", "English")), prompt)}
