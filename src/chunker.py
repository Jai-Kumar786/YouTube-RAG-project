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

    def find_time_with_hint(pos, start_idx=0, start_cumulative=0):
        # Reset scan from beginning if pos is behind our current search window
        if pos < start_cumulative:
            start_idx = 0
            start_cumulative = 0

        cumulative = start_cumulative
        for i in range(start_idx, len(segments)):
            seg = segments[i]
            seg_text = seg.text + " "
            seg_len = len(seg_text)
            if pos < cumulative + seg_len:
                return seg.start, i, cumulative
            cumulative += seg_len

        # If not found (beyond end of segments), return end time of last segment
        val = segments[-1].start + segments[-1].duration if segments else 0
        return val, len(segments), cumulative

    documents: list[Document] = []
    search_start_idx = 0
    search_start_cum = 0

    for idx, chunk_text in enumerate(raw_chunks):
        token_count = len(encoder.encode(chunk_text))
        start_pos = text.find(chunk_text)  # approximate

        start_time, found_idx, found_cum = find_time_with_hint(
            start_pos, search_start_idx, search_start_cum
        )
        # Update hint for next chunk's start_time search
        search_start_idx = found_idx
        search_start_cum = found_cum

        # For end_time, start search from where start_time was found
        end_time, _, _ = find_time_with_hint(
            start_pos + len(chunk_text), found_idx, found_cum
        )

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
