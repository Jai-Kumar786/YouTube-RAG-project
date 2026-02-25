from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional
from dotenv import load_dotenv
import uvicorn
import logging

# Load environment variables from .env file
load_dotenv()

# Import our custom modules from the src directory
from src.ingest import extract_video_id, fetch_youtube_transcript
from src.chunker import chunk_text
from src.store import store_documents, check_video_exists, delete_video_chunks, delete_all_chunks
from src.retriever import retrieve_context
from src.generator import generate_answer, generate_video_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI application
app = FastAPI(
    title="YouTube RAG API",
    description="Backend for ingesting YouTube transcripts and answering queries using RAG.",
    version="1.0.0"
)

# ---------------------------------------------------------
# CORS Middleware — allows frontend apps to call this API
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    title: str = "Untitled Video"
    suggested_questions: list[str] = []

class AskRequest(BaseModel):
    question: str
    video_id: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    sources: list[str] = []

class DeleteResponse(BaseModel):
    message: str
    deleted_count: int

class HealthResponse(BaseModel):
    status: str
    database: str
    message: str

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

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the API and database are operational.
    """
    try:
        from sqlalchemy import create_engine, text
        from src.store import DB_CONNECTION_STRING
        engine = create_engine(DB_CONNECTION_STRING)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return HealthResponse(status="healthy", database="connected", message="All systems operational.")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(status="unhealthy", database="disconnected", message=f"Database error: {str(e)}")

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
    
    # Step 1.5 - Delete old chunks if video was previously ingested
    if check_video_exists(video_id):
        logger.info(f"Video {video_id} already exists, deleting old chunks before re-ingest...")
        delete_video_chunks(video_id)
        
    # Step 2 - Download transcript
    logger.info(f"Fetching transcript for video: {video_id}")
    transcript_text = fetch_youtube_transcript(video_id)
    if not transcript_text:
        raise HTTPException(
            status_code=404, 
            detail="Transcript not found or subtitles are disabled for this video."
        )
        
    # Step 3 - Chunking
    chunks = chunk_text(transcript_text, video_id)
    logger.info(f"Created {len(chunks)} chunks for video {video_id}")
    
    # Step 4 & 5 - Generate embeddings and Store (PostgreSQL)
    try:
        num_chunks = store_documents(chunks)
    except Exception as e:
        logger.error(f"Failed to store embeddings for {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store embeddings: {str(e)}")
    
    logger.info(f"Successfully ingested video {video_id} with {num_chunks} chunks.")
    
    # Step 6 - Generate title and suggested questions from transcript
    logger.info(f"Generating title and questions for {video_id}...")
    summary = generate_video_summary(transcript_text)
    
    return IngestResponse(
        message="Transcript fetched, chunked, embedded, and stored successfully!",
        video_id=video_id,
        chunks_created=num_chunks,
        title=summary["title"],
        suggested_questions=summary["suggested_questions"]
    )

@app.delete("/videos", response_model=DeleteResponse)
async def clear_all_videos():
    """
    Deletes ALL stored video chunks from the database.
    Use this to start fresh before ingesting new videos.
    """
    logger.info("Clearing all video chunks from the database...")
    deleted = delete_all_chunks()
    logger.info(f"Deleted {deleted} chunks.")
    return DeleteResponse(
        message=f"Successfully deleted all video data ({deleted} chunks removed).",
        deleted_count=deleted
    )

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Receives a user question, performs a similarity search in PostgreSQL,
    and generates an answer using the configured LLM.
    """
    try:
        # Step 1 & 2 - Generate embedding for the question and perform similarity search
        logger.info(f"Processing question: {request.question[:80]}...")
        context_docs = retrieve_context(request.question, video_id=request.video_id)
        
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
        logger.error(f"Failed to process query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)