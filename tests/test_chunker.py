import pytest
from src.chunker import chunk_transcript

class MockSegment:
    def __init__(self, text, start, duration):
        self.text = text
        self.start = start
        self.duration = duration

def test_chunk_transcript_simple():
    segments = [
        MockSegment("Hello", 0.0, 1.0),
        MockSegment("world.", 1.0, 1.0),
        MockSegment("This", 2.0, 1.0),
        MockSegment("is", 3.0, 0.5),
        MockSegment("a", 3.5, 0.5),
        MockSegment("test.", 4.0, 1.0)
    ]
    # Ingest creates text by joining segments with space.
    full_text = " ".join(seg.text for seg in segments)

    # We test chunking with small chunk size to force splits
    chunks = chunk_transcript(full_text, segments, chunk_size=10, chunk_overlap=0)

    assert len(chunks) > 0
    # Verify metadata contains start_time and end_time
    for chunk in chunks:
        assert "start_time" in chunk.metadata
        assert "end_time" in chunk.metadata
        # Check reasonable values
        assert chunk.metadata["start_time"] >= 0.0
        assert chunk.metadata["end_time"] >= chunk.metadata["start_time"]

        # Verify specific values for first chunk
        if chunk.metadata["chunk_index"] == 0:
            # "Hello worl" -> starts at 0.0
            assert chunk.metadata["start_time"] == 0.0

def test_chunk_transcript_edge_cases():
    segments = [
        MockSegment("A", 0.0, 1.0),
    ]
    full_text = "A"
    chunks = chunk_transcript(full_text, segments, chunk_size=10, chunk_overlap=0)
    assert len(chunks) == 1
    assert chunks[0].metadata["start_time"] == 0.0
    # Existing behavior returns start time of the segment containing the position.
    # Since position 1 is within "A " (length 2), it returns start time of segment 1.
    assert chunks[0].metadata["end_time"] == 0.0
