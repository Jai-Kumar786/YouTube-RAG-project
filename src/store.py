import os
from langchain_core.documents import Document
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings

# Fetch DB connection string from environment variables
# Adjust the default string to match your docker-compose.yml PostgreSQL credentials
DB_CONNECTION_STRING = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://raguser:ragpass@localhost:5433/youtube_rag"
)

def store_documents(docs: list[Document]) -> int:
    """
    Takes LangChain Document objects, generates embeddings using Ollama,
    and stores them in a PostgreSQL database using pgvector.
    """
    print(f"Initializing Ollama embeddings and connecting to PostgreSQL...")
    
    # Step 4: Initialize Ollama Embeddings
    # We use 'nomic-embed-text' as it is highly optimized for vector search
    embeddings = OllamaEmbeddings(model="nomic-embed-text") 
    
    # Step 5: Store in PostgreSQL
    # The from_documents method automatically connects to the DB, creates the pgvector 
    # extension and tables if they don't exist, embeds the text, and inserts the records.
    vector_store = PGVector.from_documents(
        embedding=embeddings,
        documents=docs,
        collection_name="youtube_transcripts",
        connection_string=DB_CONNECTION_STRING,
        pre_delete_collection=False  # Set to True if you want to clear the DB on every ingest
    )
    
    print("Successfully stored documents in pgvector.")
    return len(docs)

def check_video_exists(video_id: str) -> bool:
    """
    Checks if a video has already been ingested by searching for any
    document with the given video_id in its metadata.
    """
    try:
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vector_store = PGVector(
            collection_name="youtube_transcripts",
            connection_string=DB_CONNECTION_STRING,
            embedding_function=embeddings,
        )
        # Search for documents with matching video_id
        results = vector_store.similarity_search(
            "test", k=1, filter={"video_id": video_id}
        )
        return len(results) > 0
    except Exception:
        # If the table doesn't exist yet, the video can't exist
        return False