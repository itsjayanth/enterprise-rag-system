# System Overview - Enterprise RAG Platform

## Executive Summary

This document provides a **high-level overview** of the complete enterprise RAG system, tying together all design documents and providing a roadmap for implementation.

---

## 1. What is This System?

A **production-grade, enterprise RAG (Retrieval Augmented Generation) platform** that enables users to:

1. **Upload documents** (PDF, TXT)
2. **Chat with documents** using natural language
3. **Get accurate answers** with citations from uploaded content
4. **Maintain conversation history** across sessions
5. **Work in a multi-user environment** with data isolation

### Key Differentiators

✅ **100% Free & Open Source**
- No AWS (no S3, no Bedrock)
- No OpenAI APIs
- No Gemini APIs
- Uses free, production-capable models

✅ **Production Architecture**
- Not a toy/demo/notebook
- Microservices design
- Kubernetes-ready
- Enterprise observability

✅ **Modern GenAI Stack (2025-2026)**
- SOTA embedding model (BGE-M3)
- Best free LLM (Llama 3.1-8B)
- Production inference (vLLM)
- Advanced retrieval (vector + reranking)

---

## 2. System Capabilities

### Phase 1: Core RAG (MVP)

**Features:**
- ✅ User authentication (JWT)
- ✅ Document upload (PDF, TXT)
- ✅ Document parsing & chunking
- ✅ Embedding generation (BGE-M3)
- ✅ Vector storage (Pinecone)
- ✅ Basic retrieval
- ✅ LLM Q&A (Llama 3.1-8B)
- ✅ Simple chat UI

**Timeline:** 4-6 weeks

### Phase 2: Production Features

**Features:**
- ✅ Streaming responses (SSE)
- ✅ Chat history & sessions
- ✅ Multi-user support
- ✅ Rate limiting
- ✅ Observability (metrics, logs, traces)
- ✅ Async processing (Celery workers)

**Timeline:** 2-4 weeks

### Phase 3: Advanced RAG

**Features:**
- ✅ Hybrid retrieval (multi-stage)
- ✅ Reranking (cross-encoder)
- ✅ Metadata filtering
- ✅ Semantic chunking
- ✅ Citation support
- ✅ User feedback loop

**Timeline:** 2-3 weeks

### Future Enhancements

**Potential Features:**
- Multi-modal RAG (images, tables)
- Graph RAG
- Agentic workflows (LangGraph)
- Fine-tuned embeddings
- Custom LLM fine-tuning
- Advanced Analytics

---

## 3. Architecture Layers

### Layer 1: Frontend (User Interface)

```
Next.js 14 Application
├── Streaming chat interface
├── Document upload with progress
├── Session management
├── Authentication UI
└── Responsive design (mobile-ready)

Tech: Next.js, shadcn/ui, TailwindCSS, Zustand
```

### Layer 2: API Gateway

```
FastAPI Gateway
├── Authentication (JWT)
├── Rate limiting
├── Request validation
├── CORS handling
└── Load balancing

Tech: FastAPI, PyJWT, SlowAPI
```

### Layer 3: Business Services

```
Microservices (Python + FastAPI)
├── User Service → User accounts
├── Document Service → Upload handling
├── Ingestion Service → PDF parsing, chunking
├── Retrieval Service → RAG orchestration
└── Chat Service → Streaming responses

Tech: FastAPI, SQLAlchemy, Pydantic
```

### Layer 4: ML Services (GPU)

```
Model Serving
├── Embedding Service → BGE-M3 (T4 GPU)
├── Reranker Service → BGE-reranker-v2-m3 (T4 GPU)
└── LLM Service → Llama 3.1-8B (A10G GPU)

Tech: vLLM, sentence-transformers, FastAPI
```

### Layer 5: Processing Layer

```
Async Workers
├── Celery workers
├── Redis broker
└── Background tasks (document processing, embeddings)

Tech: Celery, Redis
```

### Layer 6: Data Layer

```
Storage
├── PostgreSQL → Users, documents, chunks, chat
├── Redis → Cache, job queue
├── Pinecone → Vector embeddings
└── Filesystem (PVC) → Uploaded files

Tech: PostgreSQL 16, Redis 7, Pinecone
```

### Layer 7: Observability

```
Monitoring & Observability
├── Prometheus → Metrics collection
├── Grafana → Dashboards
├── OpenTelemetry → Distributed tracing
├── LangFuse → GenAI observability
└── Structured logging → JSON logs

Tech: Prometheus, Grafana, OpenTelemetry, LangFuse
```

---

## 4. Data Flow Diagrams

### 4.1 Document Upload Flow

```
User uploads PDF
    ↓
API Gateway validates file
    ↓
Document Service saves to filesystem
    ↓
PostgreSQL: Insert document record (status: pending)
    ↓
Redis: Publish event "document.uploaded"
    ↓
Celery Worker consumes event
    ↓
Ingestion Service:
  1. Parse PDF (pypdfium2)
  2. Extract text per page
  3. Chunk text (512 chars, 50 overlap)
  4. Save chunks to PostgreSQL
  5. Queue embedding tasks
    ↓
Celery Worker (batch of 32 chunks)
    ↓
Embedding Service: Generate embeddings (BGE-M3)
    ↓
Pinecone: Upsert vectors with metadata
    ↓
PostgreSQL: Update chunks.embedding_id
    ↓
PostgreSQL: Update documents.status = 'completed'
    ↓
Frontend: Show "Processing complete"
```

**Metrics:**
- 100-page PDF → 2-5 minutes
- Bottleneck: GPU embedding generation

### 4.2 Chat Query Flow

```
User types question
    ↓
Frontend: POST /api/v1/chat/query (SSE streaming)
    ↓
API Gateway: Auth check, rate limit
    ↓
Chat Service: Orchestrate RAG pipeline
    ↓
PARALLEL:
  ├─ Store user message (PostgreSQL)
  └─ Retrieval Service:
       ├─ Stage 1: Embed query (BGE-M3) → 20-50ms
       ├─ Stage 2: Vector search (Pinecone, top_k=50) → 100-200ms
       ├─ Stage 3: Rerank (BGE-reranker, top_k=5) → 30-80ms
       └─ Stage 4: Build context (2048 tokens max)
    ↓
Chat Service: Build RAG prompt
    ↓
LLM Service (vLLM):
  ├─ First token → 150-300ms
  └─ Stream tokens → 30-50 tokens/sec
    ↓
Frontend: Display streaming response
    ↓
Chat Service: Store assistant message + sources
    ↓
Frontend: Show citations
```

**Metrics:**
- Time to first token: ~300-600ms
- Full response (500 tokens): ~10-15s
- Streaming UX: User sees immediate progress

---

## 5. Technology Decisions Summary

### Why These Technologies?

| Decision | Rationale |
|----------|-----------|
| **Llama 3.1-8B** | Best free 8B model, 128K context, commercial license |
| **BGE-M3** | #1 MTEB ranking, hybrid retrieval, multilingual |
| **vLLM** | 10-20x faster than naive serving, production-proven |
| **Pinecone** | Managed vector DB, free tier, easy scaling |
| **Next.js 14** | Best React framework, SSR, streaming, great DX |
| **FastAPI** | Fast, async, auto docs, type hints |
| **PostgreSQL** | Reliable, ACID, complex queries, JSON support |
| **Redis** | Fast cache, Celery broker, simple |
| **Celery** | Mature async task queue, retries, monitoring |
| **Kubernetes** | Industry standard, auto-scaling, self-healing |
| **LangGraph** | Better than LangChain for complex workflows |

### Avoided Technologies

| Technology | Why Avoided |
|-----------|-------------|
| **AWS S3** | Vendor lock-in, cost, use local PVC instead |
| **OpenAI API** | Expensive ($$$), not self-hosted |
| **Elasticsearch** | Overkill for vector search, Pinecone simpler |
| **MongoDB** | PostgreSQL better for relational + JSONB |
| **Ollama** | Not production-grade, use vLLM |

---

## 6. Cost Breakdown

### Development Environment

| Resource | Spec | Monthly Cost |
|----------|------|--------------|
| GPU (dev) | 1x RTX 3090 (local) | $0 (owned) |
| Pinecone | Free tier (1M vectors) | $0 |
| Infrastructure | Docker Compose (local) | $0 |
| **Total** | | **$0/month** |

### Production (AWS/GCP/Azure)

| Resource | Spec | Monthly Cost (AWS) |
|----------|------|-------------------|
| GPU Nodes | 2x A10G (24GB) | ~$1,200 |
| CPU Nodes | 3x t3.xlarge | ~$300 |
| PostgreSQL | RDS db.t3.medium | ~$100 |
| Redis | ElastiCache t3.small | ~$50 |
| Pinecone | Standard (10M vectors) | ~$70 |
| Load Balancer | ALB | ~$20 |
| Storage | 500GB EBS | ~$50 |
| **Total** | | **~$1,790/month** |

### Cost Optimization

- Use 4-bit quantized LLM → Save 50% GPU cost
- Use spot instances for workers → Save 70%
- Cache embeddings → Reduce API calls
- Batch processing → Better GPU utilization

**Optimized:** ~$800-1,000/month

---

## 7. Performance Targets

### Latency Targets

| Operation | Target | Acceptable | Poor |
|-----------|--------|------------|------|
| Document upload | <1s | <3s | >5s |
| Query embedding | <50ms | <100ms | >200ms |
| Vector search | <200ms | <500ms | >1s |
| Reranking | <80ms | <150ms | >300ms |
| LLM first token | <500ms | <1s | >2s |
| LLM token rate | >30/sec | >20/sec | <10/sec |
| **End-to-end (first token)** | **<600ms** | **<1s** | **>2s** |

### Throughput Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Concurrent users | 100+ | Per GPU replica |
| Documents/hour | 100+ | With 4 workers |
| Queries/sec | 10-20 | Per LLM replica |
| Embeddings/sec | 1000+ | Per GPU |

### Availability Targets

| Metric | Target |
|--------|--------|
| Uptime | 99.5% (SLA) |
| Error rate | <1% |
| P95 latency | <2s |

---

## 8. Security Considerations

### Data Security

- ✅ JWT authentication
- ✅ Password hashing (bcrypt)
- ✅ User data isolation (Pinecone filters)
- ✅ HTTPS/TLS in production
- ✅ Input validation (Pydantic)
- ✅ Rate limiting
- ✅ File type validation

### Privacy

- ✅ No data sent to third-party APIs (self-hosted models)
- ✅ User documents isolated per user_id
- ✅ No cross-user data leakage
- ✅ Audit logs for compliance

### Compliance

- ✅ GDPR-ready (data deletion, export)
- ✅ SOC 2 considerations (audit logs, encryption)
- ✅ HIPAA considerations (PHI handling if needed)

---

## 9. Deployment Roadmap

### Stage 1: Local Development (Week 1-2)

```bash
├── Setup Docker Compose
├── Create database schemas
├── Implement core services
├── Test document upload
└── Test basic RAG pipeline
```

### Stage 2: MVP (Week 3-6)

```bash
├── Complete all microservices
├── Implement frontend
├── Add authentication
├── Deploy to staging (K8s)
└── Testing & bug fixes
```

### Stage 3: Production Features (Week 7-10)

```bash
├── Add streaming responses
├── Implement observability
├── Performance optimization
├── Load testing
└── Production deployment
```

### Stage 4: Advanced Features (Week 11-13)

```bash
├── Hybrid retrieval + reranking
├── Semantic chunking
├── User feedback loop
└── Analytics dashboard
```

---

## 10. Success Metrics

### Technical Metrics

- ✅ P95 query latency < 2s
- ✅ Document processing < 5 min (100 pages)
- ✅ Error rate < 1%
- ✅ GPU utilization 70-90%

### Business Metrics

- ✅ User retention rate
- ✅ Documents processed/day
- ✅ Queries/user/session
- ✅ User satisfaction score

### RAG Quality Metrics

- ✅ Retrieval recall@5 > 80%
- ✅ Retrieval precision@5 > 60%
- ✅ Answer accuracy (human eval)
- ✅ Citation accuracy

---

## 11. References

### Design Documents

1. [Backend Architecture](backend/architecture.md) - Microservices design
2. [Data Flow](backend/data-flow.md) - RAG pipeline details
3. [Deployment](backend/deployment.md) - K8s manifests
4. [Observability](backend/observability.md) - Monitoring strategy
5. [Project Structure](backend/project-structure.md) - Code organization
6. [GenAI Tech Stack](../GEN-AI/tech-stack.md) - Model selection
7. [Frontend Stack](../UI/frontend-stack.md) - Next.js architecture

### External Resources

- [Llama 3.1 Paper](https://ai.meta.com/research/publications/llama-3-1/)
- [BGE-M3 Paper](https://arxiv.org/abs/2402.03216)
- [vLLM Documentation](https://docs.vllm.ai/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Next.js 14 Docs](https://nextjs.org/docs)

---

## 12. Next Steps

### For Developers

1. Read all design documents in `/docs/desing-docs/`
2. Set up local development environment
3. Review microservices architecture
4. Start implementing services (see project structure)

### For DevOps

1. Review Kubernetes manifests in `/k8s/`
2. Set up monitoring (Prometheus + Grafana)
3. Configure CI/CD pipelines
4. Plan GPU node provisioning

### For Product

1. Review feature roadmap (Phase 1-3)
2. Define success metrics
3. Plan user testing
4. Create onboarding content

---

## Conclusion

This enterprise RAG system represents **modern best practices (2025-2026)** for building production GenAI applications with:

- ✅ **Free, open-source models** (no vendor lock-in)
- ✅ **Microservices architecture** (scalable, maintainable)
- ✅ **Production infrastructure** (K8s, observability)
- ✅ **Modern frontend** (Next.js, streaming)
- ✅ **Enterprise features** (auth, multi-user, citations)

The complete design is documented across 7 comprehensive documents totaling **25,000+ words** covering every aspect of the system.

**Ready to build? Start with `make dev` and follow the Quick Start guide in the main README.**

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** Architecture Team  
**Status:** Design Complete ✅

