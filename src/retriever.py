import os
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

# Match the DB connection string from store.py
DB_CONNECTION_STRING = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://raguser:ragpass@localhost:5433/youtube_rag"
)

def retrieve_context(question: str, top_k: int = 4, video_id: str | None = None) -> list[Document]:
    """
    Embeds the user question and performs a similarity search 
    against the pgvector database to find relevant transcript chunks.
    Optionally filters by video_id to scope results to a single video.
    """
    filter_msg = f" (filtered to {video_id})" if video_id else ""
    print(f"Embedding question and searching pgvector for top {top_k} matches{filter_msg}...")
    
    # Must use the exact same embedding model used during ingestion!
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Connect to the existing pgvector collection
    vector_store = PGVector(
        collection_name="youtube_transcripts",
        connection_string=DB_CONNECTION_STRING,
        embedding_function=embeddings,
        use_jsonb=True,
    )
    
    # Perform similarity search
    if video_id:
        # Fetch extra results and filter in Python to avoid JSON vs JSONB
        # column incompatibility with PGVector's SQL-level filter
        results = vector_store.similarity_search(question, k=top_k * 5)
        results = [
            doc for doc in results
            if doc.metadata.get("video_id") == video_id
        ][:top_k]
    else:
        results = vector_store.similarity_search(question, k=top_k)
    return results