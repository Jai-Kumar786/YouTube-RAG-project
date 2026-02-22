import os
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

# Match the DB connection string from store.py
DB_CONNECTION_STRING = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
)

def retrieve_context(question: str, top_k: int = 4) -> list[Document]:
    """
    Embeds the user question and performs a similarity search 
    against the pgvector database to find relevant transcript chunks.
    """
    print(f"Embedding question and searching pgvector for top {top_k} matches...")
    
    # Must use the exact same embedding model used during ingestion!
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Connect to the existing pgvector collection
    vector_store = PGVector(
        collection_name="youtube_transcripts",
        connection_string=DB_CONNECTION_STRING,
        embedding_function=embeddings,
    )
    
    # Perform similarity search
    results = vector_store.similarity_search(question, k=top_k)
    return results