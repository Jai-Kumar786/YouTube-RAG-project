import pytest
from dataclasses import dataclass
from src.chunker import chunk_transcript

@dataclass
class MockSegment:
    text: str
    start: float
    duration: float

def test_empty_input():
    """Test with empty text and empty segments."""
    documents = chunk_transcript("", [])
    assert documents == []

def test_text_without_segments():
    """Test with text but empty segments."""
    text = "Hello world"
    # Expected behavior: find_time returns 0 if segments is empty
    documents = chunk_transcript(text, [])
    assert len(documents) > 0
    assert documents[0].page_content == "Hello world"
    assert documents[0].metadata["start_time"] == 0
    assert documents[0].metadata["end_time"] == 0

def test_small_chunks():
    """Test splitting when text is larger than chunk size."""
    text = "This is a long sentence that should be split into multiple chunks."
    segments = [MockSegment(text, 0.0, 10.0)]
    # chunk_size=10, overlap=0
    documents = chunk_transcript(text, segments, chunk_size=10, chunk_overlap=0)
    assert len(documents) > 1
    # Verify content length roughly
    for doc in documents:
        assert len(doc.page_content) <= 10

def test_exact_size():
    """Test when text is exactly the chunk size."""
    text = "1234567890"
    segments = [MockSegment(text, 0.0, 1.0)]
    documents = chunk_transcript(text, segments, chunk_size=10, chunk_overlap=0)
    assert len(documents) == 1
    assert documents[0].page_content == "1234567890"

def test_overlap():
    """Test chunk overlap."""
    text = "1234567890"
    segments = [MockSegment(text, 0.0, 1.0)]
    # chunk_size=6, overlap=2
    # With no separators in text, it splits by character
    documents = chunk_transcript(text, segments, chunk_size=6, chunk_overlap=2)
    assert len(documents) >= 2

    # Check content of chunks
    content = [d.page_content for d in documents]
    # "123456"
    assert "123456" in content[0]
    # "567890" (overlap "56")
    if len(documents) > 1:
        assert "567890" in content[1]

def test_unicode():
    """Test with unicode characters."""
    text = "こんにちは世界" # "Hello World" in Japanese
    segments = [MockSegment(text, 0.0, 1.0)]
    documents = chunk_transcript(text, segments)
    assert len(documents) > 0
    assert documents[0].page_content == text

def test_source_url():
    """Verify source_url in metadata."""
    text = "test"
    segments = [MockSegment("test", 0.0, 1.0)]
    url = "http://youtube.com/watch?v=123"
    documents = chunk_transcript(text, segments, source_url=url)
    assert documents[0].metadata["source_url"] == url

def test_segments_mismatch():
    """Test when segments don't cover the full text."""
    text = "Hello world extra"
    segments = [MockSegment("Hello world", 0.0, 2.0)] # Covers first 11 chars
    # "extra" starts at pos 12.
    # find_time loop will finish.
    # Should return segments[-1].start + segments[-1].duration

    documents = chunk_transcript(text, segments)
    last_doc = documents[-1]
    # Check start/end time of the chunk containing "extra"
    # It should be >= 2.0 (start + duration of last segment)
    assert last_doc.metadata["end_time"] >= 2.0
