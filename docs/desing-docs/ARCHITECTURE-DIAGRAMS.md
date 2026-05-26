# Architecture Diagrams - Enterprise RAG System

## 1. Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              CLIENT LAYER                                       │
│                                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────┐    ┌─────────────────┐  │
│  │                      │    │                      │    │                 │  │
│  │   Web Application    │    │   Mobile (Future)    │    │   Admin CLI     │  │
│  │   (Next.js 14)       │    │   (React Native)     │    │   (Python)      │  │
│  │                      │    │                      │    │                 │  │
│  │  • Streaming Chat    │    │  • Document Upload   │    │  • Monitoring   │  │
│  │  • Document Upload   │    │  • Chat Interface    │    │  • Management   │  │
│  │  • Authentication    │    │  • Offline Support   │    │  • Scripts      │  │
│  │                      │    │                      │    │                 │  │
│  └──────────┬───────────┘    └──────────┬───────────┘    └────────┬────────┘  │
│             │                           │                         │            │
└─────────────┼───────────────────────────┼─────────────────────────┼────────────┘
              │                           │                         │
              └───────────────┬───────────┴─────────────────────────┘
                              │ HTTPS/WSS
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                            EDGE LAYER (Optional)                                │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        NGINX Ingress / Kong                              │   │
│  │  • TLS Termination                                                       │   │
│  │  • Load Balancing                                                        │   │
│  │  • Rate Limiting (Layer 7)                                               │   │
│  │  • DDoS Protection                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
└──────────────────────────────────────┼──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                            API GATEWAY LAYER                                    │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Gateway (3+ replicas)                         │   │
│  │                                                                          │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │   │
│  │  │ Authentication   │  │ Rate Limiting    │  │ Request Routing  │     │   │
│  │  │ • JWT Verify     │  │ • Per-user limit │  │ • Path-based     │     │   │
│  │  │ • Token Refresh  │  │ • Redis-backed   │  │ • Load balance   │     │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘     │   │
│  │                                                                          │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │   │
│  │  │ CORS Handling    │  │ Input Validation │  │ Error Handling   │     │   │
│  │  │ • Whitelist      │  │ • Pydantic       │  │ • Retry logic    │     │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘     │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
└──────────────────────────────────────┼──────────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│                  │       │                  │       │                  │
│  User Service    │       │ Document Service │       │  Chat Service    │
│                  │       │                  │       │                  │
│  • Registration  │       │  • Upload        │       │  • Query         │
│  • Login         │       │  • List          │       │  • Streaming     │
│  • Profile       │       │  • Delete        │       │  • History       │
│  • Permissions   │       │  • Metadata      │       │  • Sessions      │
│                  │       │                  │       │                  │
└──────────────────┘       └──────────────────┘       └──────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                          PROCESSING LAYER                                       │
│                                                                                 │
│  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐   │
│  │                  │       │                  │       │                  │   │
│  │ Ingestion Svc    │       │ Retrieval Svc    │       │ Worker Service   │   │
│  │                  │       │                  │       │                  │   │
│  │ • PDF Parse      │       │ • Embed Query    │       │ • Celery Workers │   │
│  │ • TXT Parse      │       │ • Vector Search  │       │ • Task Queue     │   │
│  │ • Chunking       │       │ • Reranking      │       │ • Retry Logic    │   │
│  │ • Metadata       │       │ • Context Build  │       │ • Batch Process  │   │
│  │                  │       │                  │       │                  │   │
│  └──────┬───────────┘       └──────────────────┘       └──────────────────┘   │
│         │                                                                       │
└─────────┼───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                      ML / AI LAYER (GPU Nodes)                                  │
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                         GPU Node Pool                                  │    │
│  │                                                                        │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │    │
│  │  │                  │  │                  │  │                  │    │    │
│  │  │ Embedding Svc    │  │ Reranker Svc     │  │ LLM Service      │    │    │
│  │  │                  │  │                  │  │                  │    │    │
│  │  │ Model: BGE-M3    │  │ Model:           │  │ Model: Llama     │    │    │
│  │  │ GPU: T4 (4GB)    │  │  BGE-reranker    │  │  3.1-8B-Instruct │    │    │
│  │  │ Replicas: 2-3    │  │ GPU: T4 (4GB)    │  │ GPU: A10G (24GB) │    │    │
│  │  │                  │  │ Replicas: 1-2    │  │ Replicas: 2+     │    │    │
│  │  │ ┌──────────────┐ │  │                  │  │                  │    │    │
│  │  │ │ Batch Embed  │ │  │ ┌──────────────┐ │  │ ┌──────────────┐ │    │    │
│  │  │ │ • 32 per call│ │  │ │ Score pairs  │ │  │ │ vLLM Server  │ │    │    │
│  │  │ │ • Normalize  │ │  │ │ • Top-K      │ │  │ │ • Streaming  │ │    │    │
│  │  │ └──────────────┘ │  │ └──────────────┘ │  │ │ • Batching   │ │    │    │
│  │  │                  │  │                  │  │ └──────────────┘ │    │    │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘    │    │
│  │                                                                        │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                            DATA LAYER                                           │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             │
│  │                  │  │                  │  │                  │             │
│  │  PostgreSQL 16   │  │   Redis 7        │  │  Pinecone        │             │
│  │                  │  │                  │  │                  │             │
│  │  • Users         │  │  • Cache         │  │  • Vectors       │             │
│  │  • Documents     │  │  • Celery Queue  │  │  • Metadata      │             │
│  │  • Chunks        │  │  • Sessions      │  │  • Similarity    │             │
│  │  • Chat History  │  │  • Rate Limits   │  │    Search        │             │
│  │                  │  │                  │  │                  │             │
│  │  Replicas: 1+1   │  │  Replicas: 3     │  │  API: Cloud      │             │
│  │  (Primary+Standby│  │  (Sentinel)      │  │  Index: 1024-dim │             │
│  │                  │  │                  │  │                  │             │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘             │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      File Storage (Kubernetes PVC)                       │   │
│  │                                                                          │   │
│  │  /data/uploads/{user_id}/{document_id}/                                 │   │
│  │    ├── original.pdf                                                     │   │
│  │    ├── extracted_text.txt                                               │   │
│  │    └── metadata.json                                                    │   │
│  │                                                                          │   │
│  │  Storage Class: ReadWriteMany (NFS / EFS)                               │   │
│  │  Capacity: 500GB - 2TB                                                  │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                      OBSERVABILITY LAYER                                        │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             │
│  │                  │  │                  │  │                  │             │
│  │  Prometheus      │  │   Grafana        │  │  LangFuse        │             │
│  │                  │  │                  │  │                  │             │
│  │  • Scrape /metrics│ │  • Dashboards    │  │  • RAG Tracing   │             │
│  │  • Alert Rules   │  │  • Alerts        │  │  • LLM Metrics   │             │
│  │  • Time Series   │  │  • Visualization │  │  • User Feedback │             │
│  │                  │  │                  │  │                  │             │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘             │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             │
│  │                  │  │                  │  │                  │             │
│  │  Jaeger          │  │  FluentD         │  │  Alertmanager    │             │
│  │  (Tracing)       │  │  (Logs)          │  │  (Alerts)        │             │
│  │                  │  │                  │  │                  │             │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. RAG Pipeline Detailed Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                     USER QUERY: "What is X in document Y?"             │
└───────────────────────────────┬────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        STAGE 1: Query Processing                        │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Chat Service                                                     │ │
│  │  • Validate input (max length, sanitize)                          │ │
│  │  • Extract session_id, document_ids                               │ │
│  │  • Store user message → PostgreSQL                                │ │
│  │  • Generate correlation_id for tracing                            │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STAGE 2: Retrieval Pipeline                         │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Step 2.1: Embed Query (Embedding Service)                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  Input: "What is X in document Y?"                          │ │ │
│  │  │  Prefix: "Represent this query for retrieving: "            │ │ │
│  │  │  Model: BAAI/bge-m3                                         │ │ │
│  │  │  Output: [1024] float vector                                │ │ │
│  │  │  Latency: ~20-50ms (GPU)                                    │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                │                                        │
│                                ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Step 2.2: Vector Search (Pinecone)                              │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  Index: enterprise-rag-vectors                              │ │ │
│  │  │  Query Vector: [1024]                                       │ │ │
│  │  │  Filters: {user_id: "abc", document_id: {$in: [...]}}      │ │ │
│  │  │  Top-K: 50                                                  │ │ │
│  │  │  Metric: cosine                                             │ │ │
│  │  │  Results: 50 chunks with scores (0.75 - 0.95)              │ │ │
│  │  │  Latency: ~100-200ms                                        │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                │                                        │
│                                ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Step 2.3: Reranking (Reranker Service)                          │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  Input: Query + 50 candidate chunks                         │ │ │
│  │  │  Model: BAAI/bge-reranker-v2-m3 (cross-encoder)            │ │ │
│  │  │  Process: Score each (query, chunk) pair                    │ │ │
│  │  │  Output: Reranked scores (0.0 - 1.0)                       │ │ │
│  │  │  Top-K: 5 (highest precision chunks)                       │ │ │
│  │  │  Latency: ~30-80ms (GPU)                                    │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                │                                        │
│                                ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Step 2.4: Context Building (Retrieval Service)                  │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  Top 5 chunks → Format with citations                       │ │ │
│  │  │  [Source 1] (Doc: abc, Page: 5)                            │ │ │
│  │  │  Content from page 5...                                     │ │ │
│  │  │                                                              │ │ │
│  │  │  [Source 2] (Doc: abc, Page: 7)                            │ │ │
│  │  │  Content from page 7...                                     │ │ │
│  │  │                                                              │ │ │
│  │  │  Token Budget: ~2048 tokens max                            │ │ │
│  │  │  Latency: ~10ms                                             │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STAGE 3: Prompt Construction                        │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Chat Service - Prompt Builder                                    │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  System Prompt:                                             │ │ │
│  │  │    "You are a helpful assistant. Answer based on context..."│ │ │
│  │  │                                                              │ │ │
│  │  │  Context:                                                    │ │ │
│  │  │    [Retrieved chunks with citations]                        │ │ │
│  │  │                                                              │ │ │
│  │  │  Conversation History (last 3 turns):                       │ │ │
│  │  │    User: "Previous question"                                │ │ │
│  │  │    Assistant: "Previous answer"                             │ │ │
│  │  │                                                              │ │ │
│  │  │  Current Question:                                           │ │ │
│  │  │    "What is X in document Y?"                               │ │ │
│  │  │                                                              │ │ │
│  │  │  Total Tokens: ~2500                                        │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STAGE 4: LLM Generation (Streaming)                 │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  LLM Service (vLLM - Llama 3.1-8B-Instruct)                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  Inference Parameters:                                       │ │ │
│  │  │  • temperature: 0.1 (factual, less creative)                │ │ │
│  │  │  • max_tokens: 512                                          │ │ │
│  │  │  • stream: true (SSE)                                       │ │ │
│  │  │  • top_p: 0.9                                               │ │ │
│  │  │                                                              │ │ │
│  │  │  Generation Flow:                                            │ │ │
│  │  │  1. First token: ~150-300ms                                 │ │ │
│  │  │  2. Stream tokens: ~20-30ms per token                       │ │ │
│  │  │  3. Average: 30-50 tokens/sec                               │ │ │
│  │  │                                                              │ │ │
│  │  │  Token Stream:                                               │ │ │
│  │  │  "X" → " is" → " a" → " concept" → " that" → "..."        │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                │                                        │
│                                │ SSE Stream                             │
│                                ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Chat Service - Stream Handler                                    │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  For each token:                                            │ │ │
│  │  │  1. Receive from vLLM                                       │ │ │
│  │  │  2. Append to message buffer                                │ │ │
│  │  │  3. Stream to frontend via SSE                              │ │ │
│  │  │  4. Update metrics                                          │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STAGE 5: Response Finalization                      │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Chat Service - Completion Handler                                │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  1. Full answer accumulated: ~200 tokens                    │ │ │
│  │  │  2. Store to PostgreSQL:                                    │ │ │
│  │  │     • session_id                                            │ │ │
│  │  │     • role: "assistant"                                     │ │ │
│  │  │     • content: full answer                                  │ │ │
│  │  │     • sources: [citations with metadata]                    │ │ │
│  │  │     • token_count: 200                                      │ │ │
│  │  │  3. Send "done" event to frontend                           │ │ │
│  │  │  4. Log to observability (LangFuse trace)                   │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND DISPLAY                                   │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  User sees:                                                        │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │  💬 Assistant:                                              │ │ │
│  │  │  X is a concept that appears in document Y on page 5.       │ │ │
│  │  │  It refers to... [streaming text]                           │ │ │
│  │  │                                                              │ │ │
│  │  │  📎 Sources:                                                │ │ │
│  │  │  • Page 5 (Score: 0.92)                                     │ │ │
│  │  │  • Page 7 (Score: 0.88)                                     │ │ │
│  │  │  • Page 12 (Score: 0.85)                                    │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Total Latency Breakdown:
• Query embedding: ~50ms
• Vector search: ~150ms
• Reranking: ~60ms
• Prompt build: ~10ms
• LLM first token: ~250ms
• LLM streaming: ~5-10s (for 200 tokens)
──────────────────────────────────
• Time to first token: ~520ms ✅
• Full response: ~6-11s ✅
```

---

## 3. Document Processing Flow

```
┌────────────────────────────────────────────────────────────────────┐
│              USER UPLOADS: document.pdf (100 pages)                │
└───────────────────────────┬────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Upload & Validation (Document Service)                    │
│  • Check file type: ✅ PDF                                          │
│  • Check size: ✅ 45MB < 50MB limit                                 │
│  • Generate document_id: "abc-123-def-456"                          │
│  • Save to: /data/uploads/user_abc/abc-123-def-456/original.pdf    │
│  • Insert PostgreSQL: status="pending"                              │
│  • Publish Redis event: "document.uploaded"                         │
│  Latency: ~2-5s (network + disk I/O)                                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: Celery Worker Pickup                                      │
│  • Worker consumes from queue: "document_ingestion"                 │
│  • Load document record from PostgreSQL                             │
│  • Update status: "processing"                                      │
│  Latency: ~100ms (queue polling)                                    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: PDF Parsing (Ingestion Service)                           │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Tool: pypdfium2 (fast path)                                  │ │
│  │  Process:                                                      │ │
│  │  • Open PDF                                                    │ │
│  │  • For each page (1-100):                                      │ │
│  │    - Extract text                                              │ │
│  │    - Extract metadata (page numbers, headings)                 │ │
│  │  • Save to: /data/uploads/.../extracted_text.txt               │ │
│  │  Result: 100 pages → ~200KB text                               │ │
│  │  Latency: ~0.5-2s per page = ~50-200s total                    │ │
│  └───────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: Text Chunking (Ingestion Service)                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Strategy: RecursiveCharacterTextSplitter                      │ │
│  │  Parameters:                                                   │ │
│  │  • chunk_size: 512 chars (~400 tokens)                         │ │
│  │  • chunk_overlap: 50 chars (10%)                               │ │
│  │  • separators: ["\n\n", "\n", ". ", " ", ""]                   │ │
│  │                                                                 │ │
│  │  Process:                                                       │ │
│  │  • Split text at paragraph boundaries first                    │ │
│  │  • If too large, split at sentence boundaries                  │ │
│  │  • Preserve page numbers                                       │ │
│  │  • Add metadata: {page, index, char_count, token_count}        │ │
│  │                                                                 │ │
│  │  Result: 100 pages → ~400 chunks                               │ │
│  │  Latency: ~100-500ms                                            │ │
│  └───────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: Save Chunks to PostgreSQL                                 │
│  • Batch insert 400 chunks                                          │
│  • Each chunk record:                                               │
│    {id, document_id, chunk_index, content, page_number, metadata}   │
│  • Update documents.total_chunks = 400                              │
│  Latency: ~500ms                                                    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6: Queue Embedding Tasks (Batch of 32)                       │
│  • Split 400 chunks into batches: 13 batches × 32 chunks            │
│  • Publish 13 tasks to Redis: "embedding_generation" queue          │
│  Latency: ~100ms                                                    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 7: Embedding Generation (Parallel Workers)                   │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Worker 1-4 process batches in parallel                        │ │
│  │                                                                 │ │
│  │  For batch of 32 chunks:                                       │ │
│  │  1. Load chunks from PostgreSQL                                │ │
│  │  2. Call Embedding Service:                                    │ │
│  │     POST /embed/documents                                      │ │
│  │     {texts: [32 chunks]}                                       │ │
│  │  3. Embedding Service (BGE-M3):                                │ │
│  │     • model.encode(texts, batch_size=32)                       │ │
│  │     • Normalize embeddings                                     │ │
│  │     • Return: [[1024] × 32]                                    │ │
│  │     • Latency: ~1-3s per batch (GPU)                           │ │
│  │  4. Upsert to Pinecone:                                        │ │
│  │     pinecone.upsert(vectors=[                                  │ │
│  │       {id, values: [1024], metadata: {doc_id, page, ...}}      │ │
│  │     ])                                                          │ │
│  │     • Latency: ~200-500ms per batch                            │ │
│  │  5. Update PostgreSQL chunks.embedding_id                      │ │
│  │                                                                 │ │
│  │  Total per batch: ~2-4s                                        │ │
│  │  With 4 parallel workers: ~13 batches / 4 = ~3-4 batches/worker│ │
│  │  Total time: ~3-4 batches × 3s = ~10-15s                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 8: Finalization                                               │
│  • All batches complete                                             │
│  • Update PostgreSQL documents:                                     │
│    - status = "completed"                                           │
│    - total_pages = 100                                              │
│    - total_chunks = 400                                             │
│    - processed_at = now()                                           │
│  • Send notification to frontend (WebSocket/polling)                │
│  Latency: ~100ms                                                    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   PROCESSING COMPLETE ✅                             │
│                                                                     │
│  Total Time: ~2-5 minutes for 100 pages                             │
│                                                                     │
│  Breakdown:                                                         │
│  • Upload: 3s                                                       │
│  • PDF Parse: 60s                                                   │
│  • Chunking: 0.5s                                                   │
│  • DB Save: 0.5s                                                    │
│  • Embeddings (parallel): 15s                                       │
│  • Pinecone upsert: 7s                                              │
│  • Finalization: 0.1s                                               │
│  ────────────────────────                                           │
│  Total: ~86s (~1.5 minutes) ✅                                       │
│                                                                     │
│  Document is now searchable! 🎉                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** System Architecture Team

