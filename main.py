from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import uvicorn

# Import our custom modules from the src directory
from src.ingest import extract_video_id, fetch_youtube_transcript
from src.chunker import chunk_text
from src.store import store_documents
from src.retriever import retrieve_context
from src.generator import generate_answer

# Initialize the FastAPI application
app = FastAPI(
    title="YouTube RAG API",
    description="Backend for ingesting YouTube transcripts and answering queries using RAG.",
    version="1.0.0"
)

# ---------------------------------------------------------
# Pydantic Models for Data Validation
# ---------------------------------------------------------

class IngestRequest(BaseModel):
    youtube_url: HttpUrl

class IngestResponse(BaseModel):
    message: str
    video_id: str
    chunks_created: int

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: list[str] = []

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/")
async def root():
    """
    Root endpoint to verify the API is running.
    """
    return {
        "message": "Welcome to the YouTube RAG API! Please navigate to /docs to use the Swagger UI.",
        "docs_url": "http://localhost:8000/docs"
    }

@app.post("/ingest", response_model=IngestResponse)
async def ingest_video(request: IngestRequest):
    """
    Receives a YouTube URL, extracts the transcript, chunks the text,
    generates embeddings, and stores them in PostgreSQL via pgvector.
    """
    url_str = str(request.youtube_url)
    
    # Step 1 - Extract Video ID
    video_id = extract_video_id(url_str)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL provided.")
        
    # Step 2 - Download transcript
    transcript_text = fetch_youtube_transcript(video_id)
    if not transcript_text:
        raise HTTPException(
            status_code=404, 
            detail="Transcript not found or subtitles are disabled for this video."
        )
        
    # Step 3 - Chunking
    chunks = chunk_text(transcript_text, video_id)
    
    # Step 4 & 5 - Generate embeddings and Store (PostgreSQL)
    try:
        num_chunks = store_documents(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store embeddings: {str(e)}")
    
    return IngestResponse(
        message="Transcript fetched, chunked, embedded, and stored successfully!",
        video_id=video_id,
        chunks_created=num_chunks
    )

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Receives a user question, performs a similarity search in PostgreSQL,
    and generates an answer using the configured LLM.
    """
    try:
        # Step 1 & 2 - Generate embedding for the question and perform similarity search
        context_docs = retrieve_context(request.question)
        
        if not context_docs:
            return AskResponse(
                answer="No relevant transcripts found in the database. Please ingest some videos first.",
                sources=[]
            )
            
        # Extract unique sources (video IDs) from metadata to return to the frontend
        sources = list(set([doc.metadata.get("video_id", "Unknown") for doc in context_docs]))
        
        # Step 3 - Pass context and question to the LLM via LangChain
        answer = generate_answer(request.question, context_docs)
        
        return AskResponse(
            answer=answer,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)