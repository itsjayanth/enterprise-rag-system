# Development Setup Guide

A quick daily-use setup guide for working on the Enterprise RAG MVP.

---

## ✅ Recommended Local Workflow

Use a hybrid development setup:

- run infrastructure with Docker Compose (Postgres, Redis)
- run ML embedding and reranker services in Docker (CPU, no GPU needed)
- run LLM via **Ollama on the host** (not in Docker) — CPU/Apple MPS
- run backend/frontend locally for faster iteration
- Pinecone is cloud-only — set `PINECONE_API_KEY` in `.env`

**No GPU required.** The entire stack runs on your local Mac CPU.
Apple Silicon Macs will be faster for LLM inference via Apple MPS.

---

## 0. Prerequisites (one-time)

```bash
# Install tools
brew install python@3.11 node@20 ollama docker

# Pull the LLM model (~4.7 GB)
ollama pull llama3.1:8b
```

---

## 1. Start infrastructure

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
cp .env.example .env
# Edit .env — add PINECONE_API_KEY and PINECONE_ENVIRONMENT
make dev-infra
```

This starts:

- PostgreSQL
- Redis

---

## 1b. Start Ollama (LLM — host process, not Docker)

```bash
# In a separate terminal tab
ollama serve
```

Verify it's working:

```bash
curl http://localhost:11434/v1/models
```

---

## 2. Run backend locally

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
python3.11 -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. Run the worker locally or in Docker

### Local worker

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
source venv/bin/activate
cd backend
celery -A workers.celery_app worker --loglevel=info
```

### Or Docker worker

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
docker compose up -d worker
```

---

## 4. Run ML services

### Embedding service

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
docker compose up -d embedding-service
```

### Reranker service

```bash
docker compose up -d reranker-service
```

### LLM service

**Ollama runs on the host — not in Docker.**

```bash
# Already started in step 1b
# Test:
curl http://localhost:11434/v1/models
```

**When backend is inside Docker**, set in `.env`:
```bash
LLM_SERVICE_URL=http://host.docker.internal:11434/v1
```

**When backend is running locally (outside Docker)**, set in `.env`:
```bash
LLM_SERVICE_URL=http://localhost:11434/v1
```

> Future GPU upgrade: replace Ollama with `docker compose up -d llm-service` (vLLM).

---

## 5. Run frontend locally

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system/frontend
npm install
npm run dev
```

---

## 6. Quick verification checklist

```bash
curl http://localhost:8000/health        # Backend
curl http://localhost:8001/health        # Embedding service
curl http://localhost:8002/health        # Reranker service
curl http://localhost:11434/v1/models    # Ollama LLM (host)
```

Open:

```text
http://localhost:3000
```

---

## 7. Useful commands

```bash
make logs
make logs-backend
make logs-worker
make stop
make clean
```

---

## 8. Minimal end-to-end smoke test

1. upload a PDF/TXT from the UI or API
2. wait until document status is `completed`
3. call retrieval or chat
4. verify sources are returned

---

## 9. When to use full Docker mode

Use `make dev` when you want the whole stack running together and want fewer differences between local and containerized behavior.

---

**Status:** ✅ Quick development guide ready

