import pytest
from src.chunker import chunk_transcript
from dataclasses import dataclass

@dataclass
class Segment:
    text: str
    start: float
    duration: float

def test_chunk_transcript_simple():
    segments = [
        Segment(text="Hello", start=0.0, duration=1.0),
        Segment(text="World", start=1.0, duration=1.0),
    ]
    text = "Hello World"
    # Note: chunker logic assumes text is formed by joining segments with space
    # The chunker adds " " to segment text for length calculation

    docs = chunk_transcript(text, segments, chunk_size=5, chunk_overlap=0)

    # "Hello" length is 5. "World" length is 5.
    # Splitter behavior depends on separators.
    # Should get "Hello" and "World" or similar.

    assert len(docs) > 0
    # verify timestamps
    # First chunk should start at 0.0
    assert docs[0].metadata["start_time"] == 0.0
    # verify content
    assert "Hello" in docs[0].page_content

def test_chunk_transcript_overlap():
    segments = [
        Segment(text="A" * 10, start=0.0, duration=1.0),
        Segment(text="B" * 10, start=1.0, duration=1.0),
    ]
    text = ("A" * 10) + " " + ("B" * 10)

    docs = chunk_transcript(text, segments, chunk_size=10, chunk_overlap=5)

    # Should produce overlapping chunks
    assert len(docs) >= 2
    # Verify times increase
    times = [d.metadata["start_time"] for d in docs]
    assert times == sorted(times)

def test_chunk_transcript_large():
    # Performance check (small scale) to ensure no regressions in logic
    segments = [Segment(text=str(i), start=float(i), duration=1.0) for i in range(100)]
    text = " ".join([s.text for s in segments])

    docs = chunk_transcript(text, segments, chunk_size=10, chunk_overlap=0)
    assert len(docs) > 0
    assert docs[0].metadata["start_time"] == 0.0
    assert docs[-1].metadata["end_time"] >= 99.0 # approximate
