# Data Flow & Retrieval Pipeline - Enterprise RAG System

## Executive Summary

This document details the **end-to-end data flows** for document ingestion and query processing in the enterprise RAG platform, including retrieval pipeline architecture, chunking strategies, and streaming patterns.

---

## 1. Document Ingestion Flow

### **1.1 High-Level Flow**

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└─────┬───────┘
      │ 1. Upload PDF/TXT
      ▼
┌─────────────────────────────────────┐
│      API Gateway                    │
│  - Auth check (JWT)                 │
│  - File validation (size, type)     │
│  - Rate limiting                    │
└─────┬───────────────────────────────┘
      │ 2. Forward to Document Service
      ▼
┌─────────────────────────────────────┐
│    Document Service                 │
│  - Generate document_id (UUID)      │
│  - Save to filesystem               │
│    /data/uploads/{user_id}/{doc_id}/│
│  - Insert to PostgreSQL             │
│    status = 'pending'               │
│  - Publish event to Redis           │
└─────┬───────────────────────────────┘
      │ 3. Publish "document.uploaded" event
      ▼
┌─────────────────────────────────────┐
│      Redis Queue                    │
│  Queue: document_ingestion          │
│  Priority: High                     │
└─────┬───────────────────────────────┘
      │ 4. Celery worker consumes
      ▼
┌─────────────────────────────────────┐
│    Celery Worker                    │
│  ┌───────────────────────────────┐ │
│  │ process_document_task()       │ │
│  │ - Load file from storage      │ │
│  │ - Call Ingestion Service      │ │
│  └───────────────────────────────┘ │
└─────┬───────────────────────────────┘
      │ 5. Process document
      ▼
┌─────────────────────────────────────┐
│    Ingestion Service                │
│  ┌───────────────────────────────┐ │
│  │ STEP 1: Parse Document        │ │
│  │  - PDF: pypdfium2/unstructured│ │
│  │  - TXT: read with encoding    │ │
│  │  - Extract text per page      │ │
│  │  - Extract metadata           │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ STEP 2: Chunk Text            │ │
│  │  - RecursiveCharacterSplitter │ │
│  │  - chunk_size=512             │ │
│  │  - chunk_overlap=50           │ │
│  │  - Preserve page numbers      │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ STEP 3: Save Chunks to DB     │ │
│  │  - Insert to chunks table     │ │
│  │  - Store metadata (page, idx) │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ STEP 4: Queue Embedding Tasks │ │
│  │  - Batch chunks (32 per task) │ │
│  │  - Publish to Redis           │ │
│  └───────────────────────────────┘ │
└─────┬───────────────────────────────┘
      │ 6. Update status to 'processing'
      ▼
┌─────────────────────────────────────┐
│      Redis Queue                    │
│  Queue: embedding_generation        │
│  Batches of 32 chunk_ids            │
└─────┬───────────────────────────────┘
      │ 7. Celery worker consumes
      ▼
┌─────────────────────────────────────┐
│    Celery Worker                    │
│  ┌───────────────────────────────┐ │
│  │ generate_embeddings_task()    │ │
│  │ - Call Embedding Service      │ │
│  └───────────────────────────────┘ │
└─────┬───────────────────────────────┘
      │ 8. Generate embeddings
      ▼
┌─────────────────────────────────────┐
│    Embedding Service                │
│  - Load BGE-M3 model              │
│  - Batch encode (batch_size=32)   │
│  - Normalize embeddings            │
│  - Return 1024-dim vectors         │
└─────┬───────────────────────────────┘
      │ 9. Upsert to Pinecone
      ▼
┌─────────────────────────────────────┐
│      Pinecone Index                 │
│  - Index vectors                    │
│  - Store metadata:                  │
│    {document_id, user_id,           │
│     chunk_index, page_number,       │
│     content (truncated)}            │
└─────┬───────────────────────────────┘
      │ 10. Update chunk.embedding_id
      ▼
┌─────────────────────────────────────┐
│    PostgreSQL                       │
│  - Update chunks.embedding_id       │
│  - Update documents.status          │
│    status = 'completed'             │
│  - Update documents.total_chunks    │
└─────────────────────────────────────┘
```

### **1.2 Timeline Metrics**

| Operation | Duration | Bottleneck |
|-----------|----------|------------|
| File upload | 1-5s | Network bandwidth |
| File validation | <100ms | I/O |
| Queue publish | <10ms | Redis latency |
| PDF parsing | 0.5-2s/page | CPU (complex PDFs) |
| Text chunking | 100-500ms | CPU |
| Embedding generation | 1-3s/batch(32) | GPU inference |
| Pinecone upsert | 200-500ms/batch | API latency |
| **Total (100 pages)** | **~2-5 minutes** | GPU throughput |

### **1.3 Error Handling**

```python
# Retry logic in Celery tasks

@app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    try:
        ingestion_service.process_document(document_id)
        
    except PDFParseError as exc:
        # Unrecoverable - mark as failed
        db.update_document(
            document_id,
            status='failed',
            error_message=str(exc)
        )
        
    except TransientError as exc:
        # Retry with exponential backoff
        self.retry(
            exc=exc,
            countdown=2 ** self.request.retries * 60
        )
        
    except Exception as exc:
        # Log and retry
        logger.error(f"Unexpected error: {exc}")
        self.retry(exc=exc, countdown=300)
```

---

## 2. Query Processing Flow (RAG Pipeline)

### **2.1 High-Level Flow**

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└─────┬───────┘
      │ 1. POST /chat/query
      │    {query, session_id?, document_ids?}
      ▼
┌─────────────────────────────────────┐
│      API Gateway                    │
│  - Auth check (JWT)                 │
│  - Rate limiting (10/min)           │
│  - Input validation                 │
└─────┬───────────────────────────────┘
      │ 2. Forward to Chat Service
      ▼
┌─────────────────────────────────────┐
│    Chat Service                     │
│  - Create/get session               │
│  - Store user message               │
│  - Orchestrate RAG pipeline         │
└─────┬───────────────────────────────┘
      │
      │ PARALLEL OPERATIONS:
      │
      ├──── 3a. Retrieve Context ─────┐
      │                                │
      │                                ▼
      │                    ┌───────────────────────┐
      │                    │  Retrieval Service    │
      │                    │  ┌─────────────────┐ │
      │                    │  │ STAGE 1:        │ │
      │                    │  │ Embed Query     │ │
      │                    │  └────┬────────────┘ │
      │                    │       │              │
      │                    │       ▼              │
      │                    │  ┌─────────────────┐ │
      │                    │  │ Embedding Svc   │ │
      │                    │  │ - BGE-M3 encode │ │
      │                    │  │ - Add prefix    │ │
      │                    │  │   "Represent    │ │
      │                    │  │    this query..." │
      │                    │  └────┬────────────┘ │
      │                    │       │              │
      │                    │       ▼              │
      │                    │  ┌─────────────────┐ │
      │                    │  │ STAGE 2:        │ │
      │                    │  │ Vector Search   │ │
      │                    │  └────┬────────────┘ │
      │                    │       │              │
      │                    │       ▼              │
      │                    │  ┌─────────────────┐ │
      │                    │  │ Pinecone Query  │ │
      │                    │  │ - top_k=50      │ │
      │                    │  │ - filter:       │ │
      │                    │  │   user_id       │ │
      │                    │  │   document_ids  │ │
      │                    │  └────┬────────────┘ │
      │                    │       │              │
      │                    │       ▼              │
      │                    │  ┌─────────────────┐ │
      │                    │  │ STAGE 3:        │ │
      │                    │  │ Rerank          │ │
      │                    │  └────┬────────────┘ │
      │                    │       │              │
      │                    │       ▼              │
      │                    │  ┌─────────────────┐ │
      │                    │  │ Reranker Svc    │ │
      │                    │  │ - Cross-encoder │ │
      │                    │  │ - top_k=5       │ │
      │                    │  └────┬────────────┘ │
      │                    │       │              │
      │                    │       ▼              │
      │                    │  ┌─────────────────┐ │
      │                    │  │ STAGE 4:        │ │
      │                    │  │ Format Context  │ │
      │                    │  │ - Merge chunks  │ │
      │                    │  │ - Add citations │ │
      │                    │  └─────────────────┘ │
      │                    └───────┬───────────────┘
      │                            │
      ├────────────────────────────┘
      │
      │ 4. Build Prompt
      ▼
┌─────────────────────────────────────┐
│    Chat Service                     │
│  - Construct RAG prompt             │
│  - Add system instructions          │
│  - Add retrieved context            │
│  - Add conversation history         │
└─────┬───────────────────────────────┘
      │ 5. Call LLM Service
      ▼
┌─────────────────────────────────────┐
│    LLM Service (vLLM)               │
│  - Stream completion                │
│  - Token-by-token generation        │
│  - OpenAI-compatible API            │
└─────┬───────────────────────────────┘
      │ 6. Stream tokens
      ▼
┌─────────────────────────────────────┐
│    Chat Service                     │
│  - Collect tokens                   │
│  - Forward to client (SSE)          │
│  - Accumulate full response         │
└─────┬───────────────────────────────┘
      │ 7. Stream to client
      ▼
┌─────────────┐
│   Client    │
│  (Browser)  │
│  - Display  │
│    tokens   │
│  - Show     │
│    sources  │
└─────────────┘
      │
      │ 8. On completion
      ▼
┌─────────────────────────────────────┐
│    Chat Service                     │
│  - Store assistant message          │
│  - Store sources/citations          │
│  - Update chat session              │
└─────────────────────────────────────┘
```

### **2.2 Timeline Metrics**

| Operation | Duration | Bottleneck |
|-----------|----------|------------|
| Query embedding | 20-50ms | GPU inference |
| Pinecone search | 100-200ms | API latency |
| Reranking (5 docs) | 30-80ms | GPU inference |
| LLM first token | 150-300ms | Model loading |
| LLM subsequent tokens | 20-30ms | GPU compute |
| **Total to first token** | **~300-600ms** | Network + LLM |
| **Full response (500 tokens)** | **~10-15s** | Token generation |

### **2.3 Detailed Retrieval Pipeline**

#### **Stage 1: Query Embedding**

```python
async def embed_query(query: str) -> List[float]:
    """Embed query with instruction prefix for better retrieval"""
    
    # BGE-M3 works better with instructions
    instruction = "Represent this query for retrieving relevant documents: "
    
    # Call embedding service
    response = await embedding_client.post("/embed/query", json={
        "text": instruction + query
    })
    
    embedding = response.json()["embedding"]
    
    # Cache for repeated queries
    await redis.setex(
        f"query_embedding:{hash(query)}",
        3600,  # 1 hour TTL
        json.dumps(embedding)
    )
    
    return embedding
```

#### **Stage 2: Vector Search**

```python
async def vector_search(
    query_embedding: List[float],
    user_id: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = 50
) -> List[SearchResult]:
    """Search Pinecone with user isolation"""
    
    # Build metadata filter
    filter_dict = {"user_id": user_id}
    
    if document_ids:
        # Search only in specific documents
        filter_dict["document_id"] = {"$in": document_ids}
    
    # Query Pinecone
    results = pinecone_index.query(
        vector=query_embedding,
        top_k=top_k,
        filter=filter_dict,
        include_metadata=True
    )
    
    # Parse results
    return [
        SearchResult(
            chunk_id=match.id,
            score=match.score,
            document_id=match.metadata["document_id"],
            page_number=match.metadata["page_number"],
            content=match.metadata["content"],
            chunk_index=match.metadata["chunk_index"]
        )
        for match in results.matches
    ]
```

#### **Stage 3: Reranking**

```python
async def rerank_results(
    query: str,
    candidates: List[SearchResult],
    top_k: int = 5
) -> List[RankedResult]:
    """Rerank using cross-encoder for precision"""
    
    # Call reranker service
    response = await reranker_client.post("/rerank", json={
        "query": query,
        "documents": [c.content for c in candidates],
        "top_k": top_k
    })
    
    reranked = response.json()["ranked_documents"]
    
    # Merge scores with original metadata
    results = []
    for i, item in enumerate(reranked):
        original = candidates[i]
        results.append(RankedResult(
            **original.dict(),
            rerank_score=item["score"],
            final_rank=i
        ))
    
    return results
```

#### **Stage 4: Context Preparation**

```python
def prepare_context(
    ranked_results: List[RankedResult],
    max_tokens: int = 2048
) -> str:
    """Format retrieved chunks into LLM context"""
    
    context_parts = []
    token_count = 0
    
    for i, result in enumerate(ranked_results):
        # Format with citation
        chunk_text = f"""
[Source {i+1}] (Document: {result.document_id}, Page: {result.page_number})
{result.content}
"""
        
        chunk_tokens = estimate_tokens(chunk_text)
        
        if token_count + chunk_tokens > max_tokens:
            break
        
        context_parts.append(chunk_text)
        token_count += chunk_tokens
    
    return "\n\n".join(context_parts)
```

#### **Stage 5: Prompt Construction**

```python
def build_rag_prompt(
    query: str,
    context: str,
    conversation_history: Optional[List[Message]] = None
) -> str:
    """Construct prompt for RAG"""
    
    system_prompt = """You are a helpful AI assistant. Answer questions based on the provided context.

Guidelines:
- Use ONLY the information from the provided context
- If the context doesn't contain enough information, say "I don't have enough information to answer that"
- Cite sources using [Source N] notation
- Be concise and accurate
- Do not make up information"""

    context_section = f"""
Context from documents:
{context}
"""

    # Add conversation history if exists
    history_section = ""
    if conversation_history:
        history_section = "\nPrevious conversation:\n"
        for msg in conversation_history[-3:]:  # Last 3 turns
            history_section += f"{msg.role}: {msg.content}\n"
    
    user_query = f"""
Question: {query}

Answer:"""

    full_prompt = f"{system_prompt}\n\n{context_section}\n{history_section}\n{user_query}"
    
    return full_prompt
```

---

## 3. Streaming Response Flow

### **3.1 Server-Sent Events (SSE) Pattern**

```python
from fastapi.responses import StreamingResponse
import asyncio

@app.post("/chat/query")
async def chat_query_stream(request: ChatQueryRequest):
    """Stream RAG response using SSE"""
    
    async def generate():
        try:
            # Stage 1: Retrieve context
            yield sse_event("status", {"message": "Retrieving context..."})
            
            retrieval_result = await retrieval_service.retrieve(
                query=request.query,
                user_id=request.user_id,
                document_ids=request.document_ids
            )
            
            # Stage 2: Send sources
            yield sse_event("sources", {
                "sources": [
                    {
                        "document_id": s.document_id,
                        "page": s.page_number,
                        "score": s.rerank_score
                    }
                    for s in retrieval_result.sources
                ]
            })
            
            # Stage 3: Build prompt
            prompt = build_rag_prompt(
                query=request.query,
                context=retrieval_result.context
            )
            
            # Stage 4: Stream LLM response
            yield sse_event("status", {"message": "Generating answer..."})
            
            full_answer = ""
            async for token in llm_service.generate_stream(prompt):
                full_answer += token
                yield sse_event("token", {"content": token})
            
            # Stage 5: Store message
            await store_message(
                session_id=request.session_id,
                role="assistant",
                content=full_answer,
                sources=retrieval_result.sources
            )
            
            # Stage 6: Done
            yield sse_event("done", {"message_id": message_id})
            
        except Exception as e:
            yield sse_event("error", {"message": str(e)})
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable NGINX buffering
        }
    )

def sse_event(event_type: str, data: dict) -> str:
    """Format SSE event"""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
```

### **3.2 Client-Side Consumption**

```typescript
// Frontend: React component

const streamChatQuery = async (query: string) => {
  const response = await fetch('/api/v1/chat/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ query })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n\n');

    for (const line of lines) {
      if (!line.trim()) continue;

      const [eventLine, dataLine] = line.split('\n');
      const eventType = eventLine.replace('event: ', '');
      const data = JSON.parse(dataLine.replace('data: ', ''));

      switch (eventType) {
        case 'status':
          setStatus(data.message);
          break;
        case 'sources':
          setSources(data.sources);
          break;
        case 'token':
          appendToken(data.content);
          break;
        case 'done':
          setComplete(true);
          break;
        case 'error':
          showError(data.message);
          break;
      }
    }
  }
};
```

---

## 4. Document Chunking Strategy

### **4.1 Phase 1: Recursive Character Splitting**

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_document_phase1(text: str, page_numbers: List[int]) -> List[Chunk]:
    """Simple recursive chunking with overlap"""
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,  # ~400 tokens for BGE-M3
        chunk_overlap=50,  # 10% overlap for context continuity
        separators=[
            "\n\n",  # Paragraph breaks
            "\n",    # Line breaks
            ". ",    # Sentence breaks
            " ",     # Word breaks
            ""       # Character breaks
        ],
        length_function=len,
        is_separator_regex=False
    )
    
    chunks = splitter.split_text(text)
    
    # Add metadata
    result = []
    for idx, chunk_text in enumerate(chunks):
        result.append(Chunk(
            index=idx,
            content=chunk_text,
            page_number=estimate_page(chunk_text, page_numbers),
            char_count=len(chunk_text),
            token_count=estimate_tokens(chunk_text)
        ))
    
    return result
```

### **4.2 Phase 3: Semantic Chunking**

```python
from langchain_experimental.text_splitter import SemanticChunker

def chunk_document_phase3(text: str, embeddings) -> List[Chunk]:
    """Semantic chunking based on embedding similarity"""
    
    chunker = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=0.95,  # Break at 95th percentile difference
        buffer_size=1  # Sentences to consider
    )
    
    chunks = chunker.split_text(text)
    
    return [
        Chunk(
            index=idx,
            content=chunk,
            metadata={"chunking_method": "semantic"}
        )
        for idx, chunk in enumerate(chunks)
    ]
```

### **4.3 Metadata Preservation**

```python
def chunk_with_metadata(
    document: Document,
    pages: List[Page]
) -> List[ChunkWithMetadata]:
    """Chunk while preserving rich metadata"""
    
    chunks = []
    
    for page_idx, page in enumerate(pages):
        page_chunks = chunk_document_phase1(
            text=page.text,
            page_numbers=[page_idx + 1]
        )
        
        for chunk in page_chunks:
            chunks.append(ChunkWithMetadata(
                content=chunk.content,
                metadata={
                    "document_id": document.id,
                    "document_name": document.filename,
                    "page_number": page_idx + 1,
                    "chunk_index": chunk.index,
                    "total_pages": len(pages),
                    "created_at": datetime.utcnow().isoformat(),
                    
                    # For citation
                    "source_type": "pdf",
                    "heading": page.heading if hasattr(page, 'heading') else None,
                    "section": page.section if hasattr(page, 'section') else None
                }
            ))
    
    return chunks
```

---

## 5. Caching Strategy

### **5.1 Redis Cache Layers**

```python
# Layer 1: Query embedding cache
async def get_query_embedding_cached(query: str) -> List[float]:
    cache_key = f"embed:query:{hashlib.md5(query.encode()).hexdigest()}"
    
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    embedding = await embedding_service.embed_query(query)
    await redis.setex(cache_key, 3600, json.dumps(embedding))
    
    return embedding

# Layer 2: Retrieval results cache
async def get_retrieval_cached(
    query: str,
    user_id: str,
    document_ids: Optional[List[str]]
) -> RetrievalResult:
    cache_key = f"retrieval:{user_id}:{hash(query)}:{hash(tuple(document_ids or []))}"
    
    cached = await redis.get(cache_key)
    if cached:
        return RetrievalResult.parse_raw(cached)
    
    result = await retrieval_service.retrieve(query, user_id, document_ids)
    await redis.setex(cache_key, 300, result.json())  # 5 min TTL
    
    return result

# Layer 3: LLM response cache (exact query match)
async def get_llm_response_cached(prompt_hash: str) -> Optional[str]:
    cache_key = f"llm:response:{prompt_hash}"
    return await redis.get(cache_key)
```

---

## 6. Batch Processing Optimization

### **6.1 Embedding Batch Generation**

```python
async def process_document_embeddings_batch(document_id: str):
    """Process embeddings in batches for efficiency"""
    
    # Load all chunks for document
    chunks = db.query(Chunk).filter(
        Chunk.document_id == document_id,
        Chunk.embedding_id == None  # Not yet embedded
    ).all()
    
    batch_size = 32
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        # Batch embed
        texts = [chunk.content for chunk in batch]
        embeddings = await embedding_service.batch_embed(texts)
        
        # Batch upsert to Pinecone
        vectors = [
            {
                "id": f"{chunk.id}",
                "values": embedding,
                "metadata": {
                    "document_id": chunk.document_id,
                    "user_id": document.user_id,
                    "page_number": chunk.page_number,
                    "content": chunk.content[:1000]
                }
            }
            for chunk, embedding in zip(batch, embeddings)
        ]
        
        pinecone_index.upsert(vectors=vectors)
        
        # Update database
        for chunk, embedding_id in zip(batch, [v["id"] for v in vectors]):
            chunk.embedding_id = embedding_id
        
        db.commit()
```

---

## 7. Error Handling & Retry Logic

### **7.1 Transient Error Handling**

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
async def pinecone_upsert_with_retry(vectors: List[dict]):
    """Upsert to Pinecone with automatic retry"""
    return pinecone_index.upsert(vectors=vectors)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(EmbeddingServiceError)
)
async def embed_with_retry(texts: List[str]):
    """Embed with retry on service errors"""
    return await embedding_service.batch_embed(texts)
```

### **7.2 Circuit Breaker Pattern**

```python
from pybreaker import CircuitBreaker

# Protect LLM service calls
llm_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    name="llm_service"
)

@llm_breaker
async def call_llm_protected(prompt: str):
    """Call LLM with circuit breaker protection"""
    return await llm_service.generate(prompt)
```

---

## 8. Performance Monitoring

### **8.1 Pipeline Metrics**

```python
from prometheus_client import Histogram, Counter

# Latency metrics
retrieval_latency = Histogram(
    'retrieval_latency_seconds',
    'Time spent in retrieval pipeline',
    ['stage']
)

llm_generation_latency = Histogram(
    'llm_generation_latency_seconds',
    'Time to first token and total generation'
)

# Throughput metrics
documents_processed = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['status']
)

embeddings_generated = Counter(
    'embeddings_generated_total',
    'Total embeddings generated'
)

# Usage in code
with retrieval_latency.labels(stage='embedding').time():
    embedding = await embed_query(query)

with retrieval_latency.labels(stage='vector_search').time():
    results = await vector_search(embedding, user_id)

with retrieval_latency.labels(stage='reranking').time():
    reranked = await rerank_results(query, results)
```

---

## Summary

This data flow architecture provides:

- ✅ **Async processing** for document ingestion (not blocking API)
- ✅ **Multi-stage retrieval** (vector search + reranking)
- ✅ **Streaming responses** for real-time UX
- ✅ **Batch optimization** for embedding generation
- ✅ **Comprehensive caching** for performance
- ✅ **Retry & circuit breakers** for resilience
- ✅ **Rich observability** with Prometheus metrics

**Key Performance Targets:**
- Document processing: 2-5 minutes for 100-page PDF
- Query to first token: <600ms
- Streaming token rate: 30-50 tokens/second

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** Backend Engineering Team

