# Phase 11: Celery Workers

**Goal:** Move document processing and embedding work out of the request-response cycle by introducing Celery workers backed by Redis.

**Duration:** 2-3 hours

**Dependencies:**
- `11-phase-10-chat-service.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ Celery configured with Redis broker and result backend
- ✅ Background task for document processing
- ✅ Background task for embedding/vector indexing
- ✅ Upload endpoint updated to queue work
- ✅ Worker logs visible through Docker Compose

---

## 📂 Files to Create or Update

```text
backend/workers/
├── celery_app.py
└── tasks.py
```

Also update:

```text
backend/app/routes/documents.py
backend/app/services/document_service.py
backend/app/services/ingestion_service.py
backend/app/config.py
```

Optional:

```text
docker-compose.yml   # only if worker command/service needs adjustment
```

---

## 🧭 Phase Strategy

You already proved the pipeline works synchronously in earlier phases.

Now refactor it so uploads stay fast:

1. upload API saves file + DB row
2. upload API queues a Celery task
3. worker processes the document in the background
4. worker generates embeddings and writes vectors
5. document status updates over time

This is the production-shaped version of the ingestion flow.

---

## ⚙️ Step 1: Create `backend/workers/celery_app.py`

### Responsibilities

- initialize the Celery application
- read broker/result backend from settings
- set serializer and retry defaults
- auto-discover task modules if you prefer

### Recommended config

- broker: `CELERY_BROKER_URL`
- result backend: `CELERY_RESULT_BACKEND`
- JSON serialization
- UTC enabled
- task retry support

Optional queue names:

- `document_ingestion`
- `embedding_generation`

You can keep everything on the default queue for the MVP if you want less setup.

---

## 🧠 Step 2: Create `backend/workers/tasks.py`

### Recommended tasks

#### `process_document_task(document_id: str)`

- set status to `processing`
- parse and chunk the document
- store chunks
- trigger embedding/vector indexing
- set status to `completed` or `failed`

#### `generate_embeddings_task(document_id: str)`

If you want a two-step pipeline:

- load unembedded chunks for the document
- call embedding service in batches
- upsert to Pinecone
- update chunk `embedding_id` values

### Simpler MVP alternative

You can keep a single `process_document_task` that does everything end to end.

That is totally acceptable for this stage.

---

## 🔁 Step 3: Add retry behavior

Use Celery retries for transient failures.

Good retry cases:

- embedding service unavailable
- Pinecone timeout
- temporary Redis/network issue

Do **not** keep retrying forever on hard failures like a corrupt PDF.

For unrecoverable failures:

- set document status to `failed`
- write `error_message`
- log the exception with the document ID

---

## 🌐 Step 4: Update upload flow to queue work

Modify the document upload path so it no longer processes synchronously.

### New behavior after upload

1. save file
2. create document row with `uploaded` or `queued`
3. dispatch `process_document_task.delay(document_id)`
4. return the document metadata immediately

### Why this matters

Large PDFs and embeddings should not block the API response.

---

## 📊 Step 5: Make status polling useful

Because processing is now asynchronous, the frontend and CLI need a status source.

Your existing endpoint:

- `GET /api/documents/{document_id}`

should now clearly expose current status values such as:

- `queued`
- `processing`
- `completed`
- `failed`

This is enough for the frontend later to poll until processing is done.

---

## ▶️ Step 6: Start the worker

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
docker compose up -d worker
```

Check logs:

```bash
docker compose logs -f worker
```

You should see Celery boot messages and task execution logs.

---

## 🧪 Step 7: Test async processing end to end

Upload a document:

```bash
curl -X POST \
  -F "file=@/absolute/path/to/sample.pdf" \
  http://localhost:8000/api/documents/upload
```

Then poll the document:

```bash
curl http://localhost:8000/api/documents/<DOCUMENT_ID>
```

Watch logs:

```bash
docker compose logs -f worker
```

Verify database status:

```bash
docker compose exec postgres psql -U postgres -d enterprise_rag -c "SELECT id, status, total_chunks, error_message FROM documents WHERE id = '<DOCUMENT_ID>';"
```

---

## ✅ Success Criteria

This phase is complete when:

- uploads return quickly
- background tasks are picked up by the worker
- document status changes over time
- chunk creation and vector indexing still complete successfully
- failures are visible through status and logs

---

## 🐛 Common Issues

### 1. Tasks are never executed

Check:

- Redis is running
- broker URL is correct
- worker imports the task module
- queue names match

### 2. Worker starts but cannot import app modules

Ensure the container working directory and Python path match the backend package layout.

### 3. Upload endpoint still blocks

Make sure the route calls `delay()` and does not run ingestion inline.

### 4. Status stays `queued` forever

The worker may be failing immediately. Check logs first.

---

## 🎯 Phase 11 Checklist

- [ ] Created Celery app configuration
- [ ] Added background tasks for document processing
- [ ] Added retry/error handling
- [ ] Updated upload endpoint to queue work
- [ ] Verified worker starts successfully
- [ ] Verified document status transitions during processing
- [ ] Verified completed documents still end up chunked and indexed

---

## 📝 Commit Phase 11

```bash
git add .
git commit -m "feat: Phase 11 - Async document processing with Celery

- Added Celery configuration and worker tasks
- Moved document processing into background jobs
- Updated upload flow to queue work
- Added status-friendly async ingestion behavior"
```

---

## ➡️ Next Phase

Continue with **Phase 12: Frontend**

- Read: `docs/implementation-plan/13-phase-12-frontend.md`
- Goal: build the Next.js UI for uploads, status polling, and streaming chat

---

**Phase 11 Complete!**

**Status:** ✅ Async ingestion ready

