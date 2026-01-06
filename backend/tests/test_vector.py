from app.vector.chunking import chunk_text


def test_chunk_empty_text():
    result = chunk_text("")
    assert result == []


def test_chunk_short_text():
    text = "Short text"
    result = chunk_text(text, chunk_size=500)
    assert len(result) == 1
    assert result[0] == text


def test_chunk_long_text():
    text = "This is a test. " * 100
    result = chunk_text(text, chunk_size=100, overlap=20)
    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= 100 or len(chunk.split()) <= 20


def test_chunk_preserves_word_boundaries():
    text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
    result = chunk_text(text, chunk_size=30, overlap=5)
    for chunk in result:
        assert not chunk.startswith(" ")
        assert not chunk.endswith(" ")
