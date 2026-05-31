# Phase 10: Chat Service

**Goal:** Implement the RAG chat API with session management, stored conversation history, and token streaming over Server-Sent Events (SSE).

**Duration:** 3-4 hours

**Dependencies:**
- `10-phase-09-retrieval.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ Chat request/response schemas
- ✅ Chat session and message persistence
- ✅ Prompt construction using retrieved context
- ✅ SSE streaming endpoint for answers
- ✅ Source/citation data returned with the answer

---

## 📂 Files to Create or Update

```text
backend/app/
├── routes/
│   └── chat.py
├── schemas/
│   └── chat.py
├── services/
│   └── chat_service.py
└── utils/
    └── streaming.py
```

Also update:

```text
backend/app/routes/__init__.py
backend/app/models/chat.py          # only if adjustments are needed
```

---

## 🧭 Chat Flow for the MVP

Implement the following sequence:

1. receive a user query
2. create or reuse a chat session
3. store the user message
4. run retrieval
5. build a grounded prompt
6. stream LLM tokens back to the client
7. store the assistant message with sources

This is the first phase where the whole RAG path becomes visible to the user.

---

## 🧾 Step 1: Create `backend/app/schemas/chat.py`

Recommended schemas:

- `ChatQueryRequest`
- `ChatSessionResponse`
- `MessageResponse`
- `ChatHistoryResponse`

### Suggested request fields

- `query: str`
- `session_id: str | None`
- `document_ids: list[str] | None`

### Validation rules

- query cannot be empty
- query length should be capped to a reasonable size, for example 5000 characters
- `document_ids` can be optional so the system can search all documents by default

---

## 🧠 Step 2: Create `backend/app/utils/streaming.py`

Add small helpers for SSE formatting.

### Useful helper functions

- `sse_event(event_type: str, data: dict) -> str`
- optional helpers like `token_event()`, `status_event()`, `done_event()`

### Event types to standardize now

- `status`
- `token`
- `sources`
- `done`
- `error`

Using a stable event format here will make the frontend phase much easier.

---

## 💬 Step 3: Create `backend/app/services/chat_service.py`

This service should orchestrate sessions, retrieval, prompting, and storage.

### Recommended methods

- `get_or_create_session(session_id: str | None)`
- `store_user_message(session_id, query)`
- `build_prompt(query, context, history)`
- `stream_answer(query, session_id, document_ids=None)`
- `store_assistant_message(session_id, content, sources)`

### Prompt rules

Your prompt should instruct the model to:

- use only the supplied context
- say when the answer is not in the context
- cite sources clearly
- be concise and factual

### Conversation history

For the MVP, include only the last few messages, for example the last 3 user/assistant turns.

---

## 🪄 Step 4: Implement the streaming generator

Inside `ChatService`, create an async generator that does roughly this:

1. emit a `status` event like `retrieving context`
2. run retrieval
3. emit a `sources` event once sources are ready
4. emit a `status` event like `generating answer`
5. iterate over streamed tokens from `LLMClient`
6. emit `token` events continuously
7. persist the final assistant message
8. emit a `done` event

If an exception occurs, emit an `error` event before ending the stream.

---

## 🌐 Step 5: Create `backend/app/routes/chat.py`

### Recommended endpoints

#### `POST /api/chat/query`

- returns `StreamingResponse`
- media type: `text/event-stream`
- delegates to `ChatService.stream_answer(...)`

#### `GET /api/chat/sessions`

- list chat sessions ordered by newest updated

#### `GET /api/chat/sessions/{session_id}/messages`

- returns message history for a session

These read endpoints are important for the frontend phase.

---

## 🔧 Step 6: Register the chat router

Update the shared router aggregation so `/api/chat/...` is active.

At this point your backend should have at least:

- `/api/documents/...`
- `/api/retrieval/search`
- `/api/chat/query`

---

## 🧪 Step 7: Test SSE manually

Create or reuse a processed document first.

Then run:

```bash
curl -N http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize the uploaded document in 3 bullet points.",
    "session_id": null,
    "document_ids": []
  }'
```

### What you should observe

- `status` event appears first
- `sources` arrives before or near token generation
- `token` events stream incrementally
- a final `done` event ends the stream

---

## 🧪 Step 8: Verify persistence

After a streamed response completes, verify the database:

```bash
docker compose exec postgres psql -U postgres -d enterprise_rag -c "SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC;"
```

```bash
docker compose exec postgres psql -U postgres -d enterprise_rag -c "SELECT role, left(content, 80) FROM messages ORDER BY created_at DESC LIMIT 10;"
```

Check that:

- a session exists
- the user message is stored
- the assistant response is stored
- `sources` were saved for assistant messages

---

## ✅ Success Criteria

This phase is complete when:

- a user can submit a query to `/api/chat/query`
- the backend retrieves relevant context
- the LLM answer streams token by token
- the final answer is stored in the database
- the response includes usable citations/sources

---

## 🐛 Common Issues

### 1. The stream buffers and sends everything at once

Make sure you are using `StreamingResponse` and formatting events correctly with double newlines.

### 2. Sources are missing from stored messages

Persist them after retrieval and again when storing the assistant response.

### 3. Session creation works but history is empty

Check that messages are committed to the database before the request ends.

### 4. Prompt quality is weak

Usually the fix is better prompt grounding or better retrieval context, not a code issue in the stream itself.

---

## 🎯 Phase 10 Checklist

- [ ] Added chat schemas
- [ ] Added SSE formatting helpers
- [ ] Implemented chat orchestration service
- [ ] Added `/api/chat/query` streaming endpoint
- [ ] Added session and message history endpoints
- [ ] Stored user and assistant messages in PostgreSQL
- [ ] Verified sources are included with assistant responses

---

## 📝 Commit Phase 10

```bash
git add .
git commit -m "feat: Phase 10 - Streaming chat service

- Added chat schemas and SSE helpers
- Implemented RAG chat orchestration
- Added streaming chat endpoint
- Persisted chat sessions, messages, and citations"
```

---

## ➡️ Next Phase

Continue with **Phase 11: Workers**

- Read: `docs/implementation-plan/12-phase-11-workers.md`
- Goal: move ingestion and embedding work into Celery so uploads do not block the API

---

**Phase 10 Complete!**

**Status:** ✅ Streaming RAG chat ready

