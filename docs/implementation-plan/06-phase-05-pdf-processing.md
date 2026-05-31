# Phase 5: PDF Processing

**Goal:** Parse uploaded PDF/TXT files, chunk the extracted text, and store chunks in PostgreSQL with metadata needed for retrieval and citations.

**Duration:** 3-4 hours

**Dependencies:**
- `05-phase-04-document-upload.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ PDF parsing with `pypdfium2`
- ✅ TXT parsing fallback
- ✅ Recursive text chunking with overlap
- ✅ Chunk records stored in PostgreSQL
- ✅ Document status updates during processing
- ✅ A manual processing entry point for testing

---

## 📂 Files to Create or Update

```text
backend/app/
├── services/
│   └── ingestion_service.py
└── utils/
    ├── pdf_parser.py
    └── chunking.py
```

Also update:

```text
backend/app/routes/documents.py
backend/app/models/document.py      # if status values need adjustment
backend/app/models/chunk.py         # if metadata fields need refinement
```

---

## 🧭 Phase Strategy

Implement processing **synchronously first** so it is easy to debug.

In this phase, a document can be processed by:

- a temporary manual endpoint, or
- a service call triggered right after upload during testing

In **Phase 11**, you will move this into Celery workers and queue it asynchronously.

---

## 📄 Step 1: Create `backend/app/utils/pdf_parser.py`

This module should extract text page-by-page.

### Responsibilities

- parse PDFs with `pypdfium2`
- return a structured representation such as:
  - list of pages
  - page number
  - extracted text
- parse `.txt` files as a simpler fallback

### Suggested data shape

```python
@dataclass
class ParsedPage:
    page_number: int
    text: str
```

### Recommended functions

- `parse_pdf(file_path: str | Path) -> list[ParsedPage]`
- `parse_txt(file_path: str | Path) -> list[ParsedPage]`
- `parse_document(file_path: str | Path, file_type: str) -> list[ParsedPage]`

### Notes

- Skip empty pages.
- Normalize whitespace.
- Log page counts and extraction timing.
- If a PDF yields almost no text, log a warning for future OCR fallback work.

---

## ✂️ Step 2: Create `backend/app/utils/chunking.py`

Use `RecursiveCharacterTextSplitter` from LangChain.

### Recommended initial settings

- `chunk_size=512`
- `chunk_overlap=50`
- separators: paragraph, newline, sentence, word

### Why these values

They align well with the design docs and are a good starting point for:

- BGE-M3 embeddings
- Pinecone vector search
- citation-friendly chunk sizes
- manageable context assembly later

### Recommended output shape

```python
@dataclass
class ChunkPayload:
    chunk_index: int
    content: str
    page_number: int | None
    char_count: int
    token_count: int | None
    chunk_metadata: dict
```

### Metadata to preserve

- `page_number`
- `source_file`
- `chunk_index`
- `char_count`
- optional token estimate

---

## 🧠 Step 3: Create `backend/app/services/ingestion_service.py`

This service should orchestrate the full ingestion flow.

### Recommended responsibilities

1. load document from the database
2. set document status to `processing`
3. parse the uploaded file
4. chunk the parsed text
5. store chunks in the `chunks` table
6. update document totals
7. mark status as `processed` or `chunked`

### Suggested public methods

- `process_document(document_id: UUID) -> Document`
- `parse_and_chunk(document: Document) -> list[ChunkPayload]`
- `persist_chunks(document_id: UUID, chunks: list[ChunkPayload]) -> int`

### Document status progression

A simple lifecycle that works well:

- `uploaded`
- `processing`
- `chunked`
- `embedded`
- `completed`
- `failed`

You can also collapse `chunked` and `embedded` later if you want fewer states.

---

## 🧼 Step 4: Clear existing chunks before reprocessing

If a document is processed twice during development, duplicate chunks become a problem.

Before inserting new chunks, delete old chunks for that document.

Recommended approach:

- `DELETE FROM chunks WHERE document_id = :document_id`
- then insert fresh chunk rows

This keeps repeated testing deterministic.

---

## 🌐 Step 5: Add a temporary processing endpoint

Update `backend/app/routes/documents.py` with a manual endpoint for this phase.

### Recommended endpoint

#### `POST /api/documents/{document_id}/process`

Behavior:

- load the document
- run `IngestionService.process_document(document_id)`
- return document status and chunk totals

### Why this endpoint is useful

It gives you a clean manual checkpoint before you introduce workers.

Later in Phase 11, the upload endpoint should queue this operation instead of doing it inline.

---

## 🧪 Step 6: Test the processing flow

### 1. Upload a file

```bash
curl -X POST \
  -F "file=@/absolute/path/to/sample.pdf" \
  http://localhost:8000/api/documents/upload
```

### 2. Process it

```bash
curl -X POST http://localhost:8000/api/documents/<DOCUMENT_ID>/process
```

### 3. Verify chunk rows

```bash
docker compose exec postgres psql -U postgres -d enterprise_rag -c "SELECT document_id, chunk_index, page_number, char_count FROM chunks WHERE document_id = '<DOCUMENT_ID>' ORDER BY chunk_index LIMIT 10;"
```

### 4. Verify document totals

```bash
docker compose exec postgres psql -U postgres -d enterprise_rag -c "SELECT id, status, total_pages, total_chunks FROM documents WHERE id = '<DOCUMENT_ID>';"
```

---

## ✅ Expected Result

After processing a valid document:

- document status is no longer `uploaded`
- `total_pages` is populated for PDFs
- `total_chunks` is populated
- chunk records exist in the `chunks` table
- each chunk contains content and page metadata

---

## 📌 Suggested Chunking Rules for MVP

Use the simple recursive splitter first.

Do **not** try to implement semantic chunking yet.

That advanced strategy belongs to a later optimization phase once the baseline RAG path works end-to-end.

MVP first:

- deterministic
- easy to debug
- easy to cite
- fast enough

---

## 🐛 Common Issues

### 1. PDF text is empty

Likely causes:

- scanned/image PDF
- extraction library mismatch
- file path issue inside Docker

For now, log the failure and mark the document as `failed` with an `error_message`.

### 2. Chunks are too large or too small

Tune these first:

- `chunk_size`
- `chunk_overlap`
- separator order

### 3. Duplicate chunks appear

Make sure old chunks are deleted before reprocessing.

### 4. `page_number` is always null

You are probably chunking the entire document as one string. Chunk page-by-page first, then merge if needed later.

---

## 🎯 Phase 5 Checklist

- [ ] Implemented PDF parser
- [ ] Implemented TXT parser
- [ ] Implemented recursive chunking utility
- [ ] Created ingestion orchestration service
- [ ] Stored chunks in PostgreSQL
- [ ] Updated document status and totals
- [ ] Added manual processing endpoint
- [ ] Verified chunks exist for at least one sample document

---

## 📝 Commit Phase 5

```bash
git add .
git commit -m "feat: Phase 5 - Document parsing and chunking

- Added PDF and TXT parsing utilities
- Implemented recursive text chunking
- Added ingestion service orchestration
- Persisted document chunks to PostgreSQL
- Added manual document processing endpoint"
```

---

## ➡️ Next Phase

Continue with **Phase 6: Embedding Service**

- Read: `docs/implementation-plan/07-phase-06-embedding-service.md`
- Goal: serve BGE-M3 embeddings for both documents and queries

---

**Phase 5 Complete!**

**Status:** ✅ Document-to-chunks pipeline ready

