# 🎬 YouTube RAG Pipeline

Ask questions about any YouTube video using **Retrieval-Augmented Generation** (RAG) powered by local Ollama models and PostgreSQL + pgvector.

## Architecture

```
YouTube URL → Transcript Extraction → Text Chunking → Embedding (Ollama) → pgvector Storage
                                                                                    ↓
User Question → Query Embedding → Similarity Search → Context Retrieval → LLM Answer
```

## Tech Stack

- **FastAPI** — REST API framework
- **LangChain** — Orchestration (chunking, embeddings, LLM chains)
- **Ollama** — Local LLM & embedding models (`nomic-embed-text`, `deepseek-v3.1`)
- **PostgreSQL + pgvector** — Vector database for semantic search
- **Docker Compose** — Database provisioning

## Quick Start

### 1. Prerequisites

- [Python 3.10+](https://python.org)
- [Docker Desktop](https://docker.com/products/docker-desktop)
- [Ollama](https://ollama.ai) installed and running

### 2. Pull Required Ollama Models

```bash
ollama pull nomic-embed-text
ollama pull deepseek-v3.1:671b-cloud
```

### 3. Start the Database

```bash
docker compose up -d
```

### 4. Install Dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 5. Configure Environment

```bash
copy .env.example .env
# Edit .env if you changed any database credentials
```

### 6. Run the API

```bash
python main.py
```

The API will be available at **http://localhost:8000** and Swagger docs at **http://localhost:8000/docs**.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/`      | Welcome message |
| `GET`  | `/health`| Health check (DB connectivity) |
| `POST` | `/ingest`| Ingest a YouTube video transcript |
| `POST` | `/ask`   | Ask a question about ingested videos |

### Ingest a Video

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Ask a Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the video?"}'
```

## Project Structure

```
youtube-rag/
├── main.py              # FastAPI app with all endpoints
├── src/
│   ├── ingest.py        # YouTube URL parsing & transcript download
│   ├── chunker.py       # Text splitting with LangChain
│   ├── store.py         # Embedding generation & pgvector storage
│   ├── retriever.py     # Similarity search against pgvector
│   └── generator.py     # LLM-powered answer generation
├── docker-compose.yml   # PostgreSQL + pgvector container
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project metadata
└── .env.example         # Environment variable template
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg2://raguser:ragpass@localhost:5433/youtube_rag` | PostgreSQL connection string |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `LLM_MODEL` | `deepseek-v3.1:671b-cloud` | LLM model for answer generation |

## License

MIT
