# Sanjivi AI — Multi-Agent AYUSH RAG Backend

Production-quality FastAPI + LangGraph + Pinecone hybrid RAG backend for Sanjivi AI.

---

## Features

- **Multi-Agent Orchestration**: Powered by LangGraph StateGraph workflow.
- **Emergency Screening**: Real-time screening of life-threatening symptoms before any traditional therapeutics are run. Bypasses execution to generate nearby hospital recommendations via Google Places API.
- **Parallel Experts**: Runs 5 AYUSH specialist Small Language Models (SLMs) in parallel via `asyncio.gather` for minimal latency.
- **Hybrid RAG Retrieval**:
  - Sparse retrieval using BM25+ (`bm25s` library).
  - Dense vector retrieval using `BAAI/bge-small-en-v1.5` embeddings stored in Pinecone.
  - Fusion of results using Reciprocal Rank Fusion (RRF).
- **Consensus & Reviewer**: Synthesises suggestions, resolves conflicts, validates clinical safety, and formatting output to plain prose before returning response.
- **Dynamic Image Search**: Google Custom Search Engine automatically fetches pose images for Yoga recommendations.

---

## Installation & Setup

1. **Prerequisites**: Python 3.12, Pinecone account, Groq account, Tavily account, Google Cloud Console account.
2. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in the required keys:
   ```bash
   cp .env.example .env
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Ingest Reference Data**:
   To parse, chunk, embed, and index all documents under `data/` directories, run:
   ```bash
   python -m app.rag.ingest
   ```

---

## Running the Server

Start the Uvicorn development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Documentation

Interactive OpenAPI documentation is available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Deployment (Hugging Face / Docker)

Build and run using Docker:
```bash
docker build -t sanjivi-backend .
docker run -p 8000:8000 --env-file .env sanjivi-backend
```
