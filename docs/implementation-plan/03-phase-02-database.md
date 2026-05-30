# Phase 2: Database Setup

**Goal:** Create the PostgreSQL schema, SQLAlchemy models, session management, and Alembic migrations that support document ingestion, chunk storage, and chat history.

**Duration:** 2-3 hours

**Dependencies:**
- `01-environment-setup.md` complete
- `02-phase-01-scaffolding.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ SQLAlchemy engine and session management
- ✅ Base ORM models for documents, chunks, chat sessions, and messages
- ✅ Alembic configured for schema migrations
- ✅ Initial migration generated and applied
- ✅ PostgreSQL tables created and verified

---

## 🧭 Scope for This Implementation

The design docs describe a future multi-user system with authentication and `user_id`-based isolation.

**For the current implementation plan, keep Phase 2 intentionally simpler:**

- No auth tables yet
- No `users` table yet
- No multi-tenant filtering yet
- Build the schema needed for:
  1. document upload
  2. document processing
  3. chunk persistence
  4. chat sessions and messages

This keeps the MVP focused on the core workflow:

**upload → parse → chunk → embed → store vectors → retrieve → chat**

---

## 📂 Files to Create or Update

```text
backend/
├── alembic.ini
├── app/
│   ├── database.py
│   └── models/
│       ├── __init__.py
│       ├── document.py
│       ├── chunk.py
│       └── chat.py
└── migrations/
	├── env.py
	├── script.py.mako
	└── versions/
		└── 0001_initial_schema.py
```

---

## 🏗️ Step 1: Create `backend/app/database.py`

Create the database bootstrap file.

### Responsibilities

- Load the database URL from settings
- Create SQLAlchemy engine
- Create session factory
- Expose declarative base
- Provide `get_db()` dependency for FastAPI

### Implementation Notes

- Use SQLAlchemy 2.x style
- Enable `pool_pre_ping=True`
- Keep `echo=False` for cleaner logs
- Import this module from API routes and services later

### Recommended structure

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
	pass


engine = create_engine(
	settings.database_url,
	pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
```

---

## 🧱 Step 2: Define the `Document` model

Create `backend/app/models/document.py`.

### Suggested fields

| Field | Type | Notes |
|------|------|-------|
| `id` | UUID | Primary key |
| `filename` | String | Original filename shown in UI |
| `file_size` | BigInteger | Bytes |
| `file_type` | String | `pdf` or `txt` |
| `storage_path` | String | Saved file path |
| `status` | String | `uploaded`, `processing`, `embedded`, `completed`, `failed` |
| `total_pages` | Integer nullable | Filled after parsing |
| `total_chunks` | Integer nullable | Filled after chunking |
| `error_message` | Text nullable | Failure reason |
| `created_at` | DateTime | Default now |
| `updated_at` | DateTime | Auto-update |
| `processed_at` | DateTime nullable | Set when pipeline completes |

### Relationships

- `Document.chunks` → one-to-many with `Chunk`

### Notes

- Keep the status field as a string for now; enums can be added later.
- Use cascade delete so removing a document removes all chunks.

---

## 🧩 Step 3: Define the `Chunk` model

Create `backend/app/models/chunk.py`.

### Suggested fields

| Field | Type | Notes |
|------|------|-------|
| `id` | UUID | Primary key |
| `document_id` | UUID FK | Links to `documents.id` |
| `chunk_index` | Integer | Sequential order within document |
| `content` | Text | Actual searchable chunk text |
| `page_number` | Integer nullable | Important for citations |
| `char_count` | Integer | Quick metadata |
| `token_count` | Integer nullable | Useful for retrieval limits |
| `embedding_id` | String nullable | Pinecone/vector id |
| `chunk_metadata` | JSON/JSONB nullable | Extra metadata; avoid `metadata` name in SQLAlchemy |
| `created_at` | DateTime | Default now |

### Important

Do **not** use the attribute name `metadata` on the ORM model because SQLAlchemy already reserves it on declarative models.

Use one of these instead:

- `chunk_metadata`
- `metadata_json`

### Constraints

- Unique on `document_id + chunk_index`
- Index on `document_id`
- Index on `embedding_id`

---

## 💬 Step 4: Define chat models

Create `backend/app/models/chat.py`.

### `ChatSession`

| Field | Type | Notes |
|------|------|-------|
| `id` | UUID | Primary key |
| `title` | String nullable | Auto-generated from first message later |
| `created_at` | DateTime | Default now |
| `updated_at` | DateTime | Auto-update |

### `Message`

| Field | Type | Notes |
|------|------|-------|
| `id` | UUID | Primary key |
| `session_id` | UUID FK | Links to chat session |
| `role` | String | `user` or `assistant` |
| `content` | Text | Message body |
| `sources` | JSON nullable | Retrieval citations |
| `token_count` | Integer nullable | Optional tracking |
| `created_at` | DateTime | Default now |

### Relationships

- `ChatSession.messages` → one-to-many with `Message`

---

## 🔌 Step 5: Export models from `backend/app/models/__init__.py`

Update the package init so Alembic can discover all models.

```python
from app.models.chat import ChatSession, Message
from app.models.chunk import Chunk
from app.models.document import Document

__all__ = ["Document", "Chunk", "ChatSession", "Message"]
```

This import aggregation is important because Alembic only sees models that are imported into the metadata graph.

---

## 🧾 Step 6: Configure Alembic

Initialize Alembic inside `backend/` if it does not exist yet:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system/backend
alembic init migrations
```

Then configure:

### `backend/alembic.ini`

- Set `script_location = migrations`
- Leave DB URL blank if you want `env.py` to read from settings

### `backend/migrations/env.py`

Import the SQLAlchemy metadata from your app:

```python
from app.database import Base
from app.models import *  # noqa: F401,F403

target_metadata = Base.metadata
```

Also read the database URL from `app.config.settings` so Alembic uses the same connection config as the app.

---

## 🛠️ Step 7: Create the initial migration

After the models are in place, generate the first migration:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system/backend
alembic revision --autogenerate -m "initial schema"
```

Expected tables:

- `documents`
- `chunks`
- `chat_sessions`
- `messages`

### Review the generated migration carefully

Check that it includes:

- primary keys
- foreign keys
- indexes
- unique constraint on `chunks(document_id, chunk_index)`
- JSON/JSONB column for `sources` and `chunk_metadata`

If anything looks wrong, fix the models and regenerate before moving on.

---

## ▶️ Step 8: Apply the migration

Start infrastructure first:

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
make dev-infra
```

Then run the migration:

```bash
docker compose exec backend alembic upgrade head
```

If the backend container is not ready yet, you can also run locally from the `backend/` directory after activating your virtual environment.

---

## ✅ Step 9: Verify the schema in PostgreSQL

Open a database shell:

```bash
docker compose exec postgres psql -U postgres -d enterprise_rag
```

Run these checks:

```sql
\dt

\d documents
\d chunks
\d chat_sessions
\d messages
```

You should see:

- foreign key from `chunks.document_id` to `documents.id`
- foreign key from `messages.session_id` to `chat_sessions.id`
- indexes on high-read columns

---

## 🧪 Recommended Smoke Test

From a Python shell inside the backend environment:

```python
from app.database import SessionLocal
from app.models.document import Document

db = SessionLocal()

doc = Document(
	filename="sample.pdf",
	file_size=12345,
	file_type="pdf",
	storage_path="/data/uploads/default/doc-1/original.pdf",
	status="uploaded",
)

db.add(doc)
db.commit()
db.refresh(doc)

print(doc.id, doc.filename, doc.status)
db.close()
```

If this succeeds, your model mapping and session handling are working.

---

## 🐛 Common Issues

### 1. Alembic says no changes detected

Usually caused by one of these:

- models are not imported in `app.models.__init__`
- `target_metadata` is not set correctly in `migrations/env.py`
- the migration command is running from the wrong directory

### 2. Reserved attribute error for `metadata`

Rename the ORM field to `chunk_metadata` or `metadata_json`.

### 3. UUID or JSON import problems

Use PostgreSQL dialect types where needed:

```python
from sqlalchemy.dialects.postgresql import JSONB, UUID
```

### 4. `relation does not exist`

Run:

```bash
docker compose exec backend alembic upgrade head
```

before testing inserts.

---

## 🎯 Phase 2 Checklist

- [ ] Created `backend/app/database.py`
- [ ] Created `Document` model
- [ ] Created `Chunk` model
- [ ] Created `ChatSession` and `Message` models
- [ ] Exported models from `app/models/__init__.py`
- [ ] Configured Alembic
- [ ] Generated initial migration
- [ ] Applied migration successfully
- [ ] Verified tables in PostgreSQL
- [ ] Inserted at least one test record successfully

---

## 📝 Commit Phase 2

```bash
git add .
git commit -m "feat: Phase 2 - Database schema and migrations

- Added SQLAlchemy engine and session management
- Created document, chunk, chat session, and message models
- Configured Alembic for migrations
- Generated and applied initial schema migration"
```

---

## ➡️ Next Phase

Continue with **Phase 3: FastAPI Core**

- Read: `docs/implementation-plan/04-phase-03-fastapi-core.md`
- Goal: start the API server, load settings, add structured logging, and expose health checks

---

**Phase 2 Complete!**

**Status:** ✅ Ready for FastAPI foundation

