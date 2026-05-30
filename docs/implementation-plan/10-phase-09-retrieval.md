# Phase 9: Retrieval Pipeline

**Goal:** Build the end-to-end retrieval layer: query embedding, Pinecone search, reranking, and context assembly for downstream LLM generation.

**Duration:** 4-5 hours

**Dependencies:**
- `08-phase-07-vector-storage.md` complete
- `09-phase-08-llm-service.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ A reranker microservice
- ✅ Backend retrieval orchestration
- ✅ Query embedding + vector search flow
- ✅ Cross-encoder reranking
- ✅ Context builder constrained by token budget
- ✅ Retrieval API endpoint for testing

---

## 📂 Files to Create or Update

```text
ml-services/reranker-service/
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py
    └── model.py
```

```text
backend/app/
├── routes/
│   └── retrieval.py
├── schemas/
│   └── retrieval.py
└── services/
    └── retrieval_service.py
```

Also update:

```text
backend/app/routes/__init__.py
backend/app/config.py
```

---

## 🧭 Retrieval Flow to Implement

This phase is the heart of the RAG backend.

### Target flow

1. embed the user query
2. search Pinecone for top `N` chunk candidates
3. rerank the candidates
4. trim to a final smaller set
5. build prompt-ready context with source metadata

### Critical retrieval rule

The query embedding must be produced by the **same embedding model** used when chunk vectors were written to Pinecone.

For this implementation:

- stored document vectors: `BAAI/bge-m3`
- query vectors: `BAAI/bge-m3`

The query can still use the BGE retrieval instruction prefix, but it must remain the same underlying model.

### Default settings from `.env`

- `RETRIEVAL_TOP_K=50`
- `RERANK_TOP_K=5`
- `MAX_CONTEXT_TOKENS=2048`

---

## 🧠 Step 1: Create the reranker service

Use `BAAI/bge-reranker-v2-m3` in a dedicated FastAPI service.

### Endpoints

#### `GET /health`

Return model and device information.

#### `POST /rerank`

Input:

```json
{
  "query": "What does the document say about compliance?",
  "documents": ["chunk 1", "chunk 2"],
  "top_k": 5
}
```

Output:

```json
{
  "results": [
    {"index": 1, "score": 0.92},
    {"index": 0, "score": 0.71}
  ]
}
```

### Implementation note

Returning indices is simpler than returning full text because the backend already has the source metadata for each candidate.

---

## 🧾 Step 2: Create retrieval schemas

In `backend/app/schemas/retrieval.py`, create at least:

- `RetrievalRequest`
- `RetrievedChunk`
- `RetrievalResponse`

### Suggested request fields

- `query: str`
- `document_ids: list[str] | None = None`
- `top_k: int | None = None`

### Suggested response fields

- `context: str`
- `chunks: list[RetrievedChunk]`
- `timings: dict[str, float] | None`

### Include metadata per chunk

- `chunk_id`
- `document_id`
- `page_number`
- `chunk_index`
- `score`
- `content`

---

## 🔎 Step 3: Create `backend/app/services/retrieval_service.py`

This service orchestrates the whole retrieval pipeline.

### Recommended public method

- `retrieve(query: str, document_ids: list[str] | None = None, top_k: int | None = None)`

### Internal stages

#### Stage A: Query embedding

- call the embedding service `/embed/query`
- use instruction-aware query encoding

#### Stage B: Vector search

- call `VectorService.search(...)`
- retrieve up to `RETRIEVAL_TOP_K`

#### Stage C: Reranking

- call the reranker service `/rerank`
- reorder the candidates
- keep the top `RERANK_TOP_K`

#### Stage D: Context assembly

- format chunks into a single string
- include source headers such as `Source 1 (page 3)`
- stop when the estimated token budget is reached

---

## 🪄 Step 4: Implement a context builder

You can keep this logic inside `retrieval_service.py` initially.

### Good context formatting example

```text
[Source 1] Document: handbook.pdf | Page: 4
<chunk text>

[Source 2] Document: policy.pdf | Page: 2
<chunk text>
```

### Rules

- include only the highest-value chunks
- preserve readable boundaries between chunks
- do not exceed the configured token budget
- keep the raw content unchanged as much as possible

This structure will make citations much easier in Phase 10.

---

## 🌐 Step 5: Add a retrieval route

Create `backend/app/routes/retrieval.py`.

### Recommended endpoint

#### `POST /api/retrieval/search`

Behavior:

- validate request payload
- call `RetrievalService.retrieve(...)`
- return the final context and source chunks

This endpoint is intentionally useful on its own before chat streaming exists.

---

## 🧪 Step 6: Test the reranker service

```bash
docker compose up -d reranker-service
```

Health check:

```bash
curl http://localhost:8002/health
```

Rerank test:

```bash
curl -X POST http://localhost:8002/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is chunking?",
    "documents": [
      "Chunking splits documents into smaller units.",
      "Redis is used for caching and queueing."
    ],
    "top_k": 2
  }'
```

---

## 🧪 Step 7: Test the full retrieval API

```bash
curl -X POST http://localhost:8000/api/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How are uploaded documents processed?",
    "document_ids": [],
    "top_k": 5
  }'
```

### What you should inspect

- are the returned chunks relevant?
- do page numbers look correct?
- is the context readable?
- are scores and ordering reasonable?

---

## ✅ Success Criteria

This phase is complete when:

- query embeddings are generated successfully
- Pinecone returns candidates
- reranking improves ordering
- final context contains the best chunks only
- `/api/retrieval/search` returns useful results for real uploaded documents

---

## 🐛 Common Issues

### 1. Retrieval returns results but reranking is wrong

Make sure the reranker response index is mapped back to the correct original candidate.

### 2. Context is too long

Cap chunk inclusion using token estimates or a conservative character-based proxy.

### 3. Document filtering returns no results

Verify that `document_id` metadata was actually written into Pinecone during Phase 7.

### 4. Scores are confusing

Keep both similarity score and rerank score if helpful, but choose one final ordering.

---

## 🎯 Phase 9 Checklist

- [ ] Created reranker microservice
- [ ] Implemented `/rerank` endpoint
- [ ] Added retrieval request/response schemas
- [ ] Implemented query embed → search → rerank → context flow
- [ ] Added `/api/retrieval/search` endpoint
- [ ] Verified retrieval works on real processed documents
- [ ] Verified context stays within budget

---

## 📝 Commit Phase 9

```bash
git add .
git commit -m "feat: Phase 9 - Retrieval pipeline with reranking

- Added reranker microservice
- Implemented retrieval orchestration service
- Added query embedding, vector search, and reranking
- Added retrieval API endpoint and context builder"
```

---

## ➡️ Next Phase

Continue with **Phase 10: Chat Service**

- Read: `docs/implementation-plan/11-phase-10-chat-service.md`
- Goal: stream RAG answers to the client and store chat history

---

**Phase 9 Complete!**

**Status:** ✅ Retrieval pipeline ready

