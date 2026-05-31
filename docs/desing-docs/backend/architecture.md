# System Architecture - Enterprise RAG Platform

> **⚠️ Local Mac Dev Note:** This document shows the target production architecture.
> For **current local Mac development**, the LLM layer uses **Ollama** (not vLLM).
> vLLM requires a CUDA GPU and does not run on Mac.
> All other services (embeddings, reranker, Postgres, Redis) run on CPU in Docker.
> Pinecone is the only cloud service.
> See `docs/implementation-plan/DEV-SETUP-GUIDE.md` for the local workflow.

## Executive Summary

This document defines the **microservices architecture** for a production-grade RAG platform supporting multi-user document Q&A with streaming responses, built on Python, PostgreSQL, Redis, and Pinecone.

**Key Principles:**
- Microservices architecture (Docker + Kubernetes ready)
- Event-driven document processing
- Asynchronous task processing
- Horizontal scalability
- Service isolation and fault tolerance

---

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Web App    │  │  Mobile App  │  │   CLI Tool   │           │
│  │  (Next.js)   │  │  (Optional)  │  │   (Admin)    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       API GATEWAY                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   FastAPI Gateway (NGINX/Kong Optional)                  │   │
│  │   - Authentication (JWT)                                 │   │
│  │   - Rate limiting                                        │   │
│  │   - Request routing                                      │   │
│  │   - CORS handling                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
┌───────────────────┐ ┌──────────────┐ ┌──────────────┐
│   USER SERVICE    │ │ CHAT SERVICE │ │ DOC SERVICE  │
│   - Auth          │ │ - Streaming  │ │ - Upload     │
│   - Profiles      │ │ - History    │ │ - List/Del   │
│   - Permissions   │ │ - Sessions   │ │ - Metadata   │
└───────────────────┘ └──────────────┘ └──────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    CORE PROCESSING LAYER                          │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐              │
│  │  INGESTION  │ │  RETRIEVAL  │ │ GENERATION   │              │
│  │  SERVICE    │ │  SERVICE    │ │ SERVICE      │              │
│  │             │ │             │ │              │              │
│  │ - PDF Parse │ │ - Query     │ │ - Prompt     │              │
│  │ - Chunking  │ │ - Rerank    │ │ - Stream     │              │
│  │ - Queue Job │ │ - Citation  │ │ - Context    │              │
│  └─────────────┘ └─────────────┘ └──────────────┘              │
└──────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│   WORKER     │    │   ML SERVICES    │    │   STORAGE   │
│   SERVICE    │    │                  │    │   LAYER     │
│              │    │ ┌──────────────┐ │    │             │
│ - Celery     │───▶│ │  EMBEDDING   │ │    │ PostgreSQL  │
│ - Redis      │    │ │  SERVICE     │ │    │ Redis       │
│ - Task Queue │    │ └──────────────┘ │    │ Pinecone    │
│              │    │ ┌──────────────┐ │    │ FileSystem  │
│              │───▶│ │  LLM SERVICE │ │    │             │
│              │    │ │  (vLLM)      │ │    │             │
│              │    │ └──────────────┘ │    │             │
│              │    │ ┌──────────────┐ │    │             │
│              │───▶│ │  RERANKER    │ │    │             │
│              │    │ │  SERVICE     │ │    │             │
│              │    │ └──────────────┘ │    │             │
└──────────────┘    └──────────────────┘    └─────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   OBSERVABILITY LAYER                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  Prometheus  │ │   Grafana    │ │   LangFuse   │            │
│  │  (Metrics)   │ │ (Dashboards) │ │  (Tracing)   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Breakdown

### **2.1 API Gateway Service**

**Responsibilities:**
- Single entry point for all client requests
- Authentication & authorization (JWT)
- Rate limiting per user/plan
- Request validation
- CORS handling
- Load balancing to backend services

**Technology:**
- **Framework:** FastAPI
- **Auth:** JWT (PyJWT)
- **Rate Limiting:** SlowAPI or Redis-based
- **Optional:** NGINX/Kong for advanced routing

**Endpoints:**
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh

POST   /api/v1/documents/upload
GET    /api/v1/documents
DELETE /api/v1/documents/{id}

POST   /api/v1/chat/query (streaming)
GET    /api/v1/chat/sessions
GET    /api/v1/chat/history/{session_id}

GET    /api/v1/health
GET    /api/v1/metrics
```

**Deployment:**
```yaml
Replicas: 3+
CPU: 0.5 cores
RAM: 512MB
Scaling: HPA (CPU/Request rate)
```

---

### **2.2 User Service**

**Responsibilities:**
- User registration & authentication
- Profile management
- Permission management
- Multi-tenant isolation

**Database Schema:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON user_sessions(token_hash);
```

---

### **2.3 Document Service**

**Responsibilities:**
- File upload handling (PDF, TXT)
- File validation (size, type, virus scan)
- Metadata management
- Document listing & deletion
- Trigger ingestion pipeline

**Database Schema:**
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    total_pages INTEGER,
    total_chunks INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);

CREATE TABLE document_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value TEXT,
    UNIQUE(document_id, key)
);
```

**File Storage:**
```python
# Local filesystem with organized structure
/data/uploads/
  ├── {user_id}/
  │   ├── {document_id}/
  │   │   ├── original.pdf
  │   │   ├── metadata.json
  │   │   └── extracted_text.txt
```

**Flow:**
```
1. Client uploads file → API Gateway
2. Document Service validates file
3. Save to filesystem at /data/uploads/{user_id}/{doc_id}/
4. Insert record in PostgreSQL
5. Publish event to Redis queue: "document.uploaded"
6. Return document_id to client
```

---

### **2.4 Ingestion Service**

**Responsibilities:**
- PDF/TXT parsing
- Text extraction
- Document chunking
- Metadata extraction (page numbers, sections)
- Queue embedding tasks
- Update document status

**Database Schema:**
```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    char_count INTEGER,
    token_count INTEGER,
    embedding_id VARCHAR(255), -- Pinecone ID
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_embedding_id ON chunks(embedding_id);
```

**Processing Pipeline:**
```python
# Triggered by worker consuming "document.uploaded" event

def process_document(document_id: str):
    # 1. Load document from filesystem
    doc = load_document(document_id)
    
    # 2. Parse PDF/TXT
    if doc.file_type == 'pdf':
        pages = parse_pdf(doc.storage_path)
    else:
        pages = parse_txt(doc.storage_path)
    
    # 3. Chunk text
    chunks = chunk_document(
        pages,
        chunk_size=512,
        chunk_overlap=50,
        preserve_page_numbers=True
    )
    
    # 4. Save chunks to PostgreSQL
    for idx, chunk in enumerate(chunks):
        db.save_chunk(
            document_id=document_id,
            chunk_index=idx,
            content=chunk.text,
            page_number=chunk.page,
            metadata=chunk.metadata
        )
    
    # 5. Queue embedding tasks
    for chunk in chunks:
        publish_event("chunk.ready_for_embedding", {
            "chunk_id": chunk.id,
            "document_id": document_id
        })
    
    # 6. Update document status
    db.update_document(document_id, status="processing")
```

---

### **2.5 Worker Service (Celery)**

**Responsibilities:**
- Asynchronous task processing
- Document ingestion orchestration
- Embedding generation
- Batch operations
- Retry logic

**Architecture:**
```
┌─────────────────────────────────────────┐
│          REDIS BROKER                   │
│  Queues:                                │
│  - document_ingestion (priority: high)  │
│  - embedding_generation (priority: med) │
│  - batch_processing (priority: low)     │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│        CELERY WORKERS                   │
│  ┌────────────────────────────────┐    │
│  │  Worker Pool (4-8 processes)   │    │
│  │  - document_processor_task     │    │
│  │  - embedding_generator_task    │    │
│  │  - batch_embedding_task        │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Celery Configuration:**
```python
# celery_config.py

from celery import Celery

app = Celery(
    'enterprise_rag',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/1'
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Queue routing
    task_routes={
        'tasks.process_document': {'queue': 'document_ingestion'},
        'tasks.generate_embeddings': {'queue': 'embedding_generation'},
        'tasks.batch_process': {'queue': 'batch_processing'},
    },
    
    # Priority
    broker_transport_options={
        'priority_steps': [0, 3, 6, 9],  # low, medium, high, critical
    }
)
```

**Task Definitions:**
```python
# tasks.py

@app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    try:
        ingestion_service.process_document(document_id)
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

@app.task(bind=True, max_retries=3)
def generate_embeddings_task(self, chunk_ids: List[str]):
    try:
        embedding_service.batch_embed_chunks(chunk_ids)
    except Exception as exc:
        self.retry(exc=exc, countdown=30)
```

**Deployment:**
```yaml
Replicas: 2-4 (autoscale)
CPU: 2 cores
RAM: 4GB
Concurrency: 4 processes per worker
```

---

### **2.6 Embedding Service**

**Responsibilities:**
- Generate embeddings for documents
- Generate embeddings for queries
- Batch processing
- Model serving (BGE-M3)

**Consistency Rule:**
- Use the **same embedding model** for document chunks and user queries
- In this architecture, both flows use `BAAI/bge-m3`
- Query embeddings may add the BGE retrieval instruction prefix, but they must still be generated by the same BGE-M3 model used during document ingestion

**API Design:**
```python
# FastAPI endpoints

@app.post("/embed/documents")
async def embed_documents(texts: List[str]) -> List[List[float]]:
    """Batch embed multiple documents"""
    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True
    )
    return embeddings.tolist()

@app.post("/embed/query")
async def embed_query(text: str) -> List[float]:
    """Embed single query with instruction prefix"""
    instruction = "Represent this query for retrieving relevant documents: "
    embedding = model.encode(
        instruction + text,
        normalize_embeddings=True
    )
    return embedding.tolist()
```

**Integration with Pinecone:**
```python
# After embedding generation, upsert to Pinecone

def store_embeddings(chunk_id: str, embedding: List[float], metadata: dict):
    pinecone_index.upsert(vectors=[{
        "id": chunk_id,
        "values": embedding,
        "metadata": {
            "document_id": metadata["document_id"],
            "user_id": metadata["user_id"],
            "chunk_index": metadata["chunk_index"],
            "page_number": metadata["page_number"],
            "content": metadata["content"][:1000],  # Truncate for metadata
            "created_at": metadata["created_at"]
        }
    }])
```

**Deployment:**
```yaml
Replicas: 2-3
GPU: 1x T4 (4GB VRAM)
CPU: 4 cores
RAM: 8GB
Model: BAAI/bge-m3
Scaling: HPA on GPU utilization
```

---

### **2.7 Retrieval Service**

**Responsibilities:**
- Query Pinecone for similar chunks
- Rerank results
- Apply metadata filters
- Citation generation
- Context preparation for LLM

**API Design:**
```python
@app.post("/retrieve")
async def retrieve(
    query: str,
    user_id: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = 20,
    rerank_top_k: int = 5
) -> RetrievalResponse:
    """
    Multi-stage retrieval:
    1. Embed query
    2. Search Pinecone (top_k)
    3. Apply filters
    4. Rerank (rerank_top_k)
    5. Prepare context
    """
    
    # Stage 1: Embed query
    query_embedding = await embedding_service.embed_query(query)
    
    # Stage 2: Vector search
    results = pinecone_index.query(
        vector=query_embedding,
        top_k=top_k,
        filter={"user_id": user_id, **({"document_id": {"$in": document_ids}} if document_ids else {})}
    )
    
    # Stage 3: Rerank
    reranked = reranker_service.rerank(
        query=query,
        documents=[r.metadata["content"] for r in results.matches]
    )
    
    # Stage 4: Prepare context
    context = prepare_context(reranked[:rerank_top_k])
    
    return {
        "context": context,
        "sources": [
            {
                "document_id": r.metadata["document_id"],
                "page_number": r.metadata["page_number"],
                "chunk_index": r.metadata["chunk_index"],
                "score": r.score,
                "content": r.metadata["content"]
            }
            for r in reranked[:rerank_top_k]
        ]
    }
```

---

### **2.8 Reranker Service**

**Responsibilities:**
- Cross-encoder reranking
- Score normalization
- Batch processing

**API Design:**
```python
@app.post("/rerank")
async def rerank(query: str, documents: List[str], top_k: int = 5):
    """Rerank documents using cross-encoder"""
    
    # Create query-document pairs
    pairs = [(query, doc) for doc in documents]
    
    # Score with cross-encoder
    scores = model.predict(pairs)
    
    # Sort and return top K
    ranked = sorted(
        zip(documents, scores),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]
    
    return {
        "ranked_documents": [
            {"document": doc, "score": float(score)}
            for doc, score in ranked
        ]
    }
```

**Deployment:**
```yaml
Replicas: 1-2
GPU: Shared with embedding service
CPU: 2 cores
RAM: 4GB
Model: BAAI/bge-reranker-v2-m3
```

---

### **2.9 LLM Service (vLLM)**

**Responsibilities:**
- Text generation
- Streaming responses
- Prompt management
- Token management

**Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-service
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        args:
          - --model=meta-llama/Meta-Llama-3.1-8B-Instruct
          - --dtype=float16
          - --max-model-len=8192
          - --served-model-name=llama-3.1-8b
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: 20Gi
          requests:
            nvidia.com/gpu: 1
            memory: 16Gi
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 120
          periodSeconds: 30
```

**Client Integration:**
```python
from openai import OpenAI

llm_client = OpenAI(
    base_url="http://vllm-service:8000/v1",
    api_key="not-needed"
)

async def generate_answer(query: str, context: str) -> AsyncGenerator:
    prompt = f"""You are a helpful assistant. Answer the question based on the provided context.

Context:
{context}

Question: {query}

Answer:"""

    stream = llm_client.chat.completions.create(
        model="llama-3.1-8b",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        temperature=0.1,
        max_tokens=512
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

---

### **2.10 Chat Service**

**Responsibilities:**
- Orchestrate RAG pipeline
- Manage chat sessions
- Stream responses to client
- Store conversation history

**Database Schema:**
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources JSONB, -- Citation metadata
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
```

**Streaming Endpoint:**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

@app.post("/chat/query")
async def chat_query(
    query: str,
    session_id: Optional[str] = None,
    document_ids: Optional[List[str]] = None
):
    """Stream RAG response"""
    
    # Create or get session
    if not session_id:
        session = create_chat_session(user_id)
        session_id = session.id
    
    # Store user message
    store_message(session_id, role="user", content=query)
    
    async def generate():
        # Step 1: Retrieve context
        retrieval_result = await retrieval_service.retrieve(
            query=query,
            user_id=user_id,
            document_ids=document_ids
        )
        
        # Step 2: Generate answer (streaming)
        full_answer = ""
        async for chunk in llm_service.generate_answer(
            query=query,
            context=retrieval_result.context
        ):
            full_answer += chunk
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        
        # Step 3: Send sources
        yield f"data: {json.dumps({'type': 'sources', 'sources': retrieval_result.sources})}\n\n"
        
        # Step 4: Store assistant message
        store_message(
            session_id,
            role="assistant",
            content=full_answer,
            sources=retrieval_result.sources
        )
        
        yield "data: {\"type\": \"done\"}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 3. Data Storage Architecture

### **3.1 PostgreSQL**

**Purpose:** Relational data (users, documents, chunks, chat history)

**Schema Summary:**
- `users` - User accounts
- `user_sessions` - JWT sessions
- `documents` - Document metadata
- `document_metadata` - Key-value metadata
- `chunks` - Chunked text with references
- `chat_sessions` - Conversation threads
- `messages` - Individual messages with sources

**Configuration:**
```yaml
# PostgreSQL deployment
Replicas: 1 (with standby for HA)
Storage: 100GB PVC
Connection Pool: PgBouncer (100 connections)
Backups: Daily via pg_dump to persistent volume
```

### **3.2 Redis**

**Purpose:** 
- Celery broker & result backend
- Caching layer
- Rate limiting
- Session storage

**Data Types:**
```
# Celery queues
celery:queue:document_ingestion
celery:queue:embedding_generation

# Cache
cache:embedding:{text_hash} -> List[float]
cache:document:{doc_id} -> JSON

# Rate limiting
ratelimit:user:{user_id}:api_calls -> Counter

# Sessions
session:{token_hash} -> User data
```

**Configuration:**
```yaml
Replicas: 1 (Redis Sentinel for HA)
Memory: 4GB
Persistence: AOF + RDB
Eviction: allkeys-lru
```

### **3.3 Pinecone**

**Purpose:** Vector storage and similarity search

**Index Configuration:**
```python
import pinecone

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))

index = pinecone.create_index(
    name="enterprise-rag-vectors",
    dimension=1024,  # BGE-M3 dimension
    metric="cosine",
    pods=1,
    pod_type="p1.x1"  # Free tier
)
```

**Metadata Schema:**
```python
{
    "document_id": "uuid",
    "user_id": "uuid",
    "chunk_index": 0,
    "page_number": 1,
    "content": "truncated text...",
    "created_at": "2026-05-25T12:00:00Z"
}
```

**Query Filters:**
```python
# User isolation
filter = {"user_id": current_user_id}

# Document-specific search
filter = {
    "user_id": current_user_id,
    "document_id": {"$in": selected_doc_ids}
}
```

### **3.4 File Storage**

**Purpose:** Original documents and extracted text

**Structure:**
```
/data/uploads/
  ├── {user_id}/
  │   ├── {doc_id_1}/
  │   │   ├── original.pdf
  │   │   ├── extracted_text.txt
  │   │   └── metadata.json
  │   ├── {doc_id_2}/
  │   │   └── ...
```

**Kubernetes PVC:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
spec:
  accessModes:
    - ReadWriteMany  # Shared across pods
  resources:
    requests:
      storage: 500Gi
  storageClassName: nfs-client  # Or local-path for dev
```

---

## 4. Inter-Service Communication

### **4.1 Synchronous (HTTP/REST)**

**When to use:**
- Client-facing APIs
- Real-time retrieval
- LLM generation

**Pattern:**
```
Client → API Gateway → Chat Service → Retrieval Service (HTTP)
                                    → LLM Service (HTTP)
```

### **4.2 Asynchronous (Event-Driven)**

**When to use:**
- Document processing
- Embedding generation
- Batch operations

**Pattern:**
```
Document Service → Redis Queue → Worker → Embedding Service
                                        → Ingestion Service
```

**Event Types:**
```python
# events.py

class Event:
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    CHUNK_READY = "chunk.ready_for_embedding"
    EMBEDDING_COMPLETE = "embedding.complete"
    INGESTION_FAILED = "ingestion.failed"
```

---

## 5. Security Architecture

### **5.1 Authentication**

```python
# JWT-based authentication

def create_access_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### **5.2 Authorization**

**Multi-tenant isolation:**
```python
# Every query must filter by user_id

async def get_user_documents(user_id: str):
    return db.query(Document).filter(Document.user_id == user_id).all()

# Pinecone queries include user filter
results = index.query(
    vector=embedding,
    filter={"user_id": user_id},  # Critical for isolation
    top_k=20
)
```

### **5.3 Rate Limiting**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat/query")
@limiter.limit("10/minute")  # 10 queries per minute
async def chat_query(...):
    pass
```

### **5.4 Input Validation**

```python
from pydantic import BaseModel, validator

class ChatQueryRequest(BaseModel):
    query: str
    session_id: Optional[str]
    document_ids: Optional[List[str]]
    
    @validator('query')
    def query_must_be_valid(cls, v):
        if len(v) > 5000:
            raise ValueError('Query too long')
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v
```

---

## 6. Scalability Considerations

### **6.1 Horizontal Scaling**

| Service | Scaling Strategy | Bottleneck | Solution |
|---------|------------------|------------|----------|
| API Gateway | HPA (CPU/Requests) | Network I/O | Add replicas |
| Chat Service | HPA (CPU) | LLM latency | Cache responses |
| Retrieval Service | HPA (CPU) | Pinecone API | Implement caching |
| Embedding Service | HPA (GPU util) | GPU memory | Add GPU nodes |
| LLM Service | Manual (GPU) | Inference speed | vLLM batching |
| Workers | HPA (Queue depth) | Task backlog | Add workers |

### **6.2 Caching Strategy**

```python
# Cache embeddings for repeated queries
@cache(ttl=3600)  # 1 hour
async def get_query_embedding(query: str) -> List[float]:
    return await embedding_service.embed_query(query)

# Cache retrieval results
@cache(ttl=300)  # 5 minutes
async def get_cached_retrieval(query_hash: str, user_id: str):
    return await retrieval_service.retrieve(...)
```

### **6.3 Database Optimization**

```sql
-- Partial indexes for common queries
CREATE INDEX idx_documents_user_active 
ON documents(user_id) 
WHERE status = 'completed';

-- Covering indexes for retrieval
CREATE INDEX idx_chunks_covering 
ON chunks(document_id, chunk_index) 
INCLUDE (content, page_number);
```

---

## 7. Deployment Architecture

See `/docs/desing-docs/backend/deployment.md` for detailed Kubernetes manifests.

**Summary:**
- **Local Dev:** Docker Compose
- **Staging:** Kubernetes (single node)
- **Production:** Kubernetes (multi-node with GPU nodes)

---

## 8. Monitoring & Health Checks

### **Health Check Endpoints**

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "chat-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/deep")
async def deep_health_check():
    checks = {
        "database": await check_postgres(),
        "redis": await check_redis(),
        "pinecone": await check_pinecone(),
        "llm_service": await check_llm_service()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return Response(
        content=json.dumps(checks),
        status_code=status_code
    )
```

---

## Summary

This architecture provides:
- ✅ **Microservices isolation** for independent scaling
- ✅ **Event-driven processing** for async operations
- ✅ **Multi-tenant support** with user-based filtering
- ✅ **Horizontal scalability** via Kubernetes HPA
- ✅ **Production-grade patterns** (health checks, retries, caching)
- ✅ **Clear separation of concerns** (API/Processing/ML layers)

**Next:** Review data flow diagrams and API specifications.

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** Backend Architecture Team

