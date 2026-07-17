from app.utils.text_processing import split_text_into_chunks


def test_chunk_creation():
    text = "Hello world. " * 200

    chunks = split_text_into_chunks(text)

    assert len(chunks) > 1
    assert all(len(chunk) > 0 for chunk in chunks)