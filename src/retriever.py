"""
Retrieval — semantic search over stored transcript chunks.
"""
from __future__ import annotations

import os
import psycopg2
from dotenv import load_dotenv

from src.store import embed_texts

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://raguser:ragpass@localhost:5433/youtube_rag")


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Embed the user query and return the top-k most similar transcript chunks
    using cosine distance (<=> operator) in pgvector.

    Returns a list of dicts with keys: id, content, metadata, score.
    """
    # Embed the query
    query_vector = embed_texts([query])[0]

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, content, metadata,
                       1 - (embedding <=> %s::vector) AS score
                FROM transcript_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (query_vector, query_vector, top_k),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "content": row[1],
            "metadata": row[2],
            "score": round(float(row[3]), 4),
        })
    return results
