"""Highlight the sentences in a source chunk that the answer is based on."""
import html
import re

STOP = {
    "the", "and", "for", "with", "that", "this", "shall", "will", "from", "have", "must", "are",
    "any", "all", "its", "not", "been", "into", "such", "each", "within", "under", "their",
    "which", "what", "when", "there", "these", "those", "than", "other", "only", "also", "provided",
    "documents", "document", "agreement", "source",
}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9%]+", text.lower()) if (len(w) > 3 or w.isdigit()) and w not in STOP}


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p for p in (s.strip() for s in parts) if p]


def best_sentences(chunk: str, answer: str, min_overlap: int = 2) -> list[str]:
    """Sentences of `chunk` sharing the most meaningful words with `answer`."""
    target = _words(answer)
    scored = [(len(_words(s) & target), s) for s in split_sentences(chunk)]
    top = max((score for score, _ in scored), default=0)
    if top < min_overlap:
        return []
    return [s for score, s in scored if score >= max(min_overlap, top * 0.6)]


def highlight_html(chunk: str, answer: str) -> str:
    """Return the chunk as safe HTML with the supporting sentences in <mark>."""
    out = html.escape(chunk)
    for sentence in best_sentences(chunk, answer):
        safe = html.escape(sentence)
        out = out.replace(safe, f"<mark>{safe}</mark>", 1)
    return out.replace("\n", "<br>")
