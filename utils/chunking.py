"""Splits long legal text into small overlapping pieces ("chunks").

Small chunks make vector search precise; the overlap keeps a sentence
that sits on a boundary from being cut in half and lost.
"""
from config import CHUNK_OVERLAP, CHUNK_SIZE

# Try to split on headings first, then paragraphs, lines, sentences, words.
SEPARATORS = ["\n# ", "\n## ", "\n\n", "\n", ". ", " "]


def _split(text: str, size: int, separators: list[str]) -> list[str]:
    if len(text) <= size:
        return [text]
    if not separators:  # no separator left: hard cut
        return [text[i:i + size] for i in range(0, len(text), size)]

    sep, rest = separators[0], separators[1:]
    if sep not in text:
        return _split(text, size, rest)

    pieces, current = [], ""
    for part in text.split(sep):
        candidate = f"{current}{sep}{part}" if current else part
        if len(candidate) <= size:
            current = candidate
        else:
            if current:
                pieces.append(current)
            if len(part) > size:
                pieces.extend(_split(part, size, rest))
                current = ""
            else:
                current = part
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Return a list of chunks (each <= chunk_size + overlap characters)."""
    text = (text or "").strip()
    if not text:
        return []
    pieces = [p.strip() for p in _split(text, chunk_size, SEPARATORS) if p.strip()]
    if overlap <= 0:
        return pieces
    # Prefix each chunk with the tail of the previous one for context.
    chunks = [pieces[0]]
    for prev, cur in zip(pieces, pieces[1:]):
        chunks.append(f"{prev[-overlap:]} {cur}")
    return chunks
