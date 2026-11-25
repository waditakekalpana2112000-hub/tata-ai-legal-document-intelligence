"""Central settings for the whole project (paths, model names, API keys)."""
import os
import re
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)  # .env wins over old terminal values


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip().strip("\"'")


# Folders
KB_DIR = BASE_DIR / "Knowledge_base"
CHROMA_DIR = Path(_env("CHROMA_DB_DIR", str(BASE_DIR / "vector_store" / "chroma_db")))
UPLOAD_DIR = BASE_DIR / "uploads"
DB_URL = _env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
EVAL_FILE = BASE_DIR / "evaluation" / "questions.json"

# Vector search
# English: all-MiniLM-L6-v2 (default). For Hindi/Marathi documents use
# EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2 in .env (a new index is built automatically).
EMBEDDING_MODEL = _env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
COLLECTION_NAME = "tata_legal_" + re.sub(r"[^a-z0-9]+", "_", EMBEDDING_MODEL.lower()).strip("_")[:40]
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 4               # chunks used to answer a chat question
MAX_FULL_CHUNKS = 40    # chunks used for summary / risks / deadlines
HISTORY_TURNS = 6       # chat memory: last N messages sent to the LLM

# LLM provider: "groq" (cloud, free key) or "ollama" (offline, runs on your laptop)
LLM_PROVIDER = _env("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = _env("GROQ_API_KEY")
GROQ_MODEL = _env("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_URL = _env("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")
OLLAMA_MODEL = _env("OLLAMA_MODEL", "llama3.2")

# Answer languages offered in the UI
LANGUAGES = ["English", "Hindi", "Marathi"]

# Email reminders (optional) - e.g. Gmail: smtp.gmail.com, 587, an App Password
SMTP_HOST = _env("SMTP_HOST")
SMTP_PORT = int(_env("SMTP_PORT", "587") or 587)
SMTP_USER = _env("SMTP_USER")
SMTP_PASSWORD = _env("SMTP_PASSWORD")
SMTP_FROM = _env("SMTP_FROM") or SMTP_USER

# Frontend -> backend
BACKEND_URL = _env("BACKEND_URL", "http://localhost:8000")
