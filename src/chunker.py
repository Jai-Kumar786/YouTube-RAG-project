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

    def find_time(pos):
        cumulative = 0
        for seg in segments:
            seg_text = seg.text + " "
            if pos < cumulative + len(seg_text):
                return seg.start
            cumulative += len(seg_text)
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
