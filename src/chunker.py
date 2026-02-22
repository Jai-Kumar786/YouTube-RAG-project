"""
Chunking & tokenization — splits a transcript into overlapping chunks
with token-count metadata.
"""
from __future__ import annotations

import tiktoken
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

    # Cache the last found segment index and cumulative length
    # This optimizes sequential lookups from O(N*M) to O(N+M)
    search_state = {"index": 0, "cumulative": 0}

    def find_time(pos):
        idx = search_state["index"]
        cumulative = search_state["cumulative"]

        # If we went backwards, reset search
        if pos < cumulative:
            idx = 0
            cumulative = 0

        for i in range(idx, len(segments)):
            seg = segments[i]
            # +1 for the space that was used during ingestion
            seg_len = len(seg.text) + 1

            if pos < cumulative + seg_len:
                # Update state to current segment start for next call
                search_state["index"] = i
                search_state["cumulative"] = cumulative
                return seg.start

            cumulative += seg_len

        # If not found, update state to end
        search_state["index"] = len(segments)
        search_state["cumulative"] = cumulative
        return segments[-1].start + segments[-1].duration if segments else 0

    documents: list[Document] = []
    for idx, chunk_text in enumerate(raw_chunks):
        token_count = len(encoder.encode(chunk_text))
        start_pos = text.find(chunk_text)  # approximate
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
