# Phase 3: FastAPI Core

**Goal:** Stand up the backend application foundation with configuration loading, structured logging, request tracing, router registration, and health checks.

**Duration:** 2-3 hours

**Dependencies:**
- `03-phase-02-database.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ Centralized application settings
- ✅ A working FastAPI app entry point
- ✅ Structured JSON logging
- ✅ Correlation IDs on every request
- ✅ Basic and deep health check endpoints
- ✅ Router wiring for future phases

---

## 📂 Files to Create or Update

```text
backend/app/
├── config.py
├── main.py
├── routes/
│   └── __init__.py
└── utils/
    ├── logging_config.py
    └── tracing.py
```

---

## 🧭 Design Decisions for This Phase

Keep the FastAPI app simple but production-aware:

- single backend service for the MVP
- no auth middleware yet
- CORS enabled for the local frontend
- structured logs from day one
- tracing via correlation/request IDs
- health checks for PostgreSQL, Redis, and later external ML services

This gives you a stable base for all later phases.

---

## ⚙️ Step 1: Create `backend/app/config.py`

Use `pydantic-settings` to load environment variables from the repo root `.env`.

### Include settings for

- database
- redis
- pinecone
- storage paths
- ML service URLs
- retrieval limits
- backend host/port
- environment and log level
- CORS origins

### Recommended fields

```python
class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str
    redis_url: str

    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "enterprise-rag"

    upload_dir: str = "./data/uploads"
    model_cache_dir: str = "./data/models"
    max_upload_size_mb: int = 50

    embedding_service_url: str = "http://embedding-service:8001"
    reranker_service_url: str = "http://reranker-service:8002"
    llm_service_url: str = "http://localhost:11434/v1"  # Ollama (local Mac); use http://host.docker.internal:11434/v1 from Docker

    retrieval_top_k: int = 50
    rerank_top_k: int = 5
    max_context_tokens: int = 2048
    llm_temperature: float = 0.1
    llm_max_tokens: int = 512

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]
```

### Notes

- Prefer lower-case Python attribute names.
- If `.env` lives at repo root, either point `env_file` to `../.env` from `backend/` or load it explicitly.
- Add simple validators for values like upload size and top-k limits if desired.

---

## 🪵 Step 2: Create structured logging in `backend/app/utils/logging_config.py`

Use `structlog` and the standard library logging module.

### Requirements

- JSON-style logs in development and production
- include timestamp, level, logger name, and request ID if present
- expose a `configure_logging()` helper

### Minimal pattern

```python
import logging
import structlog


def configure_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(level=log_level)
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
    )
```

### Log events you will rely on later

- app startup/shutdown
- health checks
- uploads
- parsing/chunking
- vector writes
- retrieval timing
- chat streaming lifecycle

---

## 🧵 Step 3: Add request tracing in `backend/app/utils/tracing.py`

Create middleware that assigns a correlation ID to every request.

### Recommended behavior

- read `X-Request-ID` if the client sends one
- otherwise generate a UUID
- attach it to `request.state.request_id`
- add it to the response headers
- bind it into the log context

### Why this matters

Later, a single user action will touch:

- upload endpoint
- ingestion service
- embedding service
- vector store
- retrieval pipeline
- chat streaming

A correlation ID makes debugging those flows much easier.

---

## 🛣️ Step 4: Create router aggregation in `backend/app/routes/__init__.py`

Start with an empty aggregator so later phases only register routers in one place.

Suggested pattern:

```python
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")
```

Later phases will attach:

- `documents`
- `retrieval`
- `chat`

If you prefer `/api/v1`, that is also acceptable. For consistency with the current implementation plan examples, `/api` is fine for now.

---

## 🚀 Step 5: Create `backend/app/main.py`

This is the backend entry point.

### Required responsibilities

1. load settings
2. configure logging
3. create FastAPI app
4. add CORS middleware
5. add request ID middleware
6. include the shared API router
7. expose health check endpoints

### Suggested app features

- title: `Enterprise RAG API`
- version: `0.1.0`
- docs enabled in development
- startup log event
- shutdown log event

### Health endpoints

#### `GET /health`

Return lightweight service info:

```json
{
  "status": "healthy",
  "service": "backend",
  "environment": "development"
}
```

#### `GET /health/deep`

Check dependencies:

- PostgreSQL connection
- Redis ping
- optional ML service reachability if URLs are configured

Return `503` if a critical dependency is down.

---

## 🔍 Step 6: Implement dependency checks

For deep health checks, create small probe helpers inside `main.py` first; refactor later if needed.

### PostgreSQL check

- open a short-lived session
- run `SELECT 1`
- return `True/False`

### Redis check

- create a Redis client
- call `PING`
- return `True/False`

### External service checks

Optional for this phase, but helpful:

- `GET http://embedding-service:8001/health`
- `GET http://reranker-service:8002/health`
- `GET http://localhost:11434/v1/models` (Ollama LLM health check)

If those services are not implemented yet, report them as `not_configured` or `not_checked` rather than failing the whole endpoint.

---

## ▶️ Step 7: Run the backend

From the repo root:

```bash
make dev-backend
```

Or locally inside the backend virtual environment:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Step 8: Verify the app

### Basic health check

```bash
curl http://localhost:8000/health
```

### Deep health check

```bash
curl http://localhost:8000/health/deep
```

### Expected behavior

- backend starts without import errors
- `/health` returns `200`
- `/health/deep` returns dependency status details
- logs include request IDs and structured fields

---

## 📌 What should exist after this phase

Even though upload/chat endpoints are not implemented yet, the backend should now provide:

- app bootstrapping
- config loading
- logging foundation
- route registration mechanism
- service readiness probes

That makes the next phases much faster.

---

## 🐛 Common Issues

### 1. `.env` values are not loading

Check the `env_file` path in `config.py`.

### 2. Backend starts but logs are unreadable

Make sure `configure_logging()` is called before the app serves requests.

### 3. `GET /health/deep` fails on Redis import

Ensure `redis` is installed from `backend/requirements.txt` and use the correct client API for the installed version.

### 4. CORS errors in browser later

Make sure `http://localhost:3000` is included in allowed origins.

---

## 🎯 Phase 3 Checklist

- [ ] Created `backend/app/config.py`
- [ ] Created structured logging setup
- [ ] Added request ID middleware
- [ ] Created `backend/app/main.py`
- [ ] Added `/health` endpoint
- [ ] Added `/health/deep` endpoint
- [ ] Started the backend successfully
- [ ] Verified request logs include correlation IDs

---

## 📝 Commit Phase 3

```bash
git add .
git commit -m "feat: Phase 3 - FastAPI app foundation

- Added configuration management
- Added structured logging and request tracing
- Created FastAPI app entry point
- Added health and deep health endpoints"
```

---

## ➡️ Next Phase

Continue with **Phase 4: Document Upload**

- Read: `docs/implementation-plan/05-phase-04-document-upload.md`
- Goal: accept PDF/TXT uploads and persist document metadata

---

**Phase 3 Complete!**

**Status:** ✅ Backend foundation ready

