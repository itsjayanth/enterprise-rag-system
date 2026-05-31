# Master Implementation Plan - Enterprise RAG System

## 🎯 Implementation Overview

This is a **production-grade implementation plan** for the enterprise RAG system, broken into **small, executable phases** optimized for incremental development and GitHub Copilot-assisted implementation.

---

## 📋 Simplified Scope (Current Implementation)

### ✅ What We're Building

- **Single-user web application** (no auth, no multi-user for now)
- **PDF/TXT document upload**
- **RAG-based chat** with uploaded documents
- **Streaming responses** (SSE)
- **Production architecture** (microservices-ready but simplified)
- **FREE open-source models** only
- **Local deployment** (Docker Compose)

### ❌ What We're NOT Building (Yet)

- Authentication/Registration
- Multi-user support
- User isolation
- Grafana/Prometheus dashboards
- Unit tests
- AWS integration
- Paid APIs (OpenAI, Gemini)

### 🔧 Simplified Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Backend** | FastAPI (Python 3.11) | Single monolith for now, split later |
| **Database** | PostgreSQL 16 | Documents, chunks, chat history |
| **Vector DB** | Pinecone (free tier) | Vector embeddings |
| **Cache/Queue** | Redis 7 | Celery broker, caching |
| **Workers** | Celery | Async document processing |
| **Embeddings** | BGE-M3 | Sentence transformers |
| **LLM** | Llama 3.1-8B | vLLM for inference |
| **Reranker** | BGE-reranker-v2-m3 | Cross-encoder |
| **Frontend** | Next.js 14 | Streaming chat UI |
| **Observability** | Structured logs + traces | JSON logging, correlation IDs |

---

## 🏗️ Implementation Strategy

### **Phase-Based Approach**

We'll implement in **12 phases**, each small enough for a single focused development session:

```
Foundation (Phases 1-3)
├─ Phase 1: Project scaffolding & environment setup
├─ Phase 2: Database models & migrations
└─ Phase 3: Core FastAPI structure with logging

Document Processing (Phases 4-5)
├─ Phase 4: Document upload & storage
└─ Phase 5: PDF parsing & chunking

AI/ML Services (Phases 6-8)
├─ Phase 6: Embedding service (BGE-M3)
├─ Phase 7: Vector storage (Pinecone integration)
└─ Phase 8: LLM service (vLLM setup)

RAG Pipeline (Phases 9-10)
├─ Phase 9: Retrieval pipeline (embed → search → rerank)
└─ Phase 10: Chat service with streaming

Worker System (Phase 11)
└─ Phase 11: Celery workers for async processing

Frontend (Phase 12)
└─ Phase 12: Next.js chat interface
```

---

## 🚀 Development Setup (Quick Start)

### Prerequisites

```bash
# Install required software (local Mac)
brew install python@3.11 node@20 ollama docker

# Pull the LLM model — ~4.7 GB download, runs on CPU/Apple MPS
ollama pull llama3.1:8b

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate
cd backend && pip install -r requirements.txt
```

### Model Setup

```bash
# Models used in this project:
# - Phase 6: BAAI/bge-m3  (embedding service — runs on CPU/MPS in Docker)
# - Phase 9: BAAI/bge-reranker-v2-m3  (reranker service — runs on CPU in Docker)
# - Phase 8: llama3.1:8b via Ollama  (LLM — runs on host Mac CPU/MPS, NOT in Docker)
#
# Note: vLLM is NOT used for local development. It requires a CUDA GPU.
# Ollama is the local LLM backend. Switch to vLLM later when a GPU is available.
#
# Embedding and reranker models auto-download from HuggingFace on first startup.
# Pull the Ollama model manually:
ollama pull llama3.1:8b
```

### Run Development Stack

```bash
# 1. Start Ollama (LLM — host process, not Docker)
ollama serve

# 2. Start infrastructure (Postgres + Redis)
make dev-infra

# 3. Configure environment
cp .env.example .env
# Edit .env and add your Pinecone API key
# LLM_SERVICE_URL should be http://localhost:11434/v1 (or host.docker.internal when inside Docker)

# 4. Run the backend locally or via Docker Compose
cd backend
uvicorn app.main:app --reload --port 8000

# 5. Run the frontend
cd ../frontend
npm install
npm run dev

# 6. Start ML services when you reach their phases (CPU, no GPU needed)
cd ..
docker compose up -d embedding-service reranker-service
```

**Useful shortcut:** see `docs/implementation-plan/DEV-SETUP-GUIDE.md` for the recommended daily development workflow.

---

## 📂 Final Project Structure

```
enterprise-rag-system/
├── .env                          # Single environment file
├── .env.example                  # Template
├── .gitignore
├── docker-compose.yml            # Full stack orchestration
├── Makefile                      # Common commands
├── README.md
│
├── backend/                      # FastAPI backend (monolith for now)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings from .env
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # Database models
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   ├── chunk.py
│   │   │   └── chat.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   └── chat.py
│   │   ├── routes/              # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── documents.py
│   │   │   └── chat.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── document_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── retrieval_service.py
│   │   │   └── chat_service.py
│   │   └── utils/               # Utilities
│   │       ├── __init__.py
│   │       ├── logging_config.py
│   │       ├── pdf_parser.py
│   │       ├── chunking.py
│   │       └── tracing.py
│   ├── workers/                 # Celery workers
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── tasks.py
│   ├── migrations/              # Alembic migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── ml-services/                 # ML model serving
│   ├── embedding-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   └── model.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── reranker-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   └── model.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── llm-service/
│       └── docker-compose.override.yml  # vLLM configuration
│
├── frontend/                    # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── chat/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   └── MessageInput.tsx
│   │   │   └── documents/
│   │   │       └── DocumentUpload.tsx
│   │   └── lib/
│   │       └── api/
│   │           ├── client.ts
│   │           └── chat.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── Dockerfile
│
├── data/                        # Local data (gitignored)
│   ├── uploads/                 # Uploaded files
│   └── models/                  # Downloaded ML models
│
├── scripts/                     # Utility scripts
│   ├── download_models.py
│   ├── init_db.py
│   └── test_pipeline.py
│
└── docs/
    ├── desing-docs/             # Design documentation (already created)
    └── implementation-plan/     # This directory
        ├── 00-MASTER-PLAN.md
        ├── 01-environment-setup.md
        ├── 02-phase-01-scaffolding.md
        ├── 03-phase-02-database.md
        ├── ...
        └── 13-phase-12-frontend.md
```

---

## 🚀 Implementation Order

### **Strategy: Backend → GenAI → Frontend**

**Why this order?**
1. **Backend first:** Establishes data models, APIs, architecture
2. **GenAI second:** Can test ML components independently via API
3. **Frontend last:** Consumes working backend APIs

### **Execution Flow**

```
Week 1: Foundation & Database
├─ Day 1-2: Phase 1 (Scaffolding)
├─ Day 2-3: Phase 2 (Database)
└─ Day 3-4: Phase 3 (FastAPI structure)

Week 2: Document Processing
├─ Day 1-2: Phase 4 (Document upload)
└─ Day 3-4: Phase 5 (PDF parsing)

Week 3: AI/ML Services
├─ Day 1-2: Phase 6 (Embeddings)
├─ Day 3: Phase 7 (Vector DB)
└─ Day 4: Phase 8 (LLM setup)

Week 4: RAG Pipeline
├─ Day 1-3: Phase 9 (Retrieval)
├─ Day 3-4: Phase 10 (Chat + streaming)
└─ Day 4: Phase 11 (Workers)

Week 5: Frontend
└─ Day 1-5: Phase 12 (Next.js UI)
```

---

## 📝 Phase Checklist

### Phase 1: Project Scaffolding ✅
- [ ] Create folder structure
- [ ] Setup `.env` and `.env.example`
- [ ] Create `docker-compose.yml`
- [ ] Create `Makefile`
- [ ] Setup `.gitignore`
- [ ] Initialize git repo
- **Output:** Clean project skeleton

### Phase 2: Database Setup ✅
- [ ] Create SQLAlchemy models
- [ ] Setup Alembic migrations
- [ ] Create initial migration
- [ ] Test PostgreSQL connection
- **Output:** Working database with schema

### Phase 3: FastAPI Core ✅
- [ ] Create FastAPI app structure
- [ ] Setup structured logging
- [ ] Setup tracing (correlation IDs)
- [ ] Create health check endpoint
- [ ] Test server startup
- **Output:** Running FastAPI server with observability

### Phase 4: Document Upload ✅
- [ ] Create document upload endpoint
- [ ] Implement file storage logic
- [ ] Create document model & schema
- [ ] Test file upload
- **Output:** Working document upload API

### Phase 5: PDF Processing ✅
- [ ] Implement PDF parser (pypdfium2)
- [ ] Implement text chunking
- [ ] Store chunks in database
- [ ] Test on sample PDFs
- **Output:** Document → chunks pipeline

### Phase 6: Embedding Service ✅
- [ ] Create embedding service (BGE-M3)
- [ ] Setup FastAPI wrapper
- [ ] Implement batch embedding
- [ ] Test embedding generation
- **Output:** Working embedding API

### Phase 7: Vector Storage ✅
- [ ] Setup Pinecone client
- [ ] Implement vector upsert
- [ ] Implement vector search
- [ ] Test retrieval
- **Output:** Working vector storage

### Phase 8: LLM Service ✅
- [ ] Setup vLLM via Docker
- [ ] Configure Llama 3.1-8B
- [ ] Test text generation
- [ ] Test streaming
- **Output:** Working LLM inference

### Phase 9: Retrieval Pipeline ✅
- [ ] Implement query embedding
- [ ] Implement vector search
- [ ] Setup reranker service
- [ ] Implement reranking
- [ ] Test end-to-end retrieval
- **Output:** Working RAG retrieval

### Phase 10: Chat Service ✅
- [ ] Create chat models (session, messages)
- [ ] Implement chat endpoint
- [ ] Implement streaming (SSE)
- [ ] Test streaming chat
- **Output:** Working RAG chat API

### Phase 11: Celery Workers ✅
- [ ] Setup Celery app
- [ ] Create document processing task
- [ ] Create embedding task
- [ ] Test async processing
- **Output:** Async document pipeline

### Phase 12: Frontend ✅
- [ ] Create Next.js app
- [ ] Implement document upload UI
- [ ] Implement chat interface
- [ ] Implement streaming display
- [ ] Test end-to-end flow
- **Output:** Working web application

---

## 🔧 Environment Variables Structure

**Single `.env` file at repo root:**

```bash
# ===================================
# DATABASE
# ===================================
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/enterprise_rag
DATABASE_POOL_SIZE=20

# ===================================
# REDIS
# ===================================
REDIS_URL=redis://localhost:6379/0

# ===================================
# PINECONE
# ===================================
PINECONE_API_KEY=your-api-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=enterprise-rag

# ===================================
# STORAGE
# ===================================
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_SIZE_MB=50

# ===================================
# ML MODELS
# ===================================
EMBEDDING_MODEL_NAME=BAAI/bge-m3
RERANKER_MODEL_NAME=BAAI/bge-reranker-v2-m3
LLM_MODEL_NAME=meta-llama/Meta-Llama-3.1-8B-Instruct
MODEL_CACHE_DIR=/data/models

# IMPORTANT:
# Use the same EMBEDDING_MODEL_NAME for both:
# 1. document chunk embeddings stored in Pinecone
# 2. user query embeddings used at retrieval time
# Query text may add the BGE retrieval instruction prefix,
# but the underlying embedding model must remain the same.

# ===================================
# ML SERVICE URLS
# ===================================
EMBEDDING_SERVICE_URL=http://embedding-service:8001
RERANKER_SERVICE_URL=http://reranker-service:8002
LLM_SERVICE_URL=http://localhost:11434/v1   # Ollama (local Mac dev)

# ===================================
# RAG CONFIGURATION
# ===================================
RETRIEVAL_TOP_K=50
RERANK_TOP_K=5
MAX_CONTEXT_TOKENS=2048
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=512

# ===================================
# APPLICATION
# ===================================
ENVIRONMENT=development
LOG_LEVEL=INFO
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# ===================================
# FRONTEND
# ===================================
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📊 Success Criteria Per Phase

Each phase must meet these criteria before moving to next:

1. **Code Quality**
   - No syntax errors
   - Follows project conventions
   - Proper error handling
   - Structured logging added

2. **Functionality**
   - Core feature works as expected
   - Manual testing passes
   - Integration with previous phases intact

3. **Documentation**
   - Code comments for complex logic
   - Docstrings for functions
   - README updates if needed

4. **Observability**
   - Structured logs emitted
   - Correlation IDs tracked
   - Errors logged with context

---

## 🎯 Development Workflow

### Per Phase Execution

```bash
# 1. Read phase documentation
cat docs/implementation-plan/XX-phase-YY-name.md

# 2. Create/modify files as per plan
# (Use GitHub Copilot for implementation)

# 3. Test the phase
make test-phase-YY

# 4. Commit phase
git add .
git commit -m "feat: Phase YY - [description]"

# 5. Move to next phase
```

### Testing Strategy

```bash
# Start infrastructure
make dev-infra  # Just DB, Redis

# Test backend
cd backend
pytest tests/  # When we add tests later

# Manual API testing
curl http://localhost:8000/health

# Test specific phase
make test-upload          # Phase 4
make test-embeddings      # Phase 6
make test-chat-streaming  # Phase 10
```

---

## 🚧 Known Simplifications & Future Improvements

### Current Simplifications

1. **No Authentication**
   - Single user, no login
   - Will add JWT auth later

2. **Monolithic Backend**
   - Single FastAPI app
   - Will split into microservices later

3. **No Multi-Tenancy**
   - No user isolation in DB/Pinecone
   - Will add user_id filters later

4. **Simplified Observability**
   - Only structured logs + traces
   - Will add Prometheus/Grafana later

5. **No Rate Limiting**
   - Open endpoints
   - Will add SlowAPI later

### Future Enhancement Path

```
Phase 13+: Production Hardening
├─ Add authentication (JWT)
├─ Add multi-user support
├─ Split into microservices
├─ Add Prometheus metrics
├─ Add Grafana dashboards
├─ Add rate limiting
├─ Add input validation
├─ Add unit tests
├─ Add integration tests
└─ Add CI/CD pipeline
```

---

## 📚 Reference Documents

For detailed design rationale, refer to:

- **System Overview:** `docs/desing-docs/SYSTEM-OVERVIEW.md`
- **Architecture:** `docs/desing-docs/backend/architecture.md`
- **GenAI Stack:** `docs/desing-docs/GEN-AI/tech-stack.md`
- **Data Flow:** `docs/desing-docs/backend/data-flow.md`
- **Frontend:** `docs/desing-docs/UI/frontend-stack.md`

---

## 🎬 Ready to Start?

**Next Steps:**

1. Read `docs/implementation-plan/01-environment-setup.md`
2. Setup your development environment
3. Start with Phase 1: `docs/implementation-plan/02-phase-01-scaffolding.md`

**Let's build! 🚀**

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Status:** Ready for Implementation

