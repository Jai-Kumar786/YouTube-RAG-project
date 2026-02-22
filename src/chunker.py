"""
Chunking & tokenization — splits a transcript into overlapping chunks
with token-count metadata.
"""
from __future__ import annotations

import tiktoken
from bisect import bisect_right
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def chunk_transcript(
    text: str,
    segments: list,
    source_url: str = "",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Document]:
    """
    Split transcript text into overlapping Document chunks.

    Each chunk carries metadata:
      - source_url: original YouTube URL
      - chunk_index: position in the sequence
      - token_count: token length (cl100k_base encoding)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_text(text)
    encoder = tiktoken.get_encoding("cl100k_base")

    # Precompute segment boundaries for faster lookup (O(M))
    segment_ends = []
    cumulative = 0
    for seg in segments:
        cumulative += len(seg.text) + 1  # +1 for the space added during ingestion
        segment_ends.append(cumulative)

    def find_time(pos):
        """Find the start time of the segment containing the given character position."""
        if not segments:
            return 0

        # Binary search for the segment index (O(log M))
        idx = bisect_right(segment_ends, pos)

        if idx < len(segments):
            return segments[idx].start

        # If position is beyond the last segment, return the end time of the last segment
        last_seg = segments[-1]
        return last_seg.start + last_seg.duration

    documents: list[Document] = []
    search_start = 0
    for idx, chunk_text in enumerate(raw_chunks):
        token_count = len(encoder.encode(chunk_text))

        # Optimized search: start looking from where the previous chunk started
        start_pos = text.find(chunk_text, search_start)

        # Fallback: if not found (e.g. text normalization mismatch), search from beginning
        if start_pos == -1:
            start_pos = text.find(chunk_text)

        # Update search_start for the next iteration to avoid O(N^2) behavior
        if start_pos != -1:
            search_start = start_pos + 1

        start_time = find_time(start_pos)
        end_time = find_time(start_pos + len(chunk_text))

        doc = Document(
            page_content=chunk_text,
            metadata={
                "source_url": source_url,
                "chunk_index": idx,
                "token_count": token_count,
                "start_time": start_time,
                "end_time": end_time,
            },
        )
        documents.append(doc)

    return documents
