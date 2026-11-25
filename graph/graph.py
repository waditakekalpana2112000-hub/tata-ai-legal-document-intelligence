"""LangGraph workflow:  START -> retrieve -> generate -> END"""
from langgraph.graph import END, START, StateGraph

from graph.nodes import generate, retrieve
from graph.state import GraphState

workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()


def run(question: str, task: str = "chat", source: str | None = None, source_b: str | None = None,
        history: list | None = None, language: str = "English") -> dict:
    return app.invoke({
        "question": question, "task": task, "source": source, "source_b": source_b,
        "history": history or [], "language": language,
    })


if __name__ == "__main__":
    # Quick demo from the project root:  python -m graph.graph
    from rag.kb_loader import ensure_knowledge_base

    ensure_knowledge_base()
    result = run("What is the governing law for the Tata contract?")
    print(result["answer"])
    print("\nSources:", sorted({d["source"] for d in result["documents"]}))
