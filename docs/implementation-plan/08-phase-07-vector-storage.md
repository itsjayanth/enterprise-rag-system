# Phase 7: Vector Storage

**Goal:** Connect the backend to Pinecone so chunk embeddings can be stored, searched, and removed by document.

**Duration:** 2-3 hours

**Dependencies:**
- `07-phase-06-embedding-service.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ Pinecone client initialization
- ✅ Automatic index creation or validation
- ✅ Vector upsert flow for chunk embeddings
- ✅ Similarity search helper methods
- ✅ Vector deletion by document ID
- ✅ Integration point between chunk storage and retrieval

---

## 📂 Files to Create or Update

```text
backend/app/services/
└── vector_service.py
```

Also update:

```text
backend/app/services/ingestion_service.py
backend/app/config.py
backend/requirements.txt
```

---

## 🧭 Design Notes for the MVP

For the current simplified implementation:

- keep vectors in a single Pinecone index
- filter by `document_id` when needed
- skip `user_id` metadata for now
- preserve metadata needed for citations and debugging

**Important:** the chunk vectors stored in Pinecone and the query embeddings used for search must come from the same embedding model. In this plan, both use `BAAI/bge-m3`; only the query text formatting differs.

Later, when auth is added, extend the metadata schema with `user_id` and tenant filters.

---

## ⚙️ Step 1: Add Pinecone dependency

Ensure `backend/requirements.txt` includes the Pinecone SDK version you want to use.

The scaffold currently proposes `pinecone-client==3.0.0`.

Before implementing, confirm the import style matches the installed version.

Then reinstall dependencies if needed.

---

## 🔌 Step 2: Create `vector_service.py`

This service should wrap all direct Pinecone interaction.

### Recommended responsibilities

- initialize Pinecone client
- create or connect to the configured index
- upsert vectors in batches
- search vectors by query embedding
- delete vectors for a document
- expose small, testable methods

### Suggested methods

- `ensure_index()`
- `upsert_chunk_embeddings(chunks_with_embeddings)`
- `search(query_embedding, top_k=50, document_ids=None)`
- `delete_document_vectors(document_id)`

---

## 🧱 Step 3: Define vector payload metadata

For each vector, include metadata similar to:

```json
{
  "document_id": "uuid",
  "chunk_id": "uuid",
  "chunk_index": 0,
  "page_number": 1,
  "content": "truncated chunk text",
  "source_file": "sample.pdf"
}
```

### Important guidance

- keep `content` truncated, for example to 500-1000 chars
- include `page_number` for citations
- include `chunk_id` so search results can map back to PostgreSQL rows

---

## 🔁 Step 4: Integrate vector writes into the ingestion flow

Update `IngestionService` so that after chunks are stored:

1. load chunk contents
2. call the embedding service in batches
3. construct vector payloads
4. upsert vectors to Pinecone
5. save `embedding_id` back to each chunk row
6. update document status

### Suggested status transition now

- `processing`
- `chunked`
- `embedded`
- `completed`

If you want fewer statuses, you can go straight from `processing` to `completed` after the Pinecone write succeeds.

---

## 🔎 Step 5: Implement search behavior

Your search method should accept:

- `query_embedding: list[float]`
- `top_k: int`
- optional `document_ids: list[str]`

### Search output should include

- vector score
- `chunk_id`
- `document_id`
- `page_number`
- `content`
- `chunk_index`

The retrieval phase will later take this raw output and rerank it.

---

## 🧪 Step 6: Test Pinecone connectivity

Before wiring the full pipeline, verify the index can be reached.

### Quick check from Python

```python
from app.services.vector_service import VectorService

service = VectorService()
print(service.describe_index())
```

### Environment validation

Ensure these values are correct in `.env`:

```bash
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
PINECONE_INDEX_NAME=enterprise-rag
```

### Index settings

Use:

- dimension: `1024`
- metric: `cosine`

Those must match BGE-M3 output.

---

## 🧪 Step 7: End-to-end test with one processed document

1. upload a document
2. process it through Phase 5 logic
3. confirm embeddings are generated
4. confirm vectors are stored
5. run a test search

### Suggested temporary smoke script flow

```python
query_embedding = embedding_client.embed_query("What is this document about?")
results = vector_service.search(query_embedding=query_embedding, top_k=5)
print(results)
```

### Verify chunk rows

At least some chunks should now have `embedding_id` populated.

```bash
docker compose exec postgres psql -U postgres -d enterprise_rag -c "SELECT id, embedding_id FROM chunks WHERE embedding_id IS NOT NULL LIMIT 10;"
```

---

## ✅ Success Criteria

This phase is complete when:

- Pinecone index exists and is reachable
- chunk embeddings are written to Pinecone
- `embedding_id` values are stored in PostgreSQL
- search returns plausible chunk results for a simple query
- document status reflects successful vector indexing

---

## 🐛 Common Issues

### 1. Index dimension mismatch

If Pinecone expects a different dimension than your embeddings return, queries and upserts will fail.

### 2. Search works but metadata is missing

Make sure `include_metadata=True` is enabled for queries.

### 3. Pinecone writes succeed but DB does not update

Commit the transaction after setting `embedding_id` values.

### 4. Search returns empty results

Likely causes:

- wrong index
- wrong environment/API key
- vectors were never inserted
- document IDs were filtered incorrectly

---

## 🎯 Phase 7 Checklist

- [ ] Added Pinecone configuration to the backend
- [ ] Created `vector_service.py`
- [ ] Validated or created the Pinecone index
- [ ] Upserted chunk embeddings with metadata
- [ ] Updated chunks with `embedding_id`
- [ ] Implemented similarity search helper
- [ ] Implemented delete-by-document helper
- [ ] Verified search returns relevant results

---

## 📝 Commit Phase 7

```bash
git add .
git commit -m "feat: Phase 7 - Pinecone vector storage integration

- Added Pinecone client wrapper
- Added vector upsert and search methods
- Integrated chunk embeddings into vector storage
- Persisted embedding IDs back to PostgreSQL"
```

---

## ➡️ Next Phase

Continue with **Phase 8: LLM Service**

- Read: `docs/implementation-plan/09-phase-08-llm-service.md`
- Goal: connect the application to vLLM-powered text generation and streaming

---

**Phase 7 Complete!**

**Status:** ✅ Vector storage ready

