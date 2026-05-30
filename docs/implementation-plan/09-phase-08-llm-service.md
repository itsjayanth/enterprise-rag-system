# Phase 8: LLM Service

**Goal:** Connect the system to a locally running Ollama service that serves Llama 3.1 on CPU/Apple MPS and supports both normal and streaming generation via an OpenAI-compatible API.

**Duration:** 1-2 hours

**Dependencies:**
- `08-phase-07-vector-storage.md` complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ Ollama installed and running Llama 3.1:8B locally
- ✅ Backend client wrapper for chat completions
- ✅ Streaming token support from the backend client
- ✅ Health check for the LLM endpoint

---

## 🧭 Local Mac LLM Strategy

**vLLM requires a CUDA GPU and does not run on Mac.**

For local Mac development we use **Ollama**, which:

- runs natively on macOS (no Docker, no GPU required)
- uses Apple MPS (Metal GPU) on Apple Silicon for faster inference
- falls back to CPU on Intel Mac — slower but functional
- exposes an **OpenAI-compatible REST API** at `http://localhost:11434/v1`
- requires zero code changes compared to vLLM because the API surface is identical

**Future GPU path:** when a GPU is available, swap `LLM_SERVICE_URL` to point at a vLLM container and set `LLM_MODEL_NAME` to the Hugging Face model ID. The backend client requires zero changes.

---

## 📂 Files to Create or Update

```text
backend/app/services/
└── llm_client.py
```

Also verify or update:

```text
.env
backend/app/config.py
```

---

## 🐳 Step 1: Ollama is NOT in Docker Compose

Ollama runs as a native macOS service, not inside Docker.

Do **not** add an `llm-service` container to `docker-compose.yml` for local dev.

When the backend runs inside Docker and needs to reach Ollama on the Mac host, use:

```bash
http://host.docker.internal:11434/v1
```

When the backend runs locally (outside Docker), use:

```bash
http://localhost:11434/v1
```

---

## ▶️ Step 2: Start Ollama

```bash
ollama serve
```

This starts the Ollama server in the foreground. Or let it run in the background — on macOS after `brew install ollama` it can run automatically.

Confirm the model is available:

```bash
curl http://localhost:11434/v1/models
```

If the model is not listed, pull it:

```bash
ollama pull llama3.1:8b
```

---

## ⚙️ Step 3: Update `.env`

```bash
# LLM — Ollama local Mac
LLM_SERVICE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3.1:8b
```

If the backend runs inside Docker, change `localhost` to `host.docker.internal`:

```bash
LLM_SERVICE_URL=http://host.docker.internal:11434/v1
```

---

## 🔌 Step 4: Add backend dependency

Use `httpx` (already in requirements) or the OpenAI Python SDK.

Recommended — add to `backend/requirements.txt`:

```txt
openai>=1.30.0
```

The OpenAI SDK works directly against Ollama's OpenAI-compatible endpoint.

---

## 🧠 Step 5: Create `backend/app/services/llm_client.py`

This client wraps the LLM calls so the rest of the app never calls Ollama directly.

### Recommended methods

- `health_check() -> bool`
- `generate(messages, temperature=None, max_tokens=None) -> str`
- `stream_generate(messages, temperature=None, max_tokens=None) -> AsyncGenerator[str]`

### Example structure

```python
from openai import AsyncOpenAI
from app.config import settings

class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.llm_service_url,
            api_key="ollama",  # Ollama ignores the key but the field is required
        )
        self.model = settings.llm_model_name

    async def generate(self, messages: list[dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False,
            temperature=kwargs.get("temperature", 0.1),
            max_tokens=kwargs.get("max_tokens", 512),
        )
        return response.choices[0].message.content

    async def stream_generate(self, messages: list[dict], **kwargs):
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=kwargs.get("temperature", 0.1),
            max_tokens=kwargs.get("max_tokens", 512),
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
```

### Input message format

```python
[
    {"role": "system", "content": "Answer only from the provided context."},
    {"role": "user", "content": "Question: ..."},
]
```

---

## 🧪 Step 6: Test Ollama directly

Non-streaming:

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
    "stream": false,
    "temperature": 0.1,
    "max_tokens": 32
  }'
```

Streaming:

```bash
curl -N http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Count from one to five."}],
    "stream": true,
    "max_tokens": 64
  }'
```

---

## 🧪 Step 7: Test the backend wrapper

```python
from app.services.llm_client import LLMClient
import asyncio

client = LLMClient()

response = asyncio.run(client.generate([
    {"role": "system", "content": "Be concise."},
    {"role": "user", "content": "What is a vector database in one sentence?"},
]))
print(response)
```

---

## ⚠️ CPU Performance Notes

On a Mac without Apple Silicon, inference will be CPU-only and slower:

| Hardware | Approximate token speed |
|---------|------------------------|
| Apple M1/M2/M3/M4 (MPS) | ~15-30 tokens/sec |
| Intel Mac (CPU only) | ~3-8 tokens/sec |

This is acceptable for development. If speed is too slow during testing, reduce `max_tokens` in the chat config.

---

## 🔮 Future GPU Path

When a GPU becomes available:

1. Start a vLLM container:
   ```bash
   docker run --gpus all -p 8003:8000 vllm/vllm-openai:latest \
     --model meta-llama/Meta-Llama-3.1-8B-Instruct \
     --dtype float16 --max-model-len 8192
   ```
2. Update `.env`:
   ```bash
   LLM_SERVICE_URL=http://localhost:8003/v1
   LLM_MODEL_NAME=meta-llama/Meta-Llama-3.1-8B-Instruct
   ```
3. The backend `LLMClient` requires **no code changes**.

---

## ✅ Success Criteria

This phase is complete when:

- `ollama serve` is running
- `llama3.1:8b` model is available locally
- `/v1/models` responds with the model listed
- Backend can generate a non-streaming completion
- Backend can stream tokens from Ollama

---

## 🐛 Common Issues

### 1. `Connection refused` on port 11434

Run `ollama serve` first.

### 2. Model not found

Run `ollama pull llama3.1:8b`.

### 3. Backend in Docker cannot reach Ollama

Use `http://host.docker.internal:11434/v1` instead of `http://localhost:11434/v1`.

### 4. Very slow responses on Intel Mac

This is expected on CPU-only. Use shorter `max_tokens` for testing.

---

## 🎯 Phase 8 Checklist

- [ ] Ollama installed and `llama3.1:8b` downloaded
- [ ] `ollama serve` running and reachable
- [ ] `.env` updated with `LLM_SERVICE_URL` and `LLM_MODEL_NAME`
- [ ] Backend `LLMClient` wrapper created
- [ ] Non-streaming completion verified
- [ ] Streaming completion verified

---

## 📝 Commit Phase 8

```bash
git add .
git commit -m "feat: Phase 8 - LLM service with Ollama (local Mac CPU)

- Added Ollama as LLM backend for local Mac development
- Added backend LLM client with OpenAI-compatible wrapper
- Added streaming and non-streaming generation support
- Documented future GPU/vLLM upgrade path"
```

---

## ➡️ Next Phase

Continue with **Phase 9: Retrieval Pipeline**

- Read: `docs/implementation-plan/10-phase-09-retrieval.md`

---

**Phase 8 Complete!**

**Status:** ✅ LLM generation ready on local Mac
