from utils.chunking import chunk_text


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_is_one_chunk():
    assert chunk_text("Net 45 days payment.") == ["Net 45 days payment."]


def test_long_text_is_split_within_size():
    text = "\n\n".join(f"Clause {i}. " + "The vendor shall comply. " * 15 for i in range(10))
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 500 + 51 for c in chunks)


def test_no_text_is_lost():
    text = " ".join(f"word{i}" for i in range(400))
    joined = " ".join(chunk_text(text, chunk_size=200, overlap=0))
    assert all(f"word{i}" in joined for i in range(400))
