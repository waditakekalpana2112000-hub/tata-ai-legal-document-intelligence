"""Streamlit frontend. Run from the project root:  streamlit run app.py
(The FastAPI backend must be running first.)"""
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st

from config import BACKEND_URL, HISTORY_TURNS
from utils.highlight import highlight_html

ALL_DOCS = "All Documents"

st.set_page_config(page_title="Tata Group AI Legal Document Intelligence System", layout="wide")
st.markdown("""
    <style>
    .main-header { font-size: 2.3rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0; }
    .sub-header { font-size: 1.05rem; color: #6B7280; margin-bottom: 20px; }
    .stButton>button, .stDownloadButton>button { width: 100%; border-radius: 6px; }
    mark { background: #FDE68A; color: #111827; padding: 0 2px; border-radius: 3px; }
    .src { font-size: 0.92rem; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)


# ---------- Backend helpers ----------
def api(method: str, path: str, raw: bool = False, **kwargs):
    """Call the backend; return (data, error_message). raw=True returns bytes."""
    try:
        r = httpx.request(method, f"{BACKEND_URL}{path}", timeout=300, **kwargs)
    except httpx.HTTPError:
        return None, f"Backend not reachable at {BACKEND_URL}. Start it with: uvicorn backend.main:app --reload"
    if r.status_code >= 400:
        try:
            return None, r.json().get("detail", r.text)
        except ValueError:
            return None, r.text
    return (r.content if raw else r.json()), None


def show_sources(sources, answer: str = ""):
    if sources:
        with st.expander(f"📚 Sources used ({len(sources)} chunks). Highlighted = the lines behind the answer"):
            for s in sources:
                score = f" · match {s['score']:.2f}" if s.get("score") is not None else ""
                st.markdown(f"**{s['source']}**{score}")
                st.markdown(f"<div class='src'>{highlight_html(s['text'], answer)}</div>", unsafe_allow_html=True)


for key, default in {"messages": [], "uploaded": set(), "risk": None, "schedule": None, "eval": None,
                     "panel": None, "report": None}.items():
    st.session_state.setdefault(key, default)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 📁 Document Hub")
    health, err = api("GET", "/health")
    if err:
        st.error(err)
        st.stop()
    llm = health["llm"]
    st.caption(f"🤖 LLM: **{llm['provider']}** · {llm['model']}" + (" · offline" if llm["provider"] == "ollama" else ""))
    if not health["llm_configured"]:
        st.warning("GROQ_API_KEY missing in .env, so AI answers won't work yet.")

    language = st.selectbox("🌐 Answer language", health.get("languages", ["English"]))

    uploaded_file = st.file_uploader("Upload Legal File", type=["txt", "md", "pdf", "docx", "csv"])
    if uploaded_file is not None:
        key = (uploaded_file.name, uploaded_file.size)
        if key not in st.session_state.uploaded:
            with st.spinner(f"Indexing {uploaded_file.name}..."):
                data, err = api("POST", "/upload", files={"file": (uploaded_file.name, uploaded_file.getvalue())})
            if err:
                st.error(err)
            else:
                st.session_state.uploaded.add(key)
                st.success(f"{data['name']} indexed ({data['chunks']} chunks)")

    st.divider()
    st.markdown("### 📄 Available Documents")
    docs, _ = api("GET", "/documents")
    docs = docs or []
    uploads = [d["name"] for d in docs if d["type"] == "upload"]
    kb = [d["name"] for d in docs if d["type"] == "knowledge_base"]
    st.caption(f"Knowledge base: {len(kb)} policy files")
    for name in uploads:
        st.markdown(f"- 📎 {name}")
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

all_names = uploads + kb
options = [ALL_DOCS] + all_names


def pick(label: str, key: str, opts=None):
    choice = st.selectbox(label, opts or options, key=key)
    return None if choice == ALL_DOCS else choice


# ---------- Header ----------
st.markdown('<div class="main-header">⚖️ Tata Group AI Legal Document Intelligence System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Document RAG & Automated Legal Audit Assistant</div>', unsafe_allow_html=True)

tab_chat, tab_policy, tab_risk, tab_dates, tab_eval = st.tabs(
    ["💬 Chat & Audits", "🛡️ Policy Check & Compare", "📊 Risk Dashboard", "🗓️ Deadline Tracker", "🧪 Accuracy Test"])

# ---------- Tab 1: chat, audits, report ----------
with tab_chat:
    source = pick("Select Document to Analyze:", "chat_doc")
    c1, c2, c3 = st.columns(3)
    actions = {"summarize": c1.button("🔍 Summarize Agreement"),
               "risks": c2.button("⚠️ Detect Hidden Risks"),
               "deadlines": c3.button("🗓️ Extract Deadlines/Terms")}
    labels = {"summarize": "Summary", "risks": "Risk report", "deadlines": "Deadlines & terms"}
    for task, clicked in actions.items():
        if clicked:
            with st.spinner("Reading the documents and thinking..."):
                data, err = api("POST", "/ask", json={"task": task, "source": source, "language": language})
            st.session_state.messages.append(
                {"role": "assistant", "content": f"❌ {err}", "sources": [], "error": True} if err else
                {"role": "assistant", "content": f"**{labels[task]}: {source or ALL_DOCS}**\n\n{data['answer']}",
                 "sources": data["sources"]})

    with st.expander("📥 Download full report (Word)"):
        st.caption("Runs summary, risk analysis, deadlines and the risk score, then builds a .docx file. Takes about a minute.")
        if st.button("Generate report", key="gen_report"):
            with st.spinner("Writing the report..."):
                content, err = api("POST", "/report", raw=True, json={"source": source, "language": language})
            if err:
                st.error(err)
            else:
                st.session_state.report = (content, source or ALL_DOCS)
        if st.session_state.report:
            content, name = st.session_state.report
            st.download_button(f"⬇️ Download report: {name}", content, file_name="contract_report.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    st.divider()
    st.markdown("#### 💬 Chat with Document Context")
    st.caption("Remembers the conversation, so follow-up questions work.")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            show_sources(msg.get("sources"), msg["content"])

# chat_input must live outside tabs/columns so it stays pinned at the bottom
if query := st.chat_input("Ask a question about the selected document..."):
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages
               if not m.get("error")][-HISTORY_TURNS:]
    st.session_state.messages.append({"role": "user", "content": query})
    with st.spinner("Thinking..."):
        data, err = api("POST", "/ask", json={"task": "chat", "source": st.session_state.get("chat_doc") if
                                              st.session_state.get("chat_doc") != ALL_DOCS else None,
                                              "question": query, "history": history, "language": language})
    st.session_state.messages.append(
        {"role": "assistant", "content": f"❌ {err}", "sources": [], "error": True} if err else
        {"role": "assistant", "content": data["answer"], "sources": data["sources"]})
    st.rerun()

# ---------- Tab 2: policy compliance + compare ----------
with tab_policy:
    st.markdown("#### 🛡️ Check a contract against Tata policy")
    st.caption("Upload a vendor contract, then check every clause against the Tata policy knowledge base.")
    if not uploads:
        st.info("Upload a contract in the sidebar first.")
    else:
        contract = st.selectbox("Contract to check", uploads, key="policy_doc")
        if st.button("Run policy check"):
            with st.spinner("Comparing the contract with every Tata policy..."):
                data, err = api("POST", "/ask", json={"task": "compliance", "source": contract, "language": language})
            st.session_state.panel = ("Policy check", contract, data, err)

    st.divider()
    st.markdown("#### ⚖️ Compare two documents")
    if len(all_names) < 2:
        st.info("Need at least two documents.")
    else:
        a, b = st.columns(2)
        doc_a = a.selectbox("Document A", all_names, key="cmp_a")
        doc_b = b.selectbox("Document B", all_names, index=1, key="cmp_b")
        if st.button("Compare documents"):
            with st.spinner("Comparing clause by clause..."):
                data, err = api("POST", "/ask", json={"task": "compare", "source": doc_a, "source_b": doc_b,
                                                      "language": language})
            st.session_state.panel = ("Comparison", f"{doc_a} vs {doc_b}", data, err)

    if st.session_state.panel:
        title, name, data, err = st.session_state.panel
        st.markdown(f"### {title}: {name}")
        if err:
            st.error(err)
        else:
            st.markdown(data["answer"])
            show_sources(data["sources"], data["answer"])

# ---------- Tab 3: risk dashboard ----------
with tab_risk:
    st.markdown("#### 📊 Contract risk dashboard")
    risk_doc = pick("Document", "risk_doc")
    if st.button("Calculate risk score"):
        with st.spinner("Scoring the contract..."):
            data, err = api("POST", "/risk-score", json={"source": risk_doc, "language": language})
        st.session_state.risk = (risk_doc or ALL_DOCS, data, err)
    if st.session_state.risk:
        name, data, err = st.session_state.risk
        if err:
            st.error(err)
        else:
            colour = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(data["level"], "⚪")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Overall risk score", f"{data['overall_score']}/100")
            m2.metric("Risk level", f"{colour} {data['level']}")
            m3.metric("High-severity risks", data["counts"]["High"])
            m4.metric("Total risks found", len(data["risks"]))
            st.progress(data["overall_score"] / 100)
            st.caption(f"{name}: {data['summary']}")
            chart = pd.DataFrame({"Risks": [data["counts"][k] for k in ["High", "Medium", "Low"]]},
                                 index=["High", "Medium", "Low"])
            st.bar_chart(chart, color="#C2410C")
            if data["risks"]:
                table = pd.DataFrame(data["risks"]).rename(columns=str.title)
                st.dataframe(table, use_container_width=True, hide_index=True)

# ---------- Tab 4: deadline tracker ----------
with tab_dates:
    st.markdown("#### 🗓️ Deadline tracker")
    st.caption("Enter the contract dates, and the AI turns every notice period into a real calendar date.")
    d1, d2, d3 = st.columns(3)
    dl_doc = d1.selectbox("Document", options, key="dl_doc")
    start = d2.date_input("Contract start date", date.today())
    end = d3.date_input("Contract end date", date.today() + timedelta(days=365))
    if st.button("Build deadline schedule"):
        with st.spinner("Extracting deadlines..."):
            data, err = api("POST", "/deadlines/schedule", json={
                "source": None if dl_doc == ALL_DOCS else dl_doc,
                "start_date": start.isoformat(), "end_date": end.isoformat()})
        st.session_state.schedule = (dl_doc, data, err)
    if st.session_state.schedule:
        name, data, err = st.session_state.schedule
        if err:
            st.error(err)
        else:
            rows = data["deadlines"]
            if not rows:
                st.info("No deadlines found.")
            else:
                table = pd.DataFrame(rows).reindex(
                    columns=["due_date", "status", "term", "description", "event", "source"])
                table.columns = ["Due date", "Status", "Term", "What it means", "Starts from", "Source"]
                st.dataframe(table.fillna(""), use_container_width=True, hide_index=True)
                ics, err = api("POST", "/deadlines/ics", raw=True, json={"contract": name, "deadlines": rows})
                if ics:
                    st.download_button("📅 Add to my calendar (.ics)", ics, file_name="contract_deadlines.ics",
                                       mime="text/calendar")
                with st.form("remind"):
                    email = st.text_input("📧 Email me these deadlines")
                    if st.form_submit_button("Send reminder email"):
                        if not health["email_configured"]:
                            st.warning("Email isn't set up. Add SMTP settings to .env (see README). "
                                       "Use the calendar file instead.")
                        else:
                            res, err = api("POST", "/deadlines/remind",
                                           json={"email": email, "contract": name, "deadlines": rows})
                            if err:
                                st.error(err)
                            else:
                                st.success(f"Sent to {res['sent_to']}")

# ---------- Tab 5: evaluation ----------
with tab_eval:
    st.markdown("#### 🧪 Accuracy test")
    st.caption("Asks 13 questions with known answers (including one the documents can't answer) "
               "and checks the retrieval, the answer and the citation.")
    if st.button("Run accuracy test"):
        with st.spinner("Running 13 questions... about a minute"):
            data, err = api("POST", "/evaluate")
        st.session_state.eval = (data, err)
    if st.session_state.eval:
        data, err = st.session_state.eval
        if err:
            st.error(err)
        else:
            e1, e2, e3 = st.columns(3)
            e1.metric("Retrieval hit rate", f"{data['retrieval_hit_rate']}%")
            e2.metric("Answer accuracy", f"{data['answer_accuracy']}%")
            e3.metric("Citation accuracy", f"{data['citation_accuracy']}%")
            table = pd.DataFrame(data["results"])
            for col in ["retrieval_hit", "answer_correct", "citation_ok"]:
                table[col] = table[col].map({True: "✅", False: "❌"})
            st.dataframe(table, use_container_width=True, hide_index=True)
