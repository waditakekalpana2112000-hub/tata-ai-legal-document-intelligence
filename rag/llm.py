"""LLM client. Works with Groq (cloud) or Ollama (offline) - both speak the
OpenAI chat-completions format, so one function handles both."""
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_URL, LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_URL


class LLMError(Exception):
    pass


def provider_info() -> dict:
    if LLM_PROVIDER == "ollama":
        return {"provider": "ollama", "model": OLLAMA_MODEL, "configured": True}
    return {"provider": "groq", "model": GROQ_MODEL, "configured": bool(GROQ_API_KEY)}


def ask_llm(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
    if LLM_PROVIDER == "ollama":
        url, model, headers = OLLAMA_URL, OLLAMA_MODEL, {}
    else:
        if not GROQ_API_KEY:
            raise LLMError("GROQ_API_KEY is not set. Add it to the .env file (see .env.example).")
        url, model, headers = GROQ_URL, GROQ_MODEL, {"Authorization": f"Bearer {GROQ_API_KEY}"}

    import httpx

    try:
        resp = httpx.post(
            url,
            headers=headers,
            json={
                "model": model,
                "temperature": temperature,
                "max_tokens": 3000,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=180,
        )
    except httpx.HTTPError as e:
        where = "Ollama (is `ollama serve` running?)" if LLM_PROVIDER == "ollama" else "Groq"
        raise LLMError(f"Could not reach {where}: {e}") from e
    if resp.status_code != 200:
        raise LLMError(f"{LLM_PROVIDER.title()} error {resp.status_code}: {resp.text[:300]}")
    return (resp.json()["choices"][0]["message"].get("content") or "").strip()
