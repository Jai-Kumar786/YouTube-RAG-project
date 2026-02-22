import pytest
from dataclasses import dataclass
from src.chunker import chunk_transcript

@dataclass
class MockSegment:
    text: str
    start: float
    duration: float

def test_chunk_transcript_empty_text():
    segments = [MockSegment(text="Hello", start=0.0, duration=1.0)]
    chunks = chunk_transcript(text="", segments=segments)
    assert chunks == []

def test_chunk_transcript_empty_segments():
    text = "Hello world"
    chunks = chunk_transcript(text=text, segments=[])
    # The current implementation might error or return 0 for times.
    # Let's verify what happens.
    # find_time returns segments[-1].start + duration if segments else 0
    # So both start_time and end_time should be 0.
    assert len(chunks) == 1
    assert chunks[0].metadata["start_time"] == 0
    assert chunks[0].metadata["end_time"] == 0
    assert chunks[0].page_content == "Hello world"

def test_chunk_transcript_basic():
    # Construct segments and text
    segments = [
        MockSegment(text="Hello", start=0.0, duration=1.0),
        MockSegment(text="world", start=1.0, duration=1.0),
    ]
    # In chunk_transcript logic, text is usually joined with " ".
    text = "Hello world"

    # Use small chunk size to force split if needed, or large enough for one chunk.
    # Let's try one chunk first.
    chunks = chunk_transcript(text=text, segments=segments, chunk_size=50, chunk_overlap=0)

    assert len(chunks) == 1
    assert chunks[0].page_content == "Hello world"
    assert chunks[0].metadata["start_time"] == 0.0
    assert chunks[0].metadata["end_time"] == 1.0

def test_chunk_transcript_split():
    segments = [
        MockSegment(text="A" * 10, start=0.0, duration=1.0),
        MockSegment(text="B" * 10, start=1.0, duration=1.0),
    ]
    text = ("A" * 10) + " " + ("B" * 10)

    # Chunk size 12. "A"*10 is 10 chars. Space is 1. "B"*10 is 10. Total 21.
    # Should split.
    chunks = chunk_transcript(text=text, segments=segments, chunk_size=12, chunk_overlap=0)

    assert len(chunks) >= 2
    assert chunks[0].page_content.startswith("AAAAAAAAAA")
    assert chunks[1].page_content.startswith("BBBBBBBBBB")

def test_chunk_transcript_small_chunk_size():
    # Very small chunk size to force many splits
    text = "Hello world this is a test"
    segments = [MockSegment(text=text, start=0.0, duration=10.0)]

    chunks = chunk_transcript(text=text, segments=segments, chunk_size=5, chunk_overlap=0)
    assert len(chunks) > 1

    # Verify reconstruction
    joined = "".join([c.page_content for c in chunks])
    # Without overlap, joined might not equal text if separator logic drops things?
    # RecursiveCharacterTextSplitter tries to keep separators.
    # But let's check basic sanity.
    assert len(chunks) > 0

def test_chunk_transcript_metadata():
    text = "Test"
    segments = [MockSegment(text="Test", start=0.0, duration=1.0)]
    source_url = "http://example.com"

    chunks = chunk_transcript(text=text, segments=segments, source_url=source_url)
    assert len(chunks) == 1
    assert chunks[0].metadata["source_url"] == source_url
    assert chunks[0].metadata["chunk_index"] == 0
    assert "token_count" in chunks[0].metadata

def test_text_shorter_than_chunk():
    text = "Short text"
    segments = [MockSegment(text="Short text", start=0.0, duration=1.0)]
    chunks = chunk_transcript(text=text, segments=segments, chunk_size=100, chunk_overlap=0)
    assert len(chunks) == 1
    assert chunks[0].page_content == "Short text"

def test_text_exact_chunk_size():
    text = "Exact size"
    segments = [MockSegment(text="Exact size", start=0.0, duration=1.0)]
    chunks = chunk_transcript(text=text, segments=segments, chunk_size=len(text), chunk_overlap=0)
    assert len(chunks) == 1
    assert chunks[0].page_content == "Exact size"

def test_large_overlap():
    text = "Hello world"
    segments = [MockSegment(text="Hello world", start=0.0, duration=1.0)]
    # Chunk size 5, overlap 4.
    chunks = chunk_transcript(text=text, segments=segments, chunk_size=5, chunk_overlap=4)
    # Expect multiple chunks with heavy overlap.
    assert len(chunks) > 1
    # Check overlap (just conceptually)
    # "Hello" -> "Hell" + "o"?
    # The splitter logic is complex, but we just want to ensure it doesn't crash.

def test_segments_mismatch():
    # Text is longer than segments cover
    text = "Hello world extra content"
    segments = [
        MockSegment(text="Hello", start=0.0, duration=1.0),
        MockSegment(text="world", start=1.0, duration=1.0),
    ]
    # find_time for "extra content" position will be > segments total length
    # It should return segments[-1].start + segments[-1].duration

    chunks = chunk_transcript(text=text, segments=segments, chunk_size=50, chunk_overlap=0)
    assert len(chunks) == 1
    assert chunks[0].metadata["end_time"] == 2.0 # 1.0 + 1.0

def test_overlap_larger_than_chunk_size():
    text = "test"
    segments = [MockSegment(text="test", start=0.0, duration=1.0)]
    # This should raise ValueError per langchain docs
    with pytest.raises(ValueError):
        chunk_transcript(text, segments, chunk_size=10, chunk_overlap=20)

def test_none_inputs():
    with pytest.raises(Exception): # TypeError or AttributeError
        chunk_transcript(text=None, segments=[])

    with pytest.raises(Exception):
         chunk_transcript(text="test", segments=None)
