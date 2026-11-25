# ⚖️ Tata AI Legal Document Intelligence

A RAG (Retrieval-Augmented Generation) system for Tata Group legal policies and uploaded contracts.
It finds the relevant clauses first and then lets an LLM answer **only from those clauses, citing its sources**.

## Features
| Tab | Feature | What it does |
|---|---|---|
| 💬 Chat & Audits | **Chat with memory** | Ask questions; follow-ups like "and for audits?" understand the earlier question |
| | **Summarize / Risks / Deadlines** | One-click audits of any document |
| | **Highlighted sources** | Shows the source chunks and highlights the exact lines behind the answer |
| | **Download report** | A Word (.docx) report with summary, risk score, risk analysis and deadlines |
| 🛡️ Policy Check & Compare | **Contract vs Tata policy** | Flags each clause as ✅ Compliant, ⚠️ Deviation or ❌ Missing |
| | **Compare two contracts** | Clause-by-clause table: which document is better for Tata |
| 📊 Risk Dashboard | **Risk score** | 0–100 score, risk level, a chart by severity and a table of risks with fixes |
| 🗓️ Deadline Tracker | **Real due dates** | Turns notice periods into calendar dates from the contract's start and end dates |
| | **Calendar + email** | Download an .ics file (Google/Outlook/Apple Calendar) or email the reminders |
| 🧪 Accuracy Test | **Evaluation** | 13 questions with known answers; scores retrieval, answer and citation accuracy |
| Sidebar | **Hindi / Marathi** | Answers in English, Hindi or Marathi |
| Settings | **Offline mode** | Runs on a local LLM with Ollama, with no internet or API key |

Also: upload PDF, DOCX, TXT, MD or CSV files, and every query is logged to SQLite (`/history`).

## Architecture
```
Streamlit UI (app.py)  ──HTTP──►  FastAPI (backend/main.py)
                                      │
                                      ▼
                         LangGraph:  retrieve ──► generate
                                      │              │
                         ChromaDB + MiniLM       Groq (GPT-OSS-120B) or Ollama (offline)
```
| Task | What `retrieve` sends to the LLM |
|---|---|
| chat | Top 4 chunks by meaning (the previous question is added for follow-ups) |
| summarize, risks, deadlines, risk score, schedule | The whole selected document |
| policy check | The whole contract plus every Tata policy clause |
| compare | Both whole documents, labelled A and B |

| Folder | Purpose |
|---|---|
| `Knowledge_base/` | Tata policy clauses (markdown) |
| `rag/` | File parsing, vector store, KB loader, LLM client (Groq/Ollama) |
| `graph/` | LangGraph workflow, state and prompts for every task |
| `backend/` | FastAPI endpoints and the SQLite query log |
| `utils/` | Chunking, highlighting, JSON parsing, deadline calendar, Word report, email |
| `evaluation/` | Accuracy test questions and scorer |
| `tests/` | Pytest suite (no API key needed) |

## Setup
```bash
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
```
Put your Groq key in `.env`. The optional settings (offline mode, Hindi/Marathi documents, email) are explained inside `.env.example`.

## Run
```bash
uvicorn backend.main:app --reload     # terminal 1: backend
streamlit run app.py                  # terminal 2: frontend
```
- UI: http://localhost:8501
- API docs: http://localhost:8000/docs

Or run both with Docker: `docker compose up --build`

### Offline mode (no internet)
1. Install Ollama from https://ollama.com and run `ollama pull llama3.2`.
2. In `.env` set `LLM_PROVIDER=ollama`, then restart the backend.

## API
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Status, LLM provider, email setup |
| GET | `/documents` | Indexed documents |
| POST | `/upload` | Upload and index a file |
| POST | `/ask` | `task`: chat / summarize / risks / deadlines / compliance / compare; also `source`, `source_b`, `history`, `language` |
| POST | `/risk-score` | Risk score JSON with counts by severity |
| POST | `/deadlines/schedule` | Deadlines with real due dates (`start_date`, `end_date`) |
| POST | `/deadlines/ics` | Calendar file for the deadlines |
| POST | `/deadlines/remind` | Email the deadlines (needs SMTP in .env) |
| POST | `/report` | Word report (.docx) |
| POST | `/evaluate` | Run the accuracy test |
| GET | `/history` | Recent questions and answers |
| POST | `/reindex` | Rebuild the knowledge base index |
| DELETE | `/documents/{name}` | Remove a document |

## Tests
```bash
pytest tests/                       # 40+ tests, no API key needed
python -m evaluation.evaluate       # real accuracy test (needs the LLM)
```
