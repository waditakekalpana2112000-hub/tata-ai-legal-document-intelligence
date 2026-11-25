"""Prompts for each task. Strict rule: answer ONLY from the given context."""

SYSTEM_PROMPT = (
    "You are a careful legal analyst for Tata Group. "
    "Use ONLY the context provided. Never invent clauses, numbers or dates. "
    "If the context does not contain the answer, say: "
    "'The documents provided do not cover this.' "
    "Cite the source file in square brackets after each fact, e.g. [payment_terms.md]. "
    "Write clearly in simple language. This is not legal advice."
)

LANGUAGE_RULE = (
    " Write the whole answer in {language}. Keep file names, numbers and the JSON keys "
    "(if JSON is requested) exactly as they are."
)

JSON_RULE = "Return ONLY valid JSON. No markdown, no code fences, no text before or after it."

TASK_INSTRUCTIONS = {
    "chat": "Answer the user's question.\n\nQuestion: {question}",
    "summarize": (
        "Summarize the agreement in this format:\n"
        "**Purpose** (1-2 lines)\n"
        "**Key clauses** (one bullet per clause: what it says in plain words)\n"
        "**Main obligations of the Vendor** (bullets)\n"
        "**Main rights of Tata Group** (bullets)"
    ),
    "risks": (
        "Review the agreement and list hidden risks, one-sided terms and missing protections. "
        "For each risk give: **Risk**, **Severity** (High/Medium/Low), **Clause**, "
        "**Why it matters**, **Suggested fix**. Order from High to Low. "
        "End with any important clause types that are missing entirely."
    ),
    "deadlines": (
        "Extract every deadline, notice period, duration, time limit and financial term. "
        "Return a markdown table with columns: | Term | Value | What it means | Source |. "
        "After the table, list the 3 deadlines that are easiest to miss."
    ),
    "compliance": (
        "The context has TATA POLICY clauses and a CONTRACT UNDER REVIEW. "
        "Check the contract against every Tata policy topic. Return a markdown table: "
        "| Topic | Tata policy says | Contract says | Status | Risk |. "
        "Status is one of: ✅ Compliant, ⚠️ Deviation, ❌ Missing. Risk is High/Medium/Low. "
        "Cite sources in the cells. After the table, give an overall verdict in one line "
        "and the top 3 changes to ask the vendor for."
    ),
    "compare": (
        "Compare DOCUMENT A and DOCUMENT B clause by clause. Return a markdown table: "
        "| Topic | Document A | Document B | Key difference | Better for Tata |. "
        "Write 'Not mentioned' when a document has no such clause. "
        "After the table, summarize the 3 most important differences."
    ),
    "risk_score": (
        "Assess the overall legal risk of the agreement for Tata Group. " + JSON_RULE + " Schema:\n"
        '{{"overall_score": <integer 0-100, 100 = extremely risky>, "level": "Low|Medium|High", '
        '"summary": "<one sentence>", "risks": [{{"title": "...", "severity": "High|Medium|Low", '
        '"clause": "...", "why": "...", "fix": "...", "source": "<file name>"}}]}}'
    ),
    "deadline_schedule": (
        "Extract every deadline or time period that someone must act on. " + JSON_RULE + " Schema:\n"
        '{{"deadlines": [{{"term": "...", "days": <integer or null>, '
        '"anchor": "start|end|event", "event": "<what starts the clock, if anchor is event>", '
        '"description": "...", "source": "<file name>"}}]}}\n'
        "anchor = start: due `days` after the contract start date. "
        "anchor = end: due `days` before the contract end date. "
        "anchor = event: counted from an event such as an invoice, a breach or termination. "
        "Convert months and years to days (1 month = 30, 1 year = 365)."
    ),
}

JSON_TASKS = {"risk_score", "deadline_schedule"}


def system_prompt(language: str = "English") -> str:
    if language and language != "English":
        return SYSTEM_PROMPT + LANGUAGE_RULE.format(language=language)
    return SYSTEM_PROMPT


def build_context(documents: list[dict]) -> str:
    parts = []
    for d in documents:
        role = f" ({d['role']})" if d.get("role") else ""
        parts.append(f"[{d['source']}]{role}\n{d['text']}")
    return "\n\n---\n\n".join(parts)


def build_history(history: list[dict]) -> str:
    lines = [f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'][:800]}" for m in history]
    return "\n".join(lines)


def build_user_prompt(task: str, question: str, documents: list[dict], history: list[dict] | None = None) -> str:
    instruction = TASK_INSTRUCTIONS.get(task, TASK_INSTRUCTIONS["chat"]).format(question=question)
    convo = ""
    if task == "chat" and history:
        convo = (
            "PREVIOUS CONVERSATION (use it only to understand follow-up questions):\n"
            f"{build_history(history)}\n\n"
        )
    return f"CONTEXT:\n{build_context(documents)}\n\n{convo}TASK:\n{instruction}"
