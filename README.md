# Enterprise RAG System

Enterprise RAG app for uploading PDF/TXT files and chatting with grounded answers.
Backend is FastAPI + Celery + PostgreSQL + Redis + Pinecone, with local Ollama for LLM generation.

## Flow (2 lines)
1. Upload -> worker parses/chunks -> embedding service creates vectors -> Pinecone stores/searches chunks.
2. Chat query -> retrieval (embed + search + rerank) -> Ollama streams answer via SSE with sources.

## Project docs
- Design docs: `docs/desing-docs/`
- Implementation phases: `docs/implementation-plan/`

## Prerequisites
- Docker + Docker Compose
- Node.js 20+ (for local frontend)
- Python 3.11+ (only if running backend outside Docker)
- Ollama (for local LLM)
- Pinecone API key + index settings in `.env`

## Environment
Create root env file:

```bash
cp .env.example .env
```

Minimum values to verify in `.env`:
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_HOST`
- `LLM_SERVICE_URL`
- `NEXT_PUBLIC_API_URL`

## Option A: Docker-first (recommended)
Start all services (backend, worker, db, redis, ml services, frontend):

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
docker compose up -d
```

Run migrations:

```bash
docker compose exec backend alembic -c /app/alembic.ini upgrade head
```

Start Ollama on host (outside Docker):

```bash
ollama serve
ollama pull llama3.1:8b
```

Access:
- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

## Option B: Local frontend + Docker backend (common dev mode)
Start backend side in Docker:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
docker compose up -d postgres redis backend worker embedding-service reranker-service
```

Run frontend locally:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system/frontend
npm install
npm run dev
```

If `3000` is busy, Next uses another port (for example `3002` or `3003`).
Update backend CORS and `NEXT_PUBLIC_API_URL` to match your actual frontend origin.

## Option C: Mostly local (advanced)
You can run backend/frontend locally and keep only infra in Docker, but this needs local Python env setup and matching URLs.
Use only if you specifically want non-container runtime debugging.

## Model download details
### 1) LLM model (Ollama)
Manual one-time pull:

```bash
ollama serve
ollama pull llama3.1:8b
curl http://localhost:11434/v1/models
```

When backend runs in Docker, use host URL in `.env`:
- `LLM_SERVICE_URL=http://host.docker.internal:11434/v1`

When backend runs locally:
- `LLM_SERVICE_URL=http://localhost:11434/v1`

### 2) Embedding model (`BAAI/bge-m3`)
- Downloaded automatically on first embedding-service startup/request.
- Cache volume is mounted at `./data/models` (via `/data/models` in container).
- First load can take a few minutes.

Check readiness:

```bash
curl http://localhost:8001/health
```

### 3) Reranker model (`BAAI/bge-reranker-v2-m3`)
- Downloaded automatically on first reranker-service startup/request.
- May take several minutes on first load or after rebuilds.

Check readiness:

```bash
curl http://localhost:8002/health
curl -X POST http://localhost:8002/rerank \
  -H "Content-Type: application/json" \
  -d '{"query":"what is chunking?","documents":["chunking splits docs","redis is cache"],"top_k":2}'
```

## Health and smoke checks
Quick health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/deep
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:11434/v1/models
```

Project smoke script:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
./scripts/smoke_check.sh
```

## Common issues
### Upload returns 422 or network error in browser
- Ensure frontend origin (for example `http://localhost:3002`) is included in backend `cors_origins`.
- Do not force `multipart/form-data` header manually for `FormData` uploads.

### Frontend starts on a different port
- Port `3000` is already in use.
- Stop old Next processes or run explicitly on `3000`:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system/frontend
npm run dev -- -p 3000
```

### Retrieval/chat works but responses are empty
- Confirm document status is `completed`.
- Confirm embedding/reranker health both show `model_status: ready`.
- Confirm Pinecone index contains vectors.

## Helpful commands
```bash
# Start everything
docker compose up -d

# Tail logs
docker compose logs -f backend
docker compose logs -f worker

# Stop stack
docker compose down
```

## License
MIT (see `LICENSE`).
