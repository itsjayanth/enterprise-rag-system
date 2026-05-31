# Phase 4: Document Upload

**Goal:** Build the API endpoint and storage logic for PDF/TXT uploads so documents can be saved, tracked in PostgreSQL, and prepared for processing.

**Duration:** 2-3 hours

**Dependencies:**
- `04-phase-03-fastapi-core.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ Pydantic schemas for document upload and responses
- ✅ File validation for type and size
- ✅ Files saved to local storage
- ✅ Document metadata saved to PostgreSQL
- ✅ API endpoints to upload and list documents

---

## 📂 Files to Create or Update

```text
backend/app/
├── schemas/
│   └── document.py
├── services/
│   └── document_service.py
└── routes/
    └── documents.py
```

Also update:

```text
backend/app/routes/__init__.py
```

---

## 🧭 MVP Behavior for This Phase

Keep the upload workflow simple:

1. client uploads a file
2. backend validates it
3. backend saves it under `data/uploads/`
4. backend inserts a row into `documents`
5. backend returns document metadata

Do **not** add background processing yet.

Processing starts in Phase 5 and becomes asynchronous in Phase 11.

---

## 🧾 Step 1: Create `backend/app/schemas/document.py`

Create request/response schemas used by routes and services.

### Suggested schemas

- `DocumentResponse`
- `DocumentListResponse` or just `list[DocumentResponse]`
- `DocumentStatusResponse`
- `DocumentProcessResponse` placeholder for next phase

### Include fields such as

- `id`
- `filename`
- `file_type`
- `file_size`
- `status`
- `total_pages`
- `total_chunks`
- `created_at`
- `updated_at`

Use `from_attributes = True` so ORM objects serialize correctly.

---

## 🛡️ Step 2: Build file validation in `document_service.py`

Validation rules for this implementation:

- allowed types: `.pdf`, `.txt`
- allowed MIME types:
  - `application/pdf`
  - `text/plain`
- maximum size: from `MAX_UPLOAD_SIZE_MB`

### Recommended helper methods

- `validate_file(file: UploadFile) -> None`
- `build_storage_path(document_id: UUID, filename: str) -> Path`
- `save_upload(file: UploadFile, destination: Path) -> None`
- `create_document_record(...) -> Document`

### Notes

- Sanitize filenames.
- Preserve the original extension.
- Use a document-specific folder.

### Suggested storage layout for the MVP

```text
data/uploads/
└── default/
    └── {document_id}/
        ├── original.pdf
        └── metadata.json   # optional for later phases
```

We use `default/` because auth and user isolation are intentionally deferred.

---

## 💾 Step 3: Save the file and create the DB record

In `DocumentService`, implement an upload flow like this:

1. validate the incoming file
2. generate a new document UUID
3. create the destination directory
4. write the file to disk
5. insert a `documents` row with status `uploaded`
6. return the saved document

### Recommended document status at this phase

Use one of:

- `uploaded`
- `pending_processing`

Either is fine as long as you stay consistent in later phases.

---

## 🌐 Step 4: Add routes in `backend/app/routes/documents.py`

### Required endpoints for this phase

#### `POST /api/documents/upload`

- accepts multipart form upload
- validates file
- stores file
- creates DB row
- returns document metadata

#### `GET /api/documents`

- returns all documents ordered by newest first
- useful for the frontend later

#### `GET /api/documents/{document_id}`

- returns one document record
- useful for status polling later

### Implementation notes

- inject `db: Session = Depends(get_db)`
- keep route handlers thin
- put business logic in `DocumentService`
- add structured logs for upload start, success, and failure

---

## 🧷 Step 5: Register the router

Update `backend/app/routes/__init__.py` to include the document routes.

Suggested structure:

```python
api_router = APIRouter(prefix="/api")
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
```

---

## 🧪 Step 6: Test the upload endpoint

Start the backend:

```bash
make dev-backend
```

Upload a sample file:

```bash
curl -X POST \
  -F "file=@/absolute/path/to/sample.pdf" \
  http://localhost:8000/api/documents/upload
```

List documents:

```bash
curl http://localhost:8000/api/documents
```

Inspect the database:

```bash
docker compose exec postgres psql -U postgres -d enterprise_rag -c "SELECT id, filename, status, file_type FROM documents ORDER BY created_at DESC;"
```

Inspect saved files:

```bash
find data/uploads -maxdepth 4 | cat
```

---

## ✅ Expected Response Shape

```json
{
  "id": "uuid",
  "filename": "sample.pdf",
  "file_type": "pdf",
  "file_size": 12345,
  "status": "uploaded",
  "total_pages": null,
  "total_chunks": null,
  "created_at": "2026-05-30T12:00:00Z",
  "updated_at": "2026-05-30T12:00:00Z"
}
```

---

## 🔍 Verification Checklist

After a successful upload, verify all three are true:

1. a row exists in `documents`
2. the file exists under `data/uploads/default/{document_id}/`
3. the API returns the same document ID and status

If any of those fail, fix the service before moving on.

---

## 🐛 Common Issues

### 1. Empty files being saved

Use streamed writes or `await file.read()` exactly once. If you read it multiple times, the second read will be empty unless you reset the cursor.

### 2. File type detection is inconsistent

Rely on extension + MIME together, not only one of them.

### 3. Upload works but document row is missing

Check that `db.add()`, `db.commit()`, and `db.refresh()` are all called.

### 4. Relative paths break in Docker

Prefer paths built from settings and `pathlib.Path`, and verify the backend container mounts `./data/uploads:/data/uploads` or an equivalent path you are actually using.

---

## 🎯 Phase 4 Checklist

- [ ] Created `schemas/document.py`
- [ ] Implemented file validation
- [ ] Implemented local file storage
- [ ] Implemented `POST /api/documents/upload`
- [ ] Implemented `GET /api/documents`
- [ ] Implemented `GET /api/documents/{document_id}`
- [ ] Saved uploaded document metadata to PostgreSQL
- [ ] Verified files exist on disk
- [ ] Verified documents can be listed through the API

---

## 📝 Commit Phase 4

```bash
git add .
git commit -m "feat: Phase 4 - Document upload workflow

- Added document schemas
- Implemented PDF/TXT upload validation
- Added local file storage
- Persisted document metadata in PostgreSQL
- Added document upload and listing endpoints"
```

---

## ➡️ Next Phase

Continue with **Phase 5: PDF Processing**

- Read: `docs/implementation-plan/06-phase-05-pdf-processing.md`
- Goal: parse uploaded files, split them into chunks, and persist chunk records

---

**Phase 4 Complete!**

**Status:** ✅ Upload workflow ready

