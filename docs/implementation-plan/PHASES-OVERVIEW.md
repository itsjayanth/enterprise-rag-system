# Phases 2-12: Quick Reference Guide

This document provides a **quick overview** of all implementation phases. Each phase will have a detailed execution document.

---

## Phase 2: Database Setup (2-3 hours)

### Objective
Create SQLAlchemy models, setup Alembic migrations, and establish database schema.

### Key Files to Create
```
backend/app/database.py                # SQLAlchemy engine & session
backend/app/models/document.py         # Document model
backend/app/models/chunk.py            # Chunk model
backend/app/models/chat.py             # ChatSession & Message models
backend/alembic.ini                    # Alembic configuration
backend/migrations/env.py              # Migration environment
backend/migrations/versions/001_initial.py  # Initial migration
```

### Key Steps
1. Install SQLAlchemy and Alembic
2. Create database connection management
3. Define Document model (id, filename, status, etc.)
4. Define Chunk model (id, document_id, content, page_number, etc.)
5. Define ChatSession and Message models
6. Initialize Alembic
7. Create initial migration
8. Test migration: `make migrate`
9. Verify tables created in PostgreSQL

### Testing
```bash
make shell-db
\dt  # List tables - should see documents, chunks, chat_sessions, messages
```

---

## Phase 3: FastAPI Core (2-3 hours)

### Objective
Setup FastAPI application with structured logging, tracing, and health checks.

### Key Files to Create
```
backend/app/main.py                    # FastAPI app entry point
backend/app/config.py                  # Settings from environment
backend/app/utils/logging_config.py    # Structured logging setup
backend/app/utils/tracing.py           # Correlation ID middleware
backend/app/routes/__init__.py         # Router aggregation
```

### Key Steps
1. Create Pydantic Settings class (loads from .env)
2. Setup structured JSON logging with structlog
3. Create correlation ID middleware
4. Create FastAPI app with CORS
5. Add health check endpoint
6. Add startup/shutdown events
7. Test server: `make dev-backend`
8. Verify: `curl http://localhost:8000/health`

### Testing
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", "..."}

# Check logs for structured JSON
make logs-backend
```

---

## Phase 4: Document Upload (2-3 hours)

### Objective
Implement document upload API with file storage.

### Key Files to Create
```
backend/app/schemas/document.py        # Pydantic schemas
backend/app/services/document_service.py  # Business logic
backend/app/routes/documents.py        # Upload endpoints
```

### Key Steps
1. Create DocumentUpload, DocumentResponse schemas
2. Implement file validation (type, size)
3. Create storage directory structure
4. Implement save_file() function
5. Create POST /api/documents/upload endpoint
6. Store document record in database
7. Return document metadata
8. Test with curl/Postman

### Testing
```bash
curl -X POST -F "file=@sample.pdf" \
  http://localhost:8000/api/documents/upload
```

---

## Phase 5: PDF Processing (3-4 hours)

### Objective
Parse PDFs, extract text, and chunk into searchable segments.

### Key Files to Create
```
backend/app/utils/pdf_parser.py        # PDF parsing logic
backend/app/utils/chunking.py          # Text chunking
backend/app/services/ingestion_service.py  # Orchestration
```

### Key Steps
1. Install pypdfium2
2. Implement PDF text extraction
3. Implement TXT file reading
4. Create RecursiveCharacterTextSplitter
5. Implement chunking with metadata preservation
6. Store chunks in database
7. Update document status
8. Test on sample PDFs

### Testing
```bash
# Upload PDF, check chunks created
make shell-db
SELECT COUNT(*) FROM chunks WHERE document_id = '...';
```

---

## Phase 6: Embedding Service (3-4 hours)

### Objective
Create FastAPI service that serves BGE-M3 embeddings.

### Key Files to Create
```
ml-services/embedding-service/app/main.py  # Service entry
ml-services/embedding-service/app/model.py # Model loading
ml-services/embedding-service/requirements.txt
ml-services/embedding-service/Dockerfile
```

### Key Steps
1. Create FastAPI app for embeddings
2. Load BGE-M3 model with sentence-transformers
3. Create /embed/documents endpoint (batch)
4. Create /embed/query endpoint (single)
5. Implement GPU detection & fallback
6. Add health check
7. Build Docker image
8. Test embedding generation

### Testing
```bash
# Start service
docker compose up -d embedding-service

# Test
curl -X POST http://localhost:8001/embed/documents \
  -H "Content-Type: application/json" \
  -d '{"texts": ["hello world"]}'
```

---

## Phase 7: Vector Storage (2-3 hours)

### Objective
Integrate Pinecone for vector storage and similarity search.

### Key Files to Create
```
backend/app/services/vector_service.py  # Pinecone client wrapper
```

### Key Steps
1. Install pinecone-client
2. Create Pinecone client initialization
3. Implement upsert_vectors()
4. Implement search_vectors()
5. Add metadata to vectors (document_id, page_number, etc.)
6. Test upsert and search
7. Integrate with chunk storage

### Testing
```python
# In Python shell
from app.services.vector_service import vector_service
vectors = vector_service.search("test query", top_k=5)
print(vectors)
```

---

## Phase 8: LLM Service (3-4 hours)

### Objective
Setup vLLM to serve Llama 3.1-8B with streaming support.

### Key Files to Create
```
ml-services/llm-service/docker-compose.override.yml
backend/app/services/llm_client.py  # Client wrapper
```

### Key Steps
1. Configure vLLM in docker-compose
2. Download Llama 3.1-8B model
3. Start vLLM service
4. Test OpenAI-compatible API
5. Implement streaming client
6. Test text generation
7. Test streaming generation

### Testing
```bash
# Test vLLM directly
curl http://localhost:8003/v1/models

curl http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Meta-Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'
```

---

## Phase 9: Retrieval Pipeline (4-5 hours)

### Objective
Build complete RAG retrieval pipeline with reranking.

### Key Files to Create
```
ml-services/reranker-service/app/main.py  # Reranker service
backend/app/services/retrieval_service.py # RAG orchestration
backend/app/routes/retrieval.py           # Retrieval endpoint
```

### Key Steps
1. Create reranker service (BGE-reranker-v2-m3)
2. Implement query → embedding
3. Implement vector search (top 50)
4. Implement reranking (top 5)
5. Implement context building
6. Create /api/retrieval/search endpoint
7. Test end-to-end retrieval
8. Verify relevant chunks returned

### Testing
```bash
curl -X POST http://localhost:8000/api/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{"query": "what is X?", "document_ids": ["..."], "top_k": 5}'
```

---

## Phase 10: Chat Service (3-4 hours)

### Objective
Implement streaming chat with RAG integration.

### Key Files to Create
```
backend/app/services/chat_service.py  # Chat orchestration
backend/app/routes/chat.py            # Chat endpoints
backend/app/utils/streaming.py        # SSE utilities
```

### Key Steps
1. Create ChatSession and Message schemas
2. Implement create_session()
3. Implement RAG pipeline orchestration
4. Build RAG prompt template
5. Implement streaming response (SSE)
6. Store messages in database
7. Test streaming chat
8. Verify citations included

### Testing
```bash
# Test streaming
curl -N http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "summarize the document", "session_id": null}'
```

---

## Phase 11: Celery Workers (2-3 hours)

### Objective
Setup async document processing with Celery.

### Key Files to Create
```
backend/workers/celery_app.py         # Celery configuration
backend/workers/tasks.py              # Task definitions
```

### Key Steps
1. Configure Celery with Redis broker
2. Create document processing task
3. Create embedding generation task
4. Modify document upload to queue tasks
5. Test task execution
6. Monitor with Flower (optional)

### Testing
```bash
# Start worker
make dev-worker

# Upload document
curl -X POST -F "file=@test.pdf" http://localhost:8000/api/documents/upload

# Check worker logs
make logs-worker
```

---

## Phase 12: Frontend (5-6 hours)

### Objective
Build Next.js chat interface with document upload.

### Key Files to Create
```
frontend/src/app/layout.tsx
frontend/src/app/page.tsx
frontend/src/app/chat/page.tsx
frontend/src/components/chat/ChatInterface.tsx
frontend/src/components/chat/MessageList.tsx
frontend/src/components/chat/MessageInput.tsx
frontend/src/components/documents/DocumentUpload.tsx
frontend/src/lib/api/client.ts
frontend/src/lib/api/chat.ts
frontend/tailwind.config.ts
frontend/tsconfig.json
```

### Key Steps
1. Initialize Next.js 14 (App Router)
2. Setup TailwindCSS
3. Install shadcn/ui components
4. Create API client (axios)
5. Implement DocumentUpload component
6. Implement ChatInterface component
7. Implement SSE streaming client
8. Handle streaming display
9. Test end-to-end flow

### Testing
```bash
# Start frontend
make dev-frontend

# Visit http://localhost:3000
# Upload document
# Chat with document
# Verify streaming works
```

---

## Execution Order Summary

```
Week 1:
Day 1: Phase 1 (Scaffolding)
Day 2: Phase 2 (Database) + Phase 3 (FastAPI)
Day 3: Phase 4 (Upload) + Phase 5 (PDF)
Day 4: Phase 6 (Embeddings)
Day 5: Phase 7 (Vectors)

Week 2:
Day 1: Phase 8 (LLM)
Day 2-3: Phase 9 (Retrieval)
Day 3-4: Phase 10 (Chat)
Day 4: Phase 11 (Workers)
Day 5: Start Phase 12 (Frontend)

Week 3:
Day 1-2: Complete Phase 12 (Frontend)
Day 3-4: Integration testing
Day 5: Bug fixes and polish
```

---

## Testing Strategy Per Phase

| Phase | Test Type | How to Test |
|-------|-----------|-------------|
| 2 | Database | `make shell-db`, check tables |
| 3 | API | `curl http://localhost:8000/health` |
| 4 | Upload | curl with multipart form data |
| 5 | Processing | Check chunks table after upload |
| 6 | Embeddings | curl POST to embedding service |
| 7 | Vectors | Python script to query Pinecone |
| 8 | LLM | curl to vLLM API |
| 9 | Retrieval | curl to retrieval endpoint |
| 10 | Chat | curl with streaming (-N flag) |
| 11 | Workers | Upload and monitor worker logs |
| 12 | Frontend | Manual UI testing |

---

## Critical Success Factors

### Per Phase
1. **Complete all steps** - Don't skip
2. **Test thoroughly** - Use provided test commands
3. **Check logs** - Ensure no errors
4. **Commit progress** - Git commit after each phase
5. **Document issues** - Note any problems

### Overall
1. **Follow order** - Phases build on each other
2. **One at a time** - Don't jump ahead
3. **Read design docs** - When unclear, check `docs/desing-docs/`
4. **Use Copilot** - Let it generate boilerplate
5. **Test incrementally** - Don't wait til end

---

## Common Pitfalls to Avoid

1. **Skipping phases** - Each phase is foundational
2. **Not testing** - Bugs compound over phases
3. **Wrong .env values** - Double-check configuration
4. **Missing dependencies** - Install all requirements
5. **Not checking logs** - Errors hide in logs
6. **Hardcoding values** - Use environment variables
7. **No correlation IDs** - Implement from Phase 3
8. **Forgetting migrations** - Run after model changes

---

## Next Steps

1. Review this overview
2. Go back to `INDEX.md` for detailed roadmap
3. Start with Phase 2: `03-phase-02-database.md` (to be created)
4. Work through each phase systematically
5. Test after each phase
6. Commit after each phase

---

**All phases ready for detailed implementation!** 

When ready to start Phase 2, the detailed execution document will be created with:
- Step-by-step code snippets
- Testing commands
- Verification checklist
- Common issues and solutions

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Status:** Ready for Implementation

