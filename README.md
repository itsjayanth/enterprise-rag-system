# Enterprise RAG System

> **Production-grade document-aware RAG platform** with multi-user support, streaming responses, and scalable architecture.

## 🎯 Overview

A complete **enterprise RAG (Retrieval Augmented Generation) system** that enables users to upload PDF/TXT documents and chat with them using **free, open-source AI models**. Built with production best practices, microservices architecture, and designed for Kubernetes deployment.

### Key Features

✅ **Document Processing**
- PDF and TXT upload support
- Intelligent chunking with metadata preservation
- Page number tracking and citation support
- Async background processing with Celery

✅ **Advanced RAG Pipeline**
- Hybrid retrieval (vector + reranking)
- BGE-M3 embeddings (state-of-the-art)
- Cross-encoder reranking for precision
- Multi-stage retrieval optimization

✅ **Production LLM Integration**
- Llama 3.1-8B-Instruct (free, commercial-friendly)
- vLLM inference server (10-20x faster than naive serving)
- Streaming responses with SSE
- Batched inference for efficiency

✅ **Multi-User Architecture**
- JWT authentication
- User-isolated data (PostgreSQL + Pinecone filters)
- Chat session management
- Rate limiting and security

✅ **Scalability & Observability**
- Microservices architecture
- Kubernetes-ready deployments
- Prometheus metrics + Grafana dashboards
- Distributed tracing (OpenTelemetry)
- GenAI-specific observability (LangFuse)

---

## 🏗️ Architecture

### High-Level System Design

```
┌─────────────┐
│   Frontend  │ Next.js 14 + shadcn/ui + Streaming Chat
│  (React)    │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────────────┐
│           API Gateway (FastAPI)              │
│  • Authentication (JWT)                      │
│  • Rate Limiting                             │
│  • Request Routing                           │
└──────┬──────────────────────────────────────┘
       │
   ┌───┴───┬──────────┬──────────┐
   ▼       ▼          ▼          ▼
┌────┐  ┌────┐    ┌────┐    ┌────┐
│User│  │Doc │    │Chat│    │...  │  Microservices
│Svc │  │Svc │    │Svc │    │     │
└────┘  └────┘    └────┘    └────┘
   │       │         │          │
   └───┬───┴────┬────┴──────────┘
       │        │
       ▼        ▼
┌──────────────────────────────────────────┐
│        Processing Layer                  │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │Ingestion │  │Retrieval │  │Worker  │ │
│  │Service   │  │Service   │  │(Celery)│ │
│  └──────────┘  └──────────┘  └────────┘ │
└──────────────────────────────────────────┘
       │        │        │
   ┌───┴────┬───┴────┬───┴───┐
   ▼        ▼        ▼       ▼
┌─────┐ ┌───────┐ ┌─────┐ ┌─────┐
│BGE  │ │LLM    │ │Re   │ │Pine │  ML & Data Layer
│M3   │ │(vLLM) │ │rank │ │cone │
└─────┘ └───────┘ └─────┘ └─────┘
   GPU      GPU      GPU    Vector DB

┌──────────────────────────────────────────┐
│         Data Storage                     │
│  PostgreSQL  │  Redis  │  File Storage  │
└──────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14, shadcn/ui, TailwindCSS | Modern React with streaming UI |
| **API Gateway** | FastAPI | Authentication, routing, rate limiting |
| **Services** | Python, FastAPI | Microservices architecture |
| **LLM** | Llama 3.1-8B-Instruct | Document Q&A (free, 128K context) |
| **Embeddings** | BGE-M3 | Best MTEB performance (1024-dim) |
| **Reranker** | BGE-reranker-v2-m3 | Cross-encoder for precision |
| **Inference** | vLLM | Production LLM serving (10-20x faster) |
| **Vector DB** | Pinecone | Similarity search at scale |
| **Database** | PostgreSQL 16 | Relational data |
| **Cache** | Redis 7 | Celery broker + caching |
| **Queue** | Celery | Async task processing |
| **Storage** | Local filesystem | Document uploads (K8s PVC) |
| **Observability** | Prometheus, Grafana, LangFuse | Metrics, dashboards, tracing |
| **Deployment** | Docker, Kubernetes | Containerization & orchestration |

---

## 📁 Project Structure

```
enterprise-rag-system/
├── docs/                         # Complete design documentation
│   └── desing-docs/
│       ├── backend/              # Backend architecture docs
│       │   ├── architecture.md
│       │   ├── data-flow.md
│       │   ├── deployment.md
│       │   ├── observability.md
│       │   └── project-structure.md
│       ├── GEN-AI/               # AI/ML stack documentation
│       │   └── tech-stack.md
│       └── UI/                   # Frontend documentation
│           └── frontend-stack.md
│
├── services/                     # Microservices (Python)
│   ├── shared/                   # Shared libraries
│   ├── api-gateway/              # API Gateway
│   ├── user-service/             # User management
│   ├── document-service/         # Document uploads
│   ├── ingestion-service/        # PDF/TXT processing
│   ├── embedding-service/        # BGE-M3 embeddings
│   ├── reranker-service/         # Cross-encoder reranking
│   ├── retrieval-service/        # RAG orchestration
│   ├── chat-service/             # Streaming chat
│   └── worker-service/           # Celery workers
│
├── frontend/                     # Next.js 14 frontend
│   ├── src/
│   │   ├── app/                  # App Router pages
│   │   ├── components/           # React components
│   │   ├── lib/                  # API clients, stores, hooks
│   │   └── types/                # TypeScript types
│   └── Dockerfile
│
├── k8s/                          # Kubernetes manifests
│   ├── deployments/              # Service deployments
│   ├── statefulsets/             # Postgres, Redis
│   ├── services/                 # K8s services
│   ├── ingress/                  # Ingress rules
│   └── monitoring/               # Prometheus, Grafana
│
├── docker-compose.yml            # Local development
└── Makefile                      # Common commands
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose**
- **Python 3.11+**
- **Node.js 20+**
- **NVIDIA GPU** (optional for local dev, required for production)
- **Pinecone account** (free tier available)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/enterprise-rag-system.git
cd enterprise-rag-system
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add:
# - PINECONE_API_KEY
# - JWT_SECRET
# Other variables have sensible defaults
```

### 3. Start Services (Local Development)

```bash
# Using Makefile
make dev

# Or directly with Docker Compose
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- All backend services
- Frontend (port 3000)
- Prometheus (port 9090)
- Grafana (port 3001)

### 4. Run Database Migrations

```bash
make migrate
```

### 5. Download Models (First Time)

```bash
make download-models
```

This downloads:
- BGE-M3 embeddings (~2GB)
- BGE-reranker-v2-m3 (~1GB)
- Llama 3.1-8B-Instruct (~16GB)

### 6. Access Application

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Grafana:** http://localhost:3001 (admin/admin)
- **Prometheus:** http://localhost:9090

---

## 📚 Documentation

Comprehensive design documentation is available in `/docs/desing-docs/`:

### Backend

1. **[Architecture](docs/desing-docs/backend/architecture.md)** - Microservices design, service breakdown, database schemas
2. **[Data Flow](docs/desing-docs/backend/data-flow.md)** - Document ingestion, RAG pipeline, streaming patterns
3. **[Deployment](docs/desing-docs/backend/deployment.md)** - Docker, Kubernetes, CI/CD
4. **[Observability](docs/desing-docs/backend/observability.md)** - Metrics, logging, tracing, alerting
5. **[Project Structure](docs/desing-docs/backend/project-structure.md)** - Folder organization, code structure

### GenAI

6. **[Tech Stack](docs/desing-docs/GEN-AI/tech-stack.md)** - Model selection, inference serving, RAG framework

### Frontend

7. **[Frontend Stack](docs/desing-docs/UI/frontend-stack.md)** - Next.js, streaming UI, state management

---

## 🔧 Development

### Available Commands

```bash
# Start development environment
make dev

# View logs
make dev-logs

# Run tests
make test

# Run linters
make lint

# Build Docker images
make build

# Run migrations
make migrate

# Seed test data
make seed

# Health check
make health-check

# Clean up
make clean
```

### Running Tests

```bash
# Unit tests
pytest services/*/tests/ -v

# Integration tests
make test-integration

# E2E tests
make test-e2e

# Load tests
cd tests/load && locust
```

---

## 🐳 Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Next.js web app |
| api-gateway | 8000 | API entry point |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache & broker |
| embedding-service | - | BGE-M3 embeddings (internal) |
| llm-service | 8001 | vLLM inference server |
| worker | - | Celery worker |
| prometheus | 9090 | Metrics collection |
| grafana | 3001 | Dashboards |

---

## ☸️ Kubernetes Deployment

### Deploy to Kubernetes

```bash
# Apply base configuration
kubectl apply -f k8s/base/

# Deploy services
kubectl apply -f k8s/deployments/

# Deploy stateful sets (Postgres, Redis)
kubectl apply -f k8s/statefulsets/

# Create ingress
kubectl apply -f k8s/ingress/
```

### Scale Services

```bash
# Scale API Gateway
kubectl scale deployment api-gateway --replicas=5

# Scale workers
kubectl scale deployment worker-service --replicas=10
```

### GPU Scheduling

GPU workloads automatically schedule on GPU-enabled nodes:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

---

## 📊 Observability

### Metrics

Access Grafana dashboards at http://localhost:3001:

- **Overview Dashboard** - Request rate, errors, latency
- **RAG Pipeline** - Retrieval latency, LLM throughput
- **GPU Monitoring** - GPU utilization, memory

### Logging

Structured JSON logs with correlation IDs:

```bash
# View logs
docker-compose logs -f chat-service

# Search logs
docker-compose logs | grep correlation_id=abc123
```

### Tracing

OpenTelemetry traces exported to Jaeger:

- Each RAG query traced end-to-end
- Spans for embedding, retrieval, reranking, generation

---

## 🔐 Security

### Authentication

- JWT-based authentication
- Token expiration (24 hours)
- Refresh token support

### Multi-Tenant Isolation

- User-scoped vector search (Pinecone filters)
- Database-level user_id filtering
- No cross-user data leakage

### Input Validation

- File type validation (PDF, TXT only)
- File size limits (50MB)
- Query length limits
- Pydantic schema validation

---

## 📈 Scaling Considerations

### Horizontal Scaling

- **Stateless services** - Scale with HPA based on CPU/memory
- **Embedding service** - Add GPU nodes
- **LLM service** - Increase replicas (requires GPUs)
- **Workers** - Scale based on queue depth

### Vertical Scaling

- **LLM inference** - Use larger GPUs (A100, H100)
- **Database** - Increase connection pool
- **Redis** - Use Redis Cluster

### Cost Optimization

- Use 4-bit quantization for LLM (5GB VRAM vs 16GB)
- Cache embeddings in Redis (TTL: 1 hour)
- Batch document processing overnight
- Use spot instances for workers

---

## 🛠️ Troubleshooting

### Common Issues

**LLM service not starting:**
```bash
# Check GPU availability
nvidia-smi

# Check model download
docker-compose exec llm-service ls /models
```

**Slow embedding generation:**
```bash
# Check GPU utilization
docker-compose exec embedding-service nvidia-smi

# Increase batch size in config
```

**Pinecone connection errors:**
```bash
# Verify API key
echo $PINECONE_API_KEY

# Test connection
python scripts/test_pinecone.py
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

### Open Source Models

- **Meta AI** - Llama 3.1 (best 8B model for RAG)
- **BAAI** - BGE-M3 & BGE-reranker-v2-m3 (SOTA retrieval)
- **vLLM Team** - High-performance LLM serving

### Technologies

- FastAPI, Next.js, PostgreSQL, Redis, Pinecone
- Docker, Kubernetes, Prometheus, Grafana
- LangChain, OpenTelemetry, LangFuse

---

## 📬 Contact

- **Documentation:** See `/docs/desing-docs/`
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

---

**Built with ❤️ for production GenAI systems**
