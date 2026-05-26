# GenAI Tech Stack - Enterprise RAG System

## Executive Summary

This document outlines the GenAI technology stack for a production-grade RAG system using **FREE, open-source models** optimized for document question-answering, with production inference serving and scalability in mind.

---

## 1. Embedding Model Selection

### **Recommended: BGE-M3 (BAAI/bge-m3)**

**Model Details:**
- **Name:** `BAAI/bge-m3`
- **Size:** 568M parameters
- **Dimensions:** 1024
- **Type:** Hybrid (Dense + Sparse + Multi-Vector)
- **License:** MIT (Commercial-friendly)

**Why BGE-M3:**

✅ **Best-in-class for production RAG:**
- Ranked #1 on MTEB leaderboard for retrieval tasks (as of 2025-2026)
- Hybrid retrieval support (dense + sparse BM25-like + ColBERT-style)
- Multi-lingual support (100+ languages)
- Optimized for long documents (8192 token context)

✅ **Production advantages:**
- Batch inference support
- Efficient memory footprint
- Fast encoding speed (~1000 docs/sec on GPU)
- Built-in support in sentence-transformers

✅ **RAG-specific benefits:**
- Instruction-aware embeddings
- Domain adaptation capability
- Strong performance on technical/enterprise documents
- No fine-tuning required for most use cases

**Alternative Options:**

| Model | Pros | Cons | Use Case |
|-------|------|------|----------|
| **sentence-transformers/all-MiniLM-L6-v2** | Fastest (CPU-friendly), smallest (80MB) | Lower accuracy | High-throughput, cost-sensitive |
| **intfloat/e5-mistral-7b-instruct** | Instruction-tuned, excellent quality | Large (7B params), slower | Quality over speed |
| **Alibaba-NLP/gte-large-en-v1.5** | Excellent English performance | English-only | English-only corpus |

**Deployment Strategy:**
```python
# Load with sentence-transformers
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-m3')
model.to('cuda')  # GPU acceleration

# Batch encoding for production
embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=False,
    normalize_embeddings=True  # Important for cosine similarity
)
```

**Resource Requirements:**
- **GPU:** 4GB VRAM minimum (T4, L4, A10 recommended)
- **CPU fallback:** Possible but 10-20x slower
- **Batch size:** 32-64 for optimal throughput

---

## 2. Reranker Model Selection

### **Recommended: BAAI/bge-reranker-v2-m3**

**Model Details:**
- **Name:** `BAAI/bge-reranker-v2-m3`
- **Size:** 568M parameters
- **Type:** Cross-encoder
- **Score range:** 0-1 (sigmoid normalized)
- **License:** MIT

**Why BGE-Reranker-v2-M3:**

✅ **State-of-the-art reranking:**
- Best reranking performance on BEIR benchmark
- Multi-lingual support
- Fast inference (~100 pairs/sec on GPU)
- Pairs naturally with BGE-M3 embeddings

✅ **Production benefits:**
- Low latency (<50ms for 10 candidates)
- Batch processing support
- Deterministic scoring
- No calibration needed

✅ **RAG pipeline integration:**
- Two-stage retrieval pattern:
  1. BGE-M3 retrieves top 100 candidates (fast)
  2. Reranker scores top 10-20 (accurate)
- Typical improvement: 15-30% MRR increase

**Alternative Options:**

| Model | Pros | Cons |
|-------|------|------|
| **cross-encoder/ms-marco-MiniLM-L-6-v2** | Lightweight, fast | Lower accuracy, English-only |
| **BAAI/bge-reranker-large** | Highest accuracy | Slower, larger memory |
| **mixedbread-ai/mxbai-rerank-large-v1** | Excellent for code/technical docs | Larger, slower |

**Deployment Pattern:**
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('BAAI/bge-reranker-v2-m3')

# Rerank retrieved chunks
scores = reranker.predict([
    (query, chunk) for chunk in retrieved_chunks
])

# Sort by score and take top K
reranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)[:5]
```

**When to use reranking:**
- Retrieve top 50-100 with vector search (recall-focused)
- Rerank to top 5-10 (precision-focused)
- Critical for multi-hop reasoning
- Essential when context window is limited

---

## 3. LLM Selection

### **Recommended: Meta-Llama-3.1-8B-Instruct**

**Model Details:**
- **Name:** `meta-llama/Meta-Llama-3.1-8B-Instruct`
- **Size:** 8B parameters
- **Context window:** 128K tokens (practical: 8-16K for RAG)
- **License:** Llama 3.1 Community License (commercial use allowed)
- **Quantization:** Supports 4-bit, 8-bit (2-4x memory reduction)

**Why Llama 3.1-8B-Instruct:**

✅ **Best production LLM for RAG:**
- **SOTA performance:** Best 8B model on reasoning benchmarks
- **Instruction following:** Excellent at following RAG prompts
- **Context adherence:** Strong citation and grounding capabilities
- **Commercial friendly:** Free for production use
- **Active ecosystem:** Best tooling support (vLLM, TGI, Hugging Face)

✅ **RAG-specific strengths:**
- Accurate citation generation
- Minimal hallucination with provided context
- Good at saying "I don't know" when context insufficient
- Excellent at multi-turn conversations
- Strong multi-lingual capabilities (8 languages)

✅ **Production advantages:**
- **Inference speed:** 40-60 tokens/sec on A10G GPU
- **Memory efficient:** ~16GB VRAM for FP16, ~5GB with 4-bit quantization
- **Batching support:** Continuous batching in vLLM
- **Scalable:** Can run 2-3 replicas on single A10G 24GB

**Performance Metrics (RAG tasks):**
- MMLU: 69.4% (reasoning)
- TruthfulQA: 63.2% (factuality)
- HumanEval: 72.6% (code understanding)
- MT-Bench: 8.1/10 (instruction following)

**Alternative Options:**

| Model | Pros | Cons | Recommendation |
|-------|------|------|----------------|
| **Qwen2.5-7B-Instruct** | Slightly better reasoning, 128K context | Less ecosystem support | Good alternative |
| **Mistral-7B-Instruct-v0.3** | Fast, efficient | Weaker instruction following | Cost-optimized option |
| **Llama-3.1-70B-Instruct** | Best quality | Requires 2-4x A100 GPUs | Enterprise tier |
| **Phi-3-medium-14B** | Good quality/size ratio | Limited context (4K) | Not recommended for RAG |

**Quantization Strategy:**

| Quantization | VRAM | Speed | Quality | Use Case |
|--------------|------|-------|---------|----------|
| **FP16** | 16GB | Baseline | 100% | Production (recommended) |
| **8-bit (LLM.int8)** | 8GB | 0.9x | 99% | Memory-constrained |
| **4-bit (GPTQ/AWQ)** | 5GB | 1.2x | 95-97% | High throughput |

**When to upgrade to 70B:**
- Complex multi-hop reasoning required
- High-stakes accuracy needs (medical, legal)
- Multi-lingual advanced reasoning
- Budget allows multi-GPU inference

---

## 4. Inference Server Selection

### **Recommended: vLLM**

**Why vLLM:**

✅ **Best production inference server (2025-2026):**
- **PagedAttention:** 2-4x higher throughput than naive serving
- **Continuous batching:** Optimal GPU utilization
- **OpenAI-compatible API:** Drop-in replacement
- **Streaming support:** Native SSE streaming for chat UI
- **Production-proven:** Used by Meta, Databricks, Anyscale

✅ **Performance advantages:**
- **Throughput:** 10-20x higher than transformers
- **Latency:** First token <200ms, subsequent ~20ms
- **Memory efficiency:** Dynamic KV cache management
- **Batching:** Automatic request batching
- **Quantization:** Built-in AWQ, GPTQ support

✅ **Kubernetes-ready:**
- Official Docker images
- Horizontal scaling support
- Health check endpoints
- Prometheus metrics export
- GPU resource management

**vLLM Deployment:**

```yaml
# Kubernetes Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-llama-8b
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        args:
          - --model=meta-llama/Meta-Llama-3.1-8B-Instruct
          - --tensor-parallel-size=1
          - --max-model-len=8192
          - --dtype=float16
        resources:
          limits:
            nvidia.com/gpu: 1
          requests:
            memory: 20Gi
```

```python
# Python client (OpenAI-compatible)
from openai import OpenAI

client = OpenAI(
    base_url="http://vllm-service:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    messages=[{"role": "user", "content": prompt}],
    stream=True,
    temperature=0.1,
    max_tokens=512
)
```

**Alternative Inference Servers:**

| Server | Pros | Cons | Use Case |
|--------|------|------|----------|
| **Text Generation Inference (TGI)** | Hugging Face ecosystem, good K8s support | Slower than vLLM (1.5-2x) | HF-first organizations |
| **Ollama** | Easiest setup, good for dev | Not production-grade, no K8s patterns | Local development only |
| **OpenLLM** | BentoML integration, good for MLOps | Smaller community | BentoML users |
| **Ray Serve** | Best for complex serving graphs | Heavyweight, complex setup | Multi-model pipelines |

**Performance Comparison (Llama 3.1-8B):**

| Server | Throughput (req/s) | Latency P50 (ms) | GPU Util | Memory |
|--------|-------------------|------------------|----------|---------|
| vLLM | 45-60 | 180 | 85-95% | 16GB |
| TGI | 25-35 | 250 | 70-80% | 18GB |
| Transformers | 5-8 | 600 | 40-50% | 16GB |

**Recommendation:** Use **vLLM** for production, **Ollama** for local development.

---

## 5. RAG Framework Selection

### **Recommended: LangGraph + LangChain**

**Strategy: Use Both (Different Purposes)**

### **LangGraph for Complex Workflows**

**Use LangGraph for:**
- ✅ Multi-step agentic RAG
- ✅ Conditional retrieval (when to retrieve vs when to answer)
- ✅ Self-correction and validation loops
- ✅ Complex state management
- ✅ Human-in-the-loop workflows

**Why LangGraph:**
- **State machine for RAG:** Explicit control flow
- **Debugging:** Clear graph visualization
- **Production-grade:** Built for complex pipelines
- **Checkpointing:** Resume long-running workflows
- **Type-safe:** Better error handling

**Example Use Cases:**
```
Query → Route Decision → 
  ├─ Simple: Direct Answer
  ├─ RAG: Retrieve → Rerank → Generate
  └─ Agent: Multi-step reasoning → Tool use → Synthesis
```

### **LangChain for Simple Pipelines**

**Use LangChain for:**
- ✅ Standard Q&A over documents
- ✅ Embeddings management
- ✅ Vector store integrations
- ✅ Document loaders and text splitters
- ✅ Prompt templates
- ✅ Integration utilities

**Why LangChain:**
- **Rich ecosystem:** 100+ integrations
- **Document processing:** Best-in-class loaders/splitters
- **Quick prototyping:** Fast to build standard RAG
- **Community:** Largest RAG framework community

**Architecture Decision:**

```
┌─────────────────────────────────────┐
│  Simple RAG (Phase 1)               │
│  → LangChain RetrievalQA            │
│  → Quick to ship                    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Advanced RAG (Phase 3)             │
│  → LangGraph state machine          │
│  → Hybrid retrieval                 │
│  → Reranking pipeline               │
│  → Self-correction                  │
└─────────────────────────────────────┘
```

**Hybrid Approach:**
```python
# Use LangChain components within LangGraph

from langgraph.graph import StateGraph
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter

# LangChain for utilities
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
vectorstore = Pinecone.from_existing_index("docs", embeddings)

# LangGraph for control flow
def retrieval_node(state):
    docs = vectorstore.similarity_search(state["query"], k=20)
    return {"retrieved_docs": docs}

def rerank_node(state):
    # Custom reranking logic
    reranked = reranker.rank(state["query"], state["retrieved_docs"])
    return {"final_docs": reranked[:5]}

graph = StateGraph(state_schema)
graph.add_node("retrieve", retrieval_node)
graph.add_node("rerank", rerank_node)
# ... build graph
```

**Why NOT just LangChain:**
- Complex conditional logic becomes spaghetti code
- Hard to debug multi-step flows
- State management is implicit
- Limited observability

**Why NOT just custom code:**
- Reinventing the wheel (chunking, loaders, etc.)
- Missing integrations (vector stores, embeddings)
- No observability tooling

**Final Recommendation:** 
- **Phase 1-2:** LangChain for speed
- **Phase 3+:** Migrate to LangGraph for advanced patterns
- **Always:** Use LangChain utilities (loaders, splitters, stores)

---

## 6. Document Processing Stack

### **PDF Parsing**

**Recommended: pypdfium2 + unstructured (hybrid approach)**

| Library | Pros | Cons | Use Case |
|---------|------|------|----------|
| **pypdfium2** | Fast, accurate text extraction | No table/layout detection | Clean text-based PDFs |
| **unstructured** | Layout-aware, tables, images | Slower, requires poppler | Complex documents |
| **PyMuPDF (fitz)** | Fast, page images | License concerns (AGPL) | Avoid for commercial |
| **docling (IBM)** | SOTA layout analysis | Heavy, slow | Research papers |

**Strategy:**
```python
# First: Try pypdfium2 (fast path)
# If low confidence: Fall back to unstructured

def parse_pdf(file_path):
    try:
        # Fast extraction
        text = pypdfium2.extract_text(file_path)
        if confidence_check(text):
            return text
    except:
        pass
    
    # Fallback: layout-aware
    from unstructured.partition.pdf import partition_pdf
    elements = partition_pdf(file_path)
    return elements
```

### **Text Chunking Strategy**

**Recommended: Semantic Chunking with Fallback**

**Phase 1: Recursive Character Splitter**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,  # ~400 tokens for BGE-M3
    chunk_overlap=50,  # 10% overlap for context
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len
)
```

**Phase 3: Semantic Chunking**
```python
from langchain_experimental.text_splitter import SemanticChunker

semantic_splitter = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="percentile",  # adaptive
    breakpoint_threshold_amount=0.95
)
```

**Metadata Tracking:**
```python
chunk_metadata = {
    "document_id": doc_id,
    "page_number": page_num,
    "chunk_index": idx,
    "source_file": filename,
    "created_at": timestamp,
    "char_count": len(chunk),
    "token_count": estimate_tokens(chunk)
}
```

---

## 7. Production Model Serving Architecture

### **Embedding Service**

```yaml
Service: embedding-service
Image: custom (sentence-transformers + FastAPI)
Model: BAAI/bge-m3
GPU: T4 (4GB) or A10G (24GB)
Replicas: 2-3
Scaling: HPA based on request latency
Endpoints:
  - POST /embed/documents (batch)
  - POST /embed/query (single)
```

### **LLM Service**

```yaml
Service: llm-service
Image: vllm/vllm-openai:latest
Model: meta-llama/Meta-Llama-3.1-8B-Instruct
GPU: A10G (24GB)
Replicas: 2
Scaling: Manual (GPU-bound)
Endpoints:
  - POST /v1/chat/completions (OpenAI-compatible)
  - POST /v1/completions
  - GET /health
```

### **Reranker Service**

```yaml
Service: reranker-service
Image: custom (CrossEncoder + FastAPI)
Model: BAAI/bge-reranker-v2-m3
GPU: T4 (4GB) shared with embeddings
Replicas: 1
Scaling: CPU-based (less critical path)
Endpoints:
  - POST /rerank
```

---

## 8. Model Download & Caching Strategy

### **Model Registry**

```python
# models/registry.py

MODELS = {
    "embeddings": {
        "name": "BAAI/bge-m3",
        "revision": "main",
        "cache_dir": "/mnt/models/embeddings"
    },
    "reranker": {
        "name": "BAAI/bge-reranker-v2-m3",
        "revision": "main",
        "cache_dir": "/mnt/models/reranker"
    },
    "llm": {
        "name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "revision": "main",
        "cache_dir": "/mnt/models/llm"
    }
}
```

### **Pre-download Strategy**

```bash
# Init container downloads models before app starts
# Use Kubernetes init containers

initContainers:
- name: model-downloader
  image: python:3.11
  command:
    - python
    - /scripts/download_models.py
  volumeMounts:
    - name: models
      mountPath: /mnt/models
```

---

## 9. Resource Requirements Summary

### **Development Environment**

| Service | CPU | RAM | GPU | Storage |
|---------|-----|-----|-----|---------|
| Embeddings | 2 cores | 4GB | 4GB VRAM | 2GB |
| Reranker | 1 core | 2GB | 2GB VRAM | 1GB |
| LLM | 4 cores | 8GB | 16GB VRAM | 16GB |
| **Total** | **7 cores** | **14GB** | **1x A10G (24GB)** | **20GB** |

### **Production Environment (Single Replica)**

| Service | CPU | RAM | GPU | Storage |
|---------|-----|-----|-----|---------|
| Embeddings | 4 cores | 8GB | 1x T4 | 2GB |
| Reranker | 2 cores | 4GB | Shared | 1GB |
| LLM | 8 cores | 20GB | 1x A10G | 16GB |
| **Total** | **14 cores** | **32GB** | **1x T4 + 1x A10G** | **20GB** |

### **Scaling Characteristics**

- **Embeddings:** Horizontally scalable, CPU/GPU hybrid
- **LLM:** GPU-bound, scale with more replicas
- **Reranker:** CPU-scalable, lower priority

---

## 10. Cost Optimization Strategies

### **Development:**
- Use Ollama for LLM (CPU-only)
- Use MiniLM for embeddings (CPU-friendly)
- Single instance of each service

### **Production:**
- 4-bit quantization for LLM (5GB VRAM)
- Cache embeddings in Redis (TTL: 1 hour)
- Batch document processing overnight
- Use spot instances for workers

### **Enterprise:**
- Full FP16 models
- Multi-GPU inference
- Hot standby replicas
- Real-time processing

---

## 11. Monitoring & Observability

### **GenAI-Specific Metrics**

```python
# Metrics to track
- embedding_latency_ms (p50, p95, p99)
- llm_generation_latency_ms
- tokens_per_second (throughput)
- retrieval_recall@k
- reranker_score_distribution
- context_relevance_score
- hallucination_rate
- user_feedback_score
```

### **Tools**

- **LangFuse:** Open-source LLM observability (LangSmith alternative)
- **Prometheus:** Metrics collection
- **Grafana:** Dashboards
- **Arize/Phoenix:** RAG-specific tracing

---

## Summary Table

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Embeddings** | BAAI/bge-m3 | Best MTEB performance, hybrid retrieval |
| **Reranker** | BAAI/bge-reranker-v2-m3 | SOTA cross-encoder, pairs with BGE-M3 |
| **LLM** | Llama 3.1-8B-Instruct | Best 8B model, commercial license, RAG-optimized |
| **Inference** | vLLM | 10-20x throughput, production-proven |
| **Framework** | LangGraph + LangChain | LangGraph for logic, LangChain for integrations |
| **PDF Parsing** | pypdfium2 + unstructured | Fast + accurate hybrid approach |
| **Chunking** | Semantic (Phase 3) | Better context preservation |

---

## Next Steps

1. Review and approve stack selections
2. Proceed to architecture design
3. Define API contracts
4. Set up model serving infrastructure
5. Implement observability from day 1

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** AI Systems Architecture Team

