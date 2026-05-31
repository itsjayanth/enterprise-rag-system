# Phase 6: Embedding Service

**Goal:** Build the embedding microservice that serves BGE-M3 embeddings for document chunks and user queries.

**Duration:** 3-4 hours

**Dependencies:**
- `06-phase-05-pdf-processing.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ A dedicated FastAPI embedding service
- ✅ BGE-M3 model loading on CPU (primary path for local Mac)
- ✅ Batch embedding endpoint for document chunks
- ✅ Query embedding endpoint for retrieval
- ✅ Health checks and startup logging
- ✅ Service verified through Docker Compose

---

## 📂 Files to Create or Update

```text
ml-services/embedding-service/
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py
    └── model.py
```

Optional but useful:

```text
ml-services/embedding-service/app/schemas.py
```

---

## 🧭 Service Responsibilities

This service should do only one job: generate embeddings efficiently.

### It must support two use cases

1. **document chunks**
   - batched
   - high throughput
   - normalized vectors

2. **user queries**
   - single-text endpoint
   - instruction-aware encoding for retrieval

Keep business logic out of this service. It should not talk directly to PostgreSQL or Pinecone.

---

## 🧠 Step 1: Create `app/model.py`

This module should load and expose the BGE-M3 model.

### Responsibilities

- load `SentenceTransformer(settings.embedding_model_name)`
- detect device: use MPS on Apple Silicon, otherwise CPU
- no CUDA required; GPU is a future upgrade path
- provide helper methods:
  - `embed_documents(texts: list[str])`
  - `embed_query(text: str)`

### Query embedding rule

Prefix query text with the instruction recommended for BGE retrieval:

```text
Represent this query for retrieving relevant documents:
```

### Important settings

- `normalize_embeddings=True`
- `batch_size=32` as a good default
- `show_progress_bar=False`

### Critical consistency rule

Use the **same embedding model instance/configuration** for both:

- `POST /embed/documents`
- `POST /embed/query`

For this project, both endpoints must use `BAAI/bge-m3`.

The only difference is input formatting:

- documents use the raw chunk text
- queries use the same BGE-M3 model, but with the retrieval instruction prefix

Do not use one model for document chunks and another model for search queries if those vectors are meant to live in the same Pinecone index.

---

## 🌐 Step 2: Create `app/main.py`

This is the embedding service entry point.

### Endpoints to implement

#### `GET /health`

Return service readiness and model/device information.

Example response:

```json
{
  "status": "healthy",
  "service": "embedding-service",
  "model": "BAAI/bge-m3",
  "device": "cpu"   # "mps" on Apple Silicon; "cuda" reserved for future GPU
}
```

#### `POST /embed/documents`

Request body:

```json
{
  "texts": ["chunk 1", "chunk 2"]
}
```

Response body:

```json
{
  "embeddings": [[0.01, 0.02], [0.03, 0.04]],
  "count": 2,
  "dimensions": 1024
}
```

#### `POST /embed/query`

Request body:

```json
{
  "text": "what does this document say about billing?"
}
```

Response body:

```json
{
  "embedding": [0.01, 0.02],
  "dimensions": 1024
}
```

---

## 📦 Step 3: Create `requirements.txt`

Minimum useful dependencies:

```txt
fastapi
uvicorn[standard]
sentence-transformers
torch
transformers
pydantic
pydantic-settings
```

If you want smaller images later, you can pin exact versions and optimize separately.

---

## 🐳 Step 4: Create `Dockerfile`

Recommended pattern:

1. start from `python:3.11-slim`
2. install system dependencies if needed
3. copy `requirements.txt`
4. install dependencies
5. copy `app/`
6. expose port `8001`
7. run uvicorn

### Example command

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## 🔌 Step 5: Connect it to Docker Compose

The Phase 1 scaffold already includes an `embedding-service` container.

Verify these are consistent:

- service port is `8001`
- the container mounts `./data/models:/data/models`
- `.env` exposes `EMBEDDING_MODEL_NAME`
- backend points to `EMBEDDING_SERVICE_URL=http://embedding-service:8001`

If any of those differ, fix them now before moving on.

---

## ▶️ Step 6: Start and test the service

```bash
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system
docker compose up -d embedding-service
```

Check health:

```bash
curl http://localhost:8001/health
```

Test document embeddings:

```bash
curl -X POST http://localhost:8001/embed/documents \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Enterprise RAG systems improve answer quality.", "Chunking preserves retrieval quality."]}'
```

Test query embeddings:

```bash
curl -X POST http://localhost:8001/embed/query \
  -H "Content-Type: application/json" \
  -d '{"text": "How are documents chunked?"}'
```

---

## ✅ Expected Validation

The service is ready when:

- the model loads successfully on startup
- `/health` returns the device and model name
- `/embed/documents` returns one embedding per input string
- `/embed/query` returns a single embedding
- the returned vector length is `1024`

---

## ⚠️ Practical Notes

### On CPU-only development machines

BGE-M3 will still work, just slower.

That is acceptable for MVP development.

### On local Mac (primary dev environment)

- PyTorch detects device automatically
- Apple Silicon Macs: device is `mps` (Metal GPU, fast)
- Intel Macs: device is `cpu` (slower but fully functional)
- No CUDA, no nvidia-docker needed
- Recommended batch size: **8** on CPU, up to **32** on MPS
- Model download: ~1.2 GB, cached in `data/models` via `HF_HOME`

### Future GPU machines

Make sure:

On future GPU machines (CUDA):

- PyTorch sees CUDA
- Docker has GPU access if you run inside containers (nvidia-container-toolkit required)
- batch sizes can go up to 64+ for optimal throughput
- VRAM requirement: ~4 GB minimum for BGE-M3

### Keep this service stateless

Do not cache request results in local memory yet. Add Redis caching later at the backend layer if needed.

---

## 🐛 Common Issues

### 1. Model download is very slow on first startup

That is normal. The first run downloads the model into the cache directory.

### 2. Service crashes with out-of-memory

Lower:

- batch size
- worker count
- concurrent requests

### 3. Returned vector dimension is not 1024

Double-check the actual model being loaded from the environment.

### 4. Slow embedding speed on Intel Mac

This is expected on CPU-only. BGE-M3 on CPU takes ~2-5 sec per batch of 8. For development with small test documents this is fine. Apple Silicon Macs are significantly faster.

Optimization tips:
- Set `batch_size=4` or `batch_size=8` on CPU
- Use shorter test documents during development

### 5. `torch.cuda.is_available()` is false

This is expected on Mac — there is no CUDA on macOS. The service uses CPU (or MPS on Apple Silicon) automatically. No action needed.

---

## 🎯 Phase 6 Checklist

- [ ] Created embedding service FastAPI app
- [ ] Loaded BGE-M3 model with device detection
- [ ] Implemented `POST /embed/documents`
- [ ] Implemented `POST /embed/query`
- [ ] Implemented `GET /health`
- [ ] Built and started the Docker service
- [ ] Verified output vector dimension is 1024

---

## 📝 Commit Phase 6

```bash
git add .
git commit -m "feat: Phase 6 - Embedding service with BGE-M3

- Added dedicated embedding microservice
- Loaded BGE-M3 on CPU/MPS (no GPU required on Mac)
- Added document and query embedding endpoints
- Added health checks and Docker support"
```

---

## ➡️ Next Phase

Continue with **Phase 7: Vector Storage**

- Read: `docs/implementation-plan/08-phase-07-vector-storage.md`
- Goal: connect chunk embeddings to Pinecone and enable similarity search

---

**Phase 6 Complete!**

**Status:** ✅ Embedding generation ready

