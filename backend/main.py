"""FastAPI backend. Run from the project root:  uvicorn backend.main:app --reload"""
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import List, Literal, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import crud, models
from backend.database import SessionLocal, engine
from config import HISTORY_TURNS, LANGUAGES, UPLOAD_DIR
from rag import vector_store
from rag.document_parser import extract_text
from rag.kb_loader import build_knowledge_base, ensure_knowledge_base
from rag.llm import LLMError, provider_info
from utils.deadline_calendar import build_ics, schedule
from utils.emailer import email_configured, send_reminder
from utils.json_utils import extract_json
from utils.report import build_report

models.Base.metadata.create_all(bind=engine)

Task = Literal["chat", "summarize", "risks", "deadlines", "compliance", "compare"]
TASK_QUESTIONS = {
    "summarize": "Summarize the agreement",
    "risks": "Detect hidden risks",
    "deadlines": "Extract deadlines and terms",
    "compliance": "Check the contract against Tata policy",
    "compare": "Compare the two documents",
    "risk_score": "Score the overall risk",
    "deadline_schedule": "Extract deadlines as a schedule",
}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_knowledge_base()  # build ChromaDB index on first start
    yield


app = FastAPI(title="Tata AI Legal Document Intelligence", lifespan=lifespan)


# ---------- Schemas ----------
class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskRequest(BaseModel):
    question: str = ""
    task: Task = "chat"
    source: Optional[str] = None        # None = search all documents
    source_b: Optional[str] = None      # second document for "compare"
    history: List[Message] = []         # chat memory
    language: str = "English"


class SourceChunk(BaseModel):
    source: str
    text: str
    score: Optional[float] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]


class DocRequest(BaseModel):
    source: Optional[str] = None
    language: str = "English"


class ScheduleRequest(BaseModel):
    source: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None


class ReminderRequest(BaseModel):
    email: str
    contract: str = "Contract"
    deadlines: List[dict]


class IcsRequest(BaseModel):
    contract: str = "Contract"
    deadlines: List[dict]


class HistoryItem(BaseModel):
    id: int
    task: str
    source: Optional[str]
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_graph(question: str, task: str, source: Optional[str], source_b: Optional[str] = None,
              history: Optional[list] = None, language: str = "English") -> dict:
    from graph.graph import run  # imported lazily so tests can mock it
    return run(question, task, source, source_b, history, language)


def _check_language(language: str) -> None:
    if language not in LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Language must be one of {LANGUAGES}")


def _run(question: str, task: str, source=None, source_b=None, history=None, language="English") -> dict:
    try:
        return run_graph(question, task, source, source_b, history, language)
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e))


def _run_json(task: str, source: Optional[str], language: str = "English") -> dict:
    result = _run(TASK_QUESTIONS[task], task, source, language=language)
    if not result.get("documents"):
        raise HTTPException(status_code=404, detail="No documents found for this selection.")
    try:
        return extract_json(result["answer"])
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"{e} Please try again.")


# ---------- Documents ----------
@app.get("/health")
def health():
    return {"status": "ok", "chunks": vector_store.count(), "llm": provider_info(),
            "llm_configured": provider_info()["configured"], "email_configured": email_configured(),
            "languages": LANGUAGES}


@app.get("/documents")
def documents():
    return vector_store.list_documents()


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    UPLOAD_DIR.mkdir(exist_ok=True)
    (UPLOAD_DIR / file.filename).write_bytes(content)
    chunks = vector_store.add_document(file.filename, text, "upload")
    return {"name": file.filename, "chunks": chunks, "characters": len(text)}


@app.delete("/documents/{name}")
def delete(name: str):
    vector_store.delete_document(name)
    return {"deleted": name}


@app.post("/reindex")
def reindex():
    return {"chunks": build_knowledge_base()}


# ---------- Q&A, audits, policy check, compare ----------
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, db: Session = Depends(get_db)):
    _check_language(req.language)
    question = req.question.strip()
    if req.task == "chat" and not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if req.task == "compliance" and not req.source:
        raise HTTPException(status_code=400, detail="Select the contract to check against Tata policy.")
    if req.task == "compare" and (not req.source or not req.source_b or req.source == req.source_b):
        raise HTTPException(status_code=400, detail="Select two different documents to compare.")
    question = question or TASK_QUESTIONS[req.task]
    history = [m.model_dump() for m in req.history][-HISTORY_TURNS:]
    result = _run(question, req.task, req.source, req.source_b, history, req.language)
    crud.log_query(db, req.task, req.source, question, result["answer"])
    return AskResponse(answer=result["answer"], sources=result.get("documents", []))


# ---------- Risk dashboard ----------
@app.post("/risk-score")
def risk_score(req: DocRequest):
    _check_language(req.language)
    data = _run_json("risk_score", req.source, req.language)
    risks = data.get("risks") or []
    counts = {lvl: sum(1 for r in risks if str(r.get("severity", "")).lower() == lvl.lower())
              for lvl in ["High", "Medium", "Low"]}
    try:
        score = max(0, min(100, int(data.get("overall_score", 0))))
    except (TypeError, ValueError):
        score = 0
    return {"overall_score": score, "level": data.get("level", ""), "summary": data.get("summary", ""),
            "risks": risks, "counts": counts}


# ---------- Deadlines: schedule, calendar, email ----------
@app.post("/deadlines/schedule")
def deadline_schedule(req: ScheduleRequest):
    if req.end_date and req.end_date <= req.start_date:
        raise HTTPException(status_code=400, detail="End date must be after the start date.")
    data = _run_json("deadline_schedule", req.source)
    return {"deadlines": schedule(data.get("deadlines") or [], req.start_date, req.end_date)}


@app.post("/deadlines/ics")
def deadline_ics(req: IcsRequest):
    return Response(build_ics(req.deadlines, req.contract), media_type="text/calendar",
                    headers={"Content-Disposition": 'attachment; filename="contract_deadlines.ics"'})


@app.post("/deadlines/remind")
def deadline_remind(req: ReminderRequest):
    if "@" not in req.email:
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    try:
        send_reminder(req.email, req.contract, req.deadlines)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # SMTP / network errors
        raise HTTPException(status_code=502, detail=f"Email failed: {e}")
    return {"sent_to": req.email, "items": len(req.deadlines)}


# ---------- Downloadable report ----------
@app.post("/report")
def report(req: DocRequest):
    _check_language(req.language)
    name = req.source or "All Documents"
    sections = {}
    for task, title in [("summarize", "Summary"), ("risks", "Risk analysis"), ("deadlines", "Deadlines and terms")]:
        sections[title] = _run(TASK_QUESTIONS[task], task, req.source, language=req.language)["answer"]
    try:
        risk = risk_score(req)
    except HTTPException:
        risk = None  # the report still works without the score
    content = build_report(name, sections, risk)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": 'attachment; filename="contract_report.docx"'})


# ---------- Accuracy evaluation ----------
@app.post("/evaluate")
def evaluate():
    from evaluation.evaluate import run_evaluation
    return run_evaluation(lambda q: _run(q, "chat"))


@app.get("/history", response_model=List[HistoryItem])
def history(limit: int = 20, db: Session = Depends(get_db)):
    return crud.get_history(db, limit)
