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
