# ⚖️ Tata AI Legal Document Intelligence

An AI-assisted legal document intelligence and review system built with **Generative AI, RAG (Retrieval-Augmented Generation), LangGraph, evidence-grounded retrieval, and Human-in-the-Loop review**. It analyzes Tata Group legal policies and uploaded contracts, extracts key clauses, checks information sufficiency, flags risks and policy deviations, tracks real deadlines, and generates verifiable summaries and `.docx` reports.

## 🌐 Live Application

[Open Tata AI Legal Document Intelligence](https://tata-ai-legal-document-intelligence-de6gtcpssxpxloffyrpqhb.streamlit.app/)

The application is deployed and can be accessed directly through the link above.

## 📂 Source Code

[GitHub Repository](https://github.com/waditakekalpana2112000-hub/tata-ai-legal-document-intelligence)

The complete source code, project structure, documentation, and configuration are available in this GitHub repository.

## 🎥 Video Explanation

[Watch the Project Walkthrough Video]([Add your video walkthrough link here])

Walkthrough of the project workflow, end-to-end architecture, live application features, and repository overview.

---

## 🎯 Business Problem & Product Goal

### Business Problem
Reviewing legal contracts and internal compliance policies manually is slow, repetitive, and dependent on specialized legal bandwidth. Teams often have to sift through dense clauses to spot high-risk terms, deviations from internal policy, and notice-period deadlines, while general-purpose AI tools can produce unsupported claims without clear clause citations.

### Product Goal
Provide an evidence-grounded legal review workspace that evaluates contracts against Tata Group legal policies, highlights risks with actionable fixes, converts notice periods into real calendar deadlines, supports multilingual responses and offline execution, and keeps human reviewers in control before finalizing outputs.

---

## ✨ Key Features

| Tab / Area | Feature | What It Does |
| :--- | :--- | :--- |
| 💬 Chat & Audits | Chat with memory | Ask follow-up questions (such as *"and for audits?"*) with conversational context |
| 💬 Chat & Audits | Summarize / Risks / Deadlines | One-click audits across selected documents |
| 💬 Chat & Audits | Highlighted sources | Shows retrieved source chunks and highlights exact supporting lines |
| 💬 Chat & Audits | Download report | Generates a Word (`.docx`) report with summary, risk score, risk analysis, and deadlines |
| 🛡️ Policy Check & Compare | Contract vs. Tata policy | Flags clauses as ✅ Compliant, ⚠️ Deviation, or ❌ Missing |
| 🛡️ Policy Check & Compare | Compare two contracts | Side-by-side clause comparison to help assess which contract is more favorable for Tata |
| 📊 Risk Dashboard | Risk score | Computes a 0–100 risk score, overall risk level, severity breakdown chart, and risk table with fixes |
| 🗓️ Deadline Tracker | Real due dates | Converts notice periods into concrete calendar dates from contract start and end dates |
| 🗓️ Deadline Tracker | Calendar + email | Exports `.ics` calendar files (Google/Outlook/Apple Calendar) and sends email reminders via SMTP |
| 🧪 Accuracy Test | Evaluation | Runs a 13-question benchmark scoring retrieval, answer, and citation accuracy |
| Sidebar | Hindi / Marathi | Generates answers in English, Hindi, or Marathi |
| Settings | Offline mode | Runs locally via Ollama without requiring internet access or a cloud API key |

Additional capabilities: upload `PDF`, `DOCX`, `TXT`, `MD`, or `CSV` files, and log every query to SQLite (`/history`).

---

## 🏗️ Architecture & AI Workflow

```text
Streamlit UI (app.py)  ──HTTP──►  FastAPI (backend/main.py)
                                      │
                                      ▼
                         LangGraph:  retrieve ──► generate
                                      │              │
                         ChromaDB + MiniLM       Groq (GPT-OSS-120B) or Ollama (offline)
AI Workflow & Task RoutingInput & Sufficiency / Clause Context: Receives user queries or uploaded legal documents and prepares the relevant context based on the requested task.Retrieval (retrieve): Uses ChromaDB and MiniLM embeddings to retrieve relevant policy/contract chunks or full document context depending on the task:chat: Top 4 semantically matching chunks (incorporating prior turn context for follow-ups)summarize, risks, deadlines, risk score, schedule: Full selected documentpolicy check: Full contract plus Tata Group policy clausescompare: Both documents (source and source_b) labeled A and BGeneration & Grounding (generate): Runs through LangGraph prompts using Groq (GPT-OSS-120B) or local Ollama (llama3.2), grounding answers in retrieved text and surfacing supporting evidence/citations.Human-in-the-Loop & Export: Reviewers can inspect evidence, risk findings, schedules, and evaluation scores before exporting .docx reports, .ics calendar files, or sending reminders.Repository StructureFolder / FilePurposeKnowledge_base/Tata Group legal policy clauses in Markdown formatrag/File parsing, vector store, KB loader, and LLM client (Groq / Ollama)graph/LangGraph workflow, state definitions, and task promptsbackend/FastAPI endpoints and SQLite query loggingutils/Chunking, text highlighting, JSON parsing, deadline calendar, .docx report, and email utilitiesevaluation/Benchmark questions and evaluation scorertests/Pytest suite (runs without an API key)app.pyStreamlit frontend applicationconfig.pyApplication and backend URL configurationrequirements.txtPython dependenciesdocker-compose.ymlMulti-service Docker setup (Dockerfile.backend and Dockerfile.frontend)🛠️ Tools & Technologies UsedFrontend: StreamlitBackend API: FastAPI, UvicornWorkflow & RAG: LangGraph, ChromaDB, MiniLM embeddingsLLMs: Groq (GPT-OSS-120B) for cloud inference; Ollama (llama3.2) for offline local inferencePersistence & Formats: SQLite, python-docx, .ics calendar export, SMTP email remindersTesting & Deployment: Pytest, Docker / Docker Compose, Streamlit Community Cloud, Render📚 Data Sources UsedTata Policy Knowledge Base (Knowledge_base/): Markdown files containing Tata Group policy clauses indexed for retrieval and compliance checking.Uploaded Contracts & Documents: Legal files uploaded through the UI or /upload API (PDF, DOCX, TXT, MD, CSV).Evaluation Dataset (evaluation/): Benchmark set of 13 legal Q&A items used to measure retrieval, answer, and citation accuracy.🚀 How to Run Locally1. SetupBashpython -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
Add your Groq API key (and any optional settings) inside .env.2. Run Backend & FrontendBashuvicorn backend.main:app --reload     # Terminal 1: Backend API
streamlit run app.py                  # Terminal 2: Streamlit UI
UI: http://localhost:8501API Docs: http://localhost:8000/docs3. Run with DockerBashdocker compose up --build
4. Offline Mode (No Internet / No API Key)Install Ollama from https://ollama.com and pull a model (e.g., ollama pull llama3.2).Set LLM_PROVIDER=ollama in .env and restart the backend.🔐 Environment VariablesConfigure .env from .env.example (never commit real secrets or API keys to GitHub):VariableRequiredPurposeGROQ_API_KEYFor cloud LLM (groq)API key for Groq model inferenceLLM_PROVIDEROptionalSelects LLM provider (groq or ollama)OLLAMA_MODELFor offline modeLocal model name in Ollama (e.g., llama3.2)BACKEND_URLOptionalFastAPI backend URL used by the Streamlit appSMTP / Email settingsOptionalSMTP configuration for /deadlines/remind email alerts🔌 API EndpointsMethodEndpointDescriptionGET/healthService status, LLM provider, and email configuration statusGET/documentsLists indexed documentsPOST/uploadUploads and indexes a documentPOST/askRuns chat, summarize, risks, deadlines, compliance, or compare (supports source, source_b, history, language)POST/risk-scoreReturns risk score JSON and counts by severityPOST/deadlines/scheduleComputes actual due dates from notice periods and start_date / end_datePOST/deadlines/icsGenerates an .ics calendar file for deadlinesPOST/deadlines/remindSends deadline reminders via email (requires SMTP in .env)POST/reportGenerates a Word (.docx) reportPOST/evaluateRuns the evaluation benchmarkGET/historyFetches logged questions and answers from SQLitePOST/reindexRebuilds the knowledge base vector indexDELETE/documents/{name}Deletes an indexed document🧪 Evaluation & TestingBashpytest tests/                       # 40+ unit/integration tests (no API key needed)
python -m evaluation.evaluate       # 13-question accuracy test (requires configured LLM)
The evaluation suite assesses retrieval accuracy, answer accuracy, and citation accuracy across 13 benchmark questions.🖼️ ScreenshotsAdd screenshots of the live application here once uploaded to the repository (for example, Chat & Highlighted Sources, Policy Check / Contract Comparison, and Risk Dashboard).⚠️ Known LimitationsCloud Cold Starts: Free/starter cloud tiers (such as Render) may take extra time on the first request after inactivity.Scanned Documents: Image-heavy or scanned PDFs without embedded text may require OCR before reliable text extraction.Legal Review Disclaimer: System outputs support legal analysis and review; final legal decisions should still be verified by a qualified legal professional.👥 Team ContributionKalpana Waditake (@waditakekalpana2112000-hub) — Project design, RAG & LangGraph pipeline, FastAPI backend, Streamlit frontend, evaluation & test suite, and deployment on Render and Streamlit Community Cloud.
