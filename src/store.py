"""
Embedding & storage — embeds chunks via Ollama and stores them in
PostgreSQL with pgvector.
"""
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import psycopg2
from psycopg2.extras import execute_values
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv

if TYPE_CHECKING:
    from langchain_core.documents import Document

load_dotenv()

EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it in .env file or environment.")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def _get_connection():
    """Return a new psycopg2 connection."""
    return psycopg2.connect(DATABASE_URL)


def init_db() -> None:
    """Create the pgvector extension and transcript_chunks table if they don't exist."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS transcript_chunks (
                    id          SERIAL PRIMARY KEY,
                    content     TEXT NOT NULL,
                    embedding   vector({EMBEDDING_DIM}),
                    metadata    JSONB DEFAULT '{{}}'::jsonb
                );
            """)
            # Create an IVFFlat index for faster cosine search (if enough rows)
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = 'idx_chunks_embedding'
                    ) THEN
                        CREATE INDEX idx_chunks_embedding
                        ON transcript_chunks
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    END IF;
                END $$;
            """)
        conn.commit()
    finally:
        conn.close()


def _get_embeddings_model() -> OllamaEmbeddings:
    """Return an OllamaEmbeddings instance."""
    return OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using Ollama and return the vectors."""
    model = _get_embeddings_model()
    return model.embed_documents(texts)


def embed_and_store(chunks: list[Document]) -> int:
    """
    Embed a list of Document chunks and bulk-insert them into PostgreSQL.
    Returns the number of rows inserted.
    """
    if not chunks:
        return 0

    texts = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]

    vectors = embed_texts(texts)

    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            rows = [
                (text, vec, json.dumps(meta))
                for text, vec, meta in zip(texts, vectors, metadatas)
            ]
            execute_values(
                cur,
                """
                INSERT INTO transcript_chunks (content, embedding, metadata)
                VALUES %s
                """,
                rows,
                template="(%s, %s::vector, %s::jsonb)",
            )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def clear_chunks() -> None:
    """Delete all rows from transcript_chunks (useful for re-ingesting)."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE transcript_chunks RESTART IDENTITY;")
        conn.commit()
    finally:
        conn.close()
