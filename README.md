# ⚖️ Tata AI Legal Document Intelligence

An AI-assisted legal document intelligence and review system built with **Generative AI, RAG (Retrieval-Augmented Generation), LangGraph, Evidence-Grounded Retrieval, and Automated Risk & Deadline Intelligence**.

The system analyzes uploaded legal contracts against **Tata Group legal policies**, retrieves relevant policy and contract clauses, highlights exact supporting evidence, flags compliance deviations and clause-level risks with actionable fixes, computes real calendar deadlines, supports multilingual responses (English, Hindi, Marathi), and generates downloadable `.docx` legal review reports.

## 🌐 Live Application

[Open Tata AI Legal Document Intelligence](https://tata-ai-legal-document-intelligence-de6gtcpssxpxloffyrpqhb.streamlit.app/)

The application is deployed on Streamlit Community Cloud with a FastAPI backend hosted on Render and can be accessed directly through the link above.

## 📂 Source Code

[GitHub Repository](https://github.com/waditakekalpana2112000-hub/tata-ai-legal-document-intelligence)

The complete source code, project structure, knowledge base, evaluation suite, and deployment configuration are available in this GitHub repository.

## 🎥 Video Explanation

[Watch the Project Walkthrough Video]([Add your video walkthrough link here])

Watch the video for a complete walkthrough of the business problem, system architecture, AI workflow, live application features, and repository structure.

---

## 🎯 Business Problem & Product Goal

### Business Problem
Reviewing legal contracts and verifying compliance against internal corporate policies manually is time-consuming, repetitive, and prone to human oversight. Legal and business teams often struggle to:
- Quickly locate specific obligations across lengthy contracts
- Spot deviations or missing clauses compared to standard Tata Group legal policies
- Assess overall contract risk and prioritize critical clauses
- Convert relative notice periods (e.g., *"30 days prior written notice"*) into concrete calendar deadlines
- Rely on generic AI tools without risking unsupported answers or missing clause citations

### Product Goal
Build an **evidence-grounded legal document intelligence platform** that automates contract analysis, policy compliance checking, risk scoring, and deadline tracking while citing exact source clauses—giving reviewers verifiable insights, exportable Word reports, calendar reminders, and both cloud and offline LLM execution modes.

---

## ✨ Key Features

### 💬 Conversational Legal Q&A & One-Click Audits
- **Chat with Memory:** Ask natural-language questions about uploaded documents and follow up seamlessly (e.g., *"and for audits?"*) using conversation history.
- **One-Click Audits:** Instantly generate document summaries, risk breakdowns, and deadline extractions from a single interface.
- **Highlighted Source Evidence:** Displays the exact retrieved chunks and highlights the supporting lines behind every answer so findings remain verifiable.
- **Downloadable Word Report (`.docx`):** Exports a structured legal review document containing the executive summary, risk score, detailed risk analysis, and deadlines.

### 🛡️ Tata Policy Compliance Check & Contract Comparison
- **Contract vs. Tata Policy Check:** Evaluates every clause of an uploaded contract against the internal Tata Group legal policy knowledge base, flagging each clause as:
  - ✅ **Compliant**
  - ⚠️ **Deviation**
  - ❌ **Missing**
- **Side-by-Side Contract Comparison:** Compares two contracts (Document A vs. Document B) clause-by-clause to determine which version is more favorable for Tata.

### 📊 Risk Dashboard
- **0–100 Risk Score & Risk Level:** Computes an overall quantitative risk score and risk classification for the contract.
- **Severity Breakdown & Actionable Fixes:** Visualizes risks by severity and presents a structured risk table with recommended remediation steps.

### 🗓️ Deadline Tracker & Automated Reminders
- **Real Due Date Calculation:** Converts contractual notice periods into actual calendar dates based on the contract's `start_date` and `end_date`.
- **Calendar & Email Integration:** Downloads `.ics` calendar files compatible with Google Calendar, Outlook, and Apple Calendar, and sends automated deadline alerts via SMTP email.

### 🌐 Multilingual & Offline Support
- **Multilingual Output:** Generates responses in **English**, **Hindi**, or **Marathi** directly from the sidebar.
- **Offline Local Mode:** Supports running completely offline via **Ollama (`llama3.2`)** with no internet connection or cloud API key required.
- **Multi-Format Upload & Query Logging:** Supports `PDF`, `DOCX`, `TXT`, `MD`, and `CSV` files, with every query logged to a local SQLite database (`/history`).

---

## 🔄 System Workflow & AI Pipeline

```text
                  Document Upload (PDF / DOCX / TXT / MD / CSV)
                                       │
                                       ▼
                        Document Parsing & Chunking
                                       │
                                       ▼
                 Vector Indexing (ChromaDB + MiniLM Embeddings)
                                       │
                                       ▼
                         FastAPI Request (/ask, /risk-score, etc.)
                                       │
                                       ▼
                     LangGraph Workflow: retrieve ──► generate
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
   Chat (Top-4)              Audit / Risk / Deadlines       Policy Check / Compare
 (Semantic chunks)            (Full selected document)      (Full contract + Tata KB
                                                             or Document A vs. B)
        │                              │                              │
        └──────────────────────────────┼──────────────────────────────┘
                                       ▼
                  LLM Inference (Groq GPT-OSS-120B / Offline Ollama)
                                       │
                                       ▼
          Evidence Highlighting • Risk Scoring • Due Dates • .docx / .ics Export
```

### Task-Based Context Routing

| Task | What `retrieve` Sends to the LLM |
| :--- | :--- |
| `chat` | Top 4 semantically relevant chunks (combined with prior question context for follow-ups) |
| `summarize`, `risks`, `deadlines`, `risk score`, `schedule` | Complete text of the selected document |
| `policy check` (`compliance`) | Full uploaded contract alongside all Tata Group policy clauses from `Knowledge_base/` |
| `compare` | Complete text of both selected documents, labeled **Document A** and **Document B** |

---

## 🏗️ Application Architecture

```text
┌─────────────────────────────────────┐
│       Streamlit Frontend (app.py)   │
│  Chat • Policy Check • Risk • Dates │
└──────────────────┬──────────────────┘
                   │ HTTP REST API
                   ▼
┌─────────────────────────────────────┐
│      FastAPI Backend (backend/)     │
│  Endpoints • SQLite Query History   │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│    LangGraph Orchestration (graph/) │
│       State • Prompts • Routing     │
└─────────┬─────────────────┬─────────┘
          │                 │
          ▼                 ▼
┌──────────────────┐ ┌──────────────────────────┐
│    RAG Layer     │ │        LLM Layer         │
│ ChromaDB + MiniLM│ │ Groq (GPT-OSS-120B) or   │
│  Knowledge_base/ │ │ Ollama (llama3.2 offline)│
└──────────────────┘ └──────────────────────────┘
```

---

## 🧩 Tools & Technologies Used

| Technology | Purpose |
| :--- | :--- |
| **Python** | Core backend, RAG, and frontend application development |
| **Streamlit** | Interactive multi-tab web user interface (`app.py`) |
| **FastAPI & Uvicorn** | High-performance REST API backend (`backend/main.py`) |
| **LangGraph** | State-driven workflow orchestration (`retrieve` → `generate`) |
| **ChromaDB** | Vector database for semantic clause storage and retrieval |
| **MiniLM Embeddings** | Dense vector embeddings for semantic similarity search |
| **Groq (`GPT-OSS-120B`)** | Cloud LLM inference for fast legal reasoning and structured outputs |
| **Ollama (`llama3.2`)** | Local LLM runtime for offline, air-gapped execution |
| **SQLite** | Persistent query and response logging (`/history`) |
| **python-docx** | Automated generation of downloadable Word (`.docx`) audit reports |
| **`.ics` & SMTP** | Calendar file export and email deadline reminder notifications |
| **Pytest** | Automated unit and integration test suite (40+ tests) |
| **Docker & Docker Compose** | Containerized multi-service deployment (`Dockerfile.backend`, `Dockerfile.frontend`) |

---

## 📚 Data Sources Used

- **Tata Policy Knowledge Base (`Knowledge_base/`):** Structured Markdown files containing Tata Group corporate legal policy clauses indexed into ChromaDB for compliance benchmarking.
- **User-Uploaded Contracts & Documents:** Dynamic legal files uploaded via the Streamlit UI or `/upload` endpoint in `.pdf`, `.docx`, `.txt`, `.md`, and `.csv` formats.
- **Evaluation Benchmark (`evaluation/`):** A curated dataset of 13 legal Q&A test cases with ground-truth answers and expected source citations.

---

## 📁 Repository Structure

| Folder / File | Purpose |
| :--- | :--- |
| `Knowledge_base/` | Tata Group legal policy clauses stored in Markdown format |
| `rag/` | Document parsing, ChromaDB vector store, knowledge base loader, and Groq/Ollama LLM client |
| `graph/` | LangGraph workflow definition, shared state, and task-specific prompts |
| `backend/` | FastAPI application endpoints and SQLite query history logging |
| `utils/` | Text chunking, source highlighting, JSON parsing, deadline calculator, `.ics` export, `.docx` report builder, and email sender |
| `evaluation/` | 13-question accuracy benchmark and automated evaluation scorer |
| `tests/` | 40+ Pytest unit and integration tests (no API key required) |
| `app.py` | Streamlit frontend application |
| `config.py` | Environment and backend URL configuration |
| `requirements.txt` | Python package dependencies |
| `Dockerfile.backend` / `Dockerfile.frontend` | Container definitions for backend and frontend services |
| `docker-compose.yml` | Local multi-container orchestration |

---

## 🚀 How to Run Locally

### 1. Clone & Install Dependencies

```bash
git clone [https://github.com/waditakekalpana2112000-hub/tata-ai-legal-document-intelligence.git](https://github.com/waditakekalpana2112000-hub/tata-ai-legal-document-intelligence.git)
cd tata-ai-legal-document-intelligence

python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
```

Add your `GROQ_API_KEY` (and any optional settings) inside `.env`.

### 2. Start Backend & Frontend

```bash
# Terminal 1: Start FastAPI backend
uvicorn backend.main:app --reload

# Terminal 2: Start Streamlit UI
streamlit run app.py
```

- **Frontend UI:** `http://localhost:8501`
- **Interactive API Docs:** `http://localhost:8000/docs`

### 3. Run with Docker

```bash
docker compose up --build
```

### 4. Run in Offline Mode (No Internet / No API Key)

1. Install Ollama from `https://ollama.com` and pull a local model:
   ```bash
   ollama pull llama3.2
   ```
2. Set `LLM_PROVIDER=ollama` in your `.env` file and restart the backend.

---

## 🔐 Environment Variables

Configure `.env` using `.env.example` as a template (never commit real secrets or API keys to GitHub):

| Variable | Required | Description |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Yes (Cloud mode) | API key for Groq LLM inference |
| `LLM_PROVIDER` | No (Default: `groq`) | Selects LLM provider: `groq` for cloud or `ollama` for offline mode |
| `OLLAMA_MODEL` | Offline mode | Local Ollama model identifier (e.g., `llama3.2`) |
| `BACKEND_URL` | No | FastAPI backend URL consumed by the Streamlit frontend |
| `SMTP_HOST` / `SMTP_PORT` | Optional | SMTP mail server host and port for `/deadlines/remind` |
| `SMTP_USER` / `SMTP_PASS` | Optional | SMTP authentication credentials for email reminders |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Returns service health, active LLM provider, and email setup status |
| `GET` | `/documents` | Lists all currently indexed documents |
| `POST` | `/upload` | Uploads, parses, and indexes a legal document (`PDF`, `DOCX`, `TXT`, `MD`, `CSV`) |
| `POST` | `/ask` | Executes `chat`, `summarize`, `risks`, `deadlines`, `compliance`, or `compare` with optional `source`, `source_b`, `history`, and `language` |
| `POST` | `/risk-score` | Computes 0–100 risk score JSON and counts grouped by severity |
| `POST` | `/deadlines/schedule` | Calculates concrete due dates from notice periods and `start_date` / `end_date` |
| `POST` | `/deadlines/ics` | Generates a downloadable `.ics` calendar file for extracted deadlines |
| `POST` | `/deadlines/remind` | Dispatches deadline reminder emails via configured SMTP |
| `POST` | `/report` | Generates and returns a formatted Word (`.docx`) review report |
| `POST` | `/evaluate` | Runs the 13-question accuracy evaluation suite |
| `GET` | `/history` | Retrieves past user queries and responses logged in SQLite |
| `POST` | `/reindex` | Rebuilds the Tata policy knowledge base vector index |
| `DELETE` | `/documents/{name}` | Removes an indexed document from the store |

---

## 🧪 Evaluation & Testing

```bash
# Run 40+ automated unit and integration tests (no API key required)
pytest tests/

# Run the 13-question end-to-end RAG accuracy benchmark (requires configured LLM)
python -m evaluation.evaluate
```

### Evaluation Metrics
The evaluation module (`evaluation/evaluate.py`) benchmarks the system across **13 domain-specific legal questions** on three dimensions:
1. **Retrieval Accuracy:** Measures whether the expected Tata policy or contract clauses are retrieved.
2. **Answer Accuracy:** Evaluates correctness and completeness against ground-truth legal answers.
3. **Citation Accuracy:** Verifies that generated answers accurately cite supporting source clauses.

---

## 🖼️ Screenshots

*(Add screenshots of the live application here once uploaded to your repository—such as Chat & Highlighted Sources, Policy Check / Contract Comparison, Risk Dashboard, and Deadline Tracker.)*

---

## ⚠️ Known Limitations & Disclaimer

- **Cloud Cold Starts:** When deployed on free-tier cloud hosting (Render), the backend may take 30–50 seconds to wake up on the initial request after idle periods.
- **Scanned / Image-Only PDFs:** Standard document parsing works best on text-based PDFs and DOCX files; scanned image-only PDFs require OCR preprocessing before indexing.
- **Legal Review Disclaimer:** This system is built as an AI-assisted legal review and portfolio application. Outputs are intended to support initial analysis and should be verified by qualified legal professionals before making binding legal decisions.

---

## 👨‍💻 Author & Team Contribution

**Kalpana Waditake** (`@waditakekalpana2112000-hub`)

Designed, developed, tested, and deployed end-to-end:
- Built the RAG retrieval pipeline, ChromaDB indexing, and Tata Group legal policy knowledge base
- Implemented LangGraph task routing for Q&A, audits, policy compliance checks, and contract comparisons
- Developed the FastAPI backend, SQLite query logging, risk scoring, `.ics` calendar export, email reminders, and `.docx` report generator
- Built the multi-tab Streamlit frontend with English/Hindi/Marathi language support and offline Ollama integration
- Created the 40+ Pytest suite, 13-question accuracy benchmark, Docker setup, and live deployments on Streamlit Community Cloud and Render
