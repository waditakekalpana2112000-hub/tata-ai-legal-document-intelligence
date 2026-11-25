from typing import List, Optional, TypedDict


class GraphState(TypedDict, total=False):
    question: str            # user's question (or task name for buttons)
    task: str                # chat | summarize | risks | deadlines | compliance | compare | risk_score | deadline_schedule
    source: Optional[str]    # one document name, or None = all documents
    source_b: Optional[str]  # second document (compare only)
    history: List[dict]      # earlier chat messages: {role, content}
    language: str            # English | Hindi | Marathi
    documents: List[dict]    # retrieved chunks: {text, source, score, role?}
    answer: str
