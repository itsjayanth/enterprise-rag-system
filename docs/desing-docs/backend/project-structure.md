# Project Structure - Enterprise RAG System

## Executive Summary

This document defines the **complete folder structure** for the enterprise RAG monorepo, organized for microservices architecture with shared libraries, clear separation of concerns, and production best practices.

---

## 1. Repository Structure Overview

```
enterprise-rag-system/
├── .github/                      # GitHub Actions CI/CD
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── deploy-staging.yml
│   │   └── deploy-production.yml
│   └── CODEOWNERS
│
├── docs/                         # Documentation
│   ├── desing-docs/              # Design documents (as created)
│   │   ├── backend/
│   │   │   ├── architecture.md
│   │   │   ├── data-flow.md
│   │   │   ├── deployment.md
│   │   │   ├── observability.md
│   │   │   └── project-structure.md
│   │   ├── GEN-AI/
│   │   │   └── tech-stack.md
│   │   └── UI/
│   │       └── frontend-stack.md
│   ├── api/                      # API documentation
│   │   ├── openapi.yaml
│   │   └── postman-collection.json
│   ├── test-data/                # Small committed development datasets and expected outputs
│   │   └── README.md
│   └── runbooks/                 # Operational runbooks
│       ├── deployment.md
│       ├── incident-response.md
│       └── troubleshooting.md
│
├── services/                     # Microservices
│   ├── shared/                   # Shared libraries
│   │   ├── __init__.py
│   │   ├── auth/                 # Authentication utilities
│   │   │   ├── __init__.py
│   │   │   ├── jwt_handler.py
│   │   │   └── middleware.py
│   │   ├── database/             # Database utilities
│   │   │   ├── __init__.py
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   ├── session.py        # DB session management
│   │   │   └── migrations/       # Alembic migrations
│   │   ├── logging/              # Logging configuration
│   │   │   ├── __init__.py
│   │   │   └── structured.py
│   │   ├── metrics/              # Prometheus metrics
│   │   │   ├── __init__.py
│   │   │   └── custom_metrics.py
│   │   ├── tracing/              # OpenTelemetry
│   │   │   ├── __init__.py
│   │   │   └── setup.py
│   │   ├── schemas/              # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── chat.py
│   │   │   └── retrieval.py
│   │   └── utils/                # Common utilities
│   │       ├── __init__.py
│   │       ├── text_processing.py
│   │       ├── file_validation.py
│   │       └── error_handlers.py
│   │
│   ├── api-gateway/              # API Gateway Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   └── chat.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth_middleware.py
│   │   │   ├── rate_limiter.py
│   │   │   └── cors.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_routes.py
│   │       └── test_middleware.py
│   │
│   ├── user-service/             # User Management Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   └── user_service.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── users.py
│   │   └── tests/
│   │
│   ├── document-service/         # Document Upload/Management
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── document.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── upload_service.py
│   │   │   ├── validation_service.py
│   │   │   └── storage_service.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── documents.py
│   │   └── tests/
│   │
│   ├── ingestion-service/        # Document Processing
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── txt_parser.py
│   │   │   └── base_parser.py
│   │   ├── chunking/
│   │   │   ├── __init__.py
│   │   │   ├── recursive_splitter.py
│   │   │   ├── semantic_splitter.py
│   │   │   └── metadata_extractor.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── ingestion_service.py
│   │   └── tests/
│   │
│   ├── embedding-service/        # Embedding Generation
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── model_loader.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── embedding_service.py
│   │   │   └── batch_processor.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── embeddings.py
│   │   └── tests/
│   │
│   ├── reranker-service/         # Reranking Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── reranker_model.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── reranker_service.py
│   │   └── tests/
│   │
│   ├── retrieval-service/        # RAG Retrieval Orchestration
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── retrieval_service.py
│   │   │   ├── pinecone_client.py
│   │   │   └── context_builder.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── retrieval.py
│   │   └── tests/
│   │
│   ├── chat-service/             # Chat/Streaming Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── chat_session.py
│   │   │   └── message.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── chat_service.py
│   │   │   ├── rag_pipeline.py
│   │   │   ├── prompt_builder.py
│   │   │   └── llm_client.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── chat.py
│   │   └── tests/
│   │
│   └── worker-service/           # Celery Workers
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── celery_app.py
│       ├── config.py
│       ├── tasks/
│       │   ├── __init__.py
│       │   ├── document_tasks.py
│       │   ├── embedding_tasks.py
│       │   └── batch_tasks.py
│       └── tests/
│
├── frontend/                     # Next.js Frontend
│   ├── .next/
│   ├── public/
│   │   ├── favicon.ico
│   │   └── assets/
│   ├── src/
│   │   ├── app/                  # Next.js 14 App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── chat/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [sessionId]/
│   │   │   │       └── page.tsx
│   │   │   └── documents/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   └── ...
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   ├── StreamingMessage.tsx
│   │   │   │   └── SourceCard.tsx
│   │   │   ├── documents/
│   │   │   │   ├── DocumentUpload.tsx
│   │   │   │   ├── DocumentList.tsx
│   │   │   │   └── DocumentCard.tsx
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── Footer.tsx
│   │   ├── lib/
│   │   │   ├── api/              # API client
│   │   │   │   ├── client.ts
│   │   │   │   ├── auth.ts
│   │   │   │   ├── documents.ts
│   │   │   │   └── chat.ts
│   │   │   ├── hooks/            # Custom React hooks
│   │   │   │   ├── useAuth.ts
│   │   │   │   ├── useChat.ts
│   │   │   │   └── useDocuments.ts
│   │   │   ├── stores/           # Zustand state management
│   │   │   │   ├── authStore.ts
│   │   │   │   ├── chatStore.ts
│   │   │   │   └── documentStore.ts
│   │   │   └── utils/
│   │   │       ├── cn.ts
│   │   │       └── formatters.ts
│   │   ├── styles/
│   │   │   └── globals.css
│   │   └── types/
│   │       ├── api.ts
│   │       ├── chat.ts
│   │       └── document.ts
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── .env.local
│
├── k8s/                          # Kubernetes manifests
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   └── secrets.yaml
│   ├── deployments/
│   │   ├── api-gateway.yaml
│   │   ├── document-service.yaml
│   │   ├── ingestion-service.yaml
│   │   ├── embedding-service.yaml
│   │   ├── reranker-service.yaml
│   │   ├── retrieval-service.yaml
│   │   ├── chat-service.yaml
│   │   ├── worker-service.yaml
│   │   └── frontend.yaml
│   ├── statefulsets/
│   │   ├── postgres.yaml
│   │   └── redis.yaml
│   ├── services/
│   │   ├── api-gateway-svc.yaml
│   │   ├── postgres-svc.yaml
│   │   └── ...
│   ├── storage/
│   │   ├── uploads-pvc.yaml
│   │   └── models-pvc.yaml
│   ├── ingress/
│   │   └── ingress.yaml
│   ├── hpa/
│   │   ├── api-gateway-hpa.yaml
│   │   └── ...
│   └── monitoring/
│       ├── prometheus.yaml
│       ├── grafana.yaml
│       └── jaeger.yaml
│
├── scripts/                      # Utility scripts
│   ├── setup/
│   │   ├── install_dependencies.sh
│   │   ├── download_models.py
│   │   └── init_database.sh
│   ├── development/
│   │   ├── run_local.sh
│   │   ├── seed_data.py
│   │   └── test_pipeline.py
│   ├── deployment/
│   │   ├── build_images.sh
│   │   ├── deploy_k8s.sh
│   │   └── rollback.sh
│   └── monitoring/
│       ├── check_health.py
│       └── generate_report.py
│
├── migrations/                   # Database migrations
│   ├── versions/
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_add_chat_sessions.sql
│   │   └── ...
│   └── alembic.ini
│
├── tests/                        # Integration & E2E tests
│   ├── integration/
│   │   ├── test_document_flow.py
│   │   ├── test_chat_flow.py
│   │   └── test_retrieval.py
│   ├── e2e/
│   │   ├── test_user_journey.py
│   │   └── test_upload_chat.py
│   ├── load/
│   │   ├── locustfile.py         # Load testing with Locust
│   │   └── k6_script.js          # Load testing with k6
│   └── fixtures/
│       ├── sample_documents/
│       └── test_data.json
│
├── monitoring/                   # Monitoring configs
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── overview.json
│   │   │   ├── rag-pipeline.json
│   │   │   └── gpu-monitoring.json
│   │   └── provisioning/
│   └── langfuse/
│       └── config.yaml
│
├── data/                         # Local development data
│   ├── uploads/                  # Uploaded documents (gitignored)
│   └── models/                   # Downloaded models (gitignored)
│
├── .env.example                  # Example environment variables
├── .gitignore
├── docker-compose.yml            # Local development
├── docker-compose.prod.yml       # Production-like local
├── Makefile                      # Common commands
├── README.md
├── LICENSE
└── pyproject.toml                # Python project config

```

---

## 2. Detailed Service Structure

### **2.1 Shared Library (`services/shared/`)**

**Purpose:** Reusable code across all services

```python
# services/shared/database/models.py

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    status = Column(String(50), default='pending')
    total_pages = Column(Integer)
    total_chunks = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    char_count = Column(Integer)
    token_count = Column(Integer)
    embedding_id = Column(String(255))
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON)
    token_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

```python
# services/shared/schemas/document.py

from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, List

class DocumentBase(BaseModel):
    filename: str
    file_type: str

class DocumentCreate(DocumentBase):
    user_id: UUID4
    file_size: int
    storage_path: str

class DocumentResponse(DocumentBase):
    id: UUID4
    user_id: UUID4
    file_size: int
    status: str
    total_pages: Optional[int]
    total_chunks: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChunkResponse(BaseModel):
    id: UUID4
    document_id: UUID4
    chunk_index: int
    content: str
    page_number: Optional[int]
    
    class Config:
        from_attributes = True
```

### **2.2 Service Structure Example (`chat-service/`)**

```
chat-service/
├── Dockerfile
├── requirements.txt
├── main.py                      # FastAPI app entry point
├── config.py                    # Configuration management
├── models/                      # Database models (if service-specific)
│   ├── __init__.py
│   └── custom_models.py
├── services/                    # Business logic
│   ├── __init__.py
│   ├── chat_service.py          # Main chat orchestration
│   ├── rag_pipeline.py          # RAG pipeline logic
│   ├── prompt_builder.py        # Prompt construction
│   └── llm_client.py            # LLM API client
├── routes/                      # API endpoints
│   ├── __init__.py
│   └── chat.py
├── dependencies/                # FastAPI dependencies
│   ├── __init__.py
│   └── auth.py
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── test_chat_service.py
│   ├── test_rag_pipeline.py
│   └── conftest.py
└── README.md
```

**main.py:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from shared.logging import setup_logging
from shared.tracing import setup_tracing, instrument_fastapi
from config import settings
from routes import chat

# Setup observability
logger = setup_logging("chat-service")
tracer = setup_tracing("chat-service")

# Create FastAPI app
app = FastAPI(
    title="Chat Service",
    version="1.0.0",
    description="RAG-powered chat service with streaming"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument with tracing
instrument_fastapi(app, "chat-service")

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "chat-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 3. Frontend Structure Details

### **3.1 Page Structure (`frontend/src/app/`)**

```typescript
// frontend/src/app/chat/page.tsx

import { ChatInterface } from '@/components/chat/ChatInterface'
import { DocumentSelector } from '@/components/documents/DocumentSelector'
import { Suspense } from 'react'

export default function ChatPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Chat with Documents</h1>
      
      <Suspense fallback={<div>Loading...</div>}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="md:col-span-1">
            <DocumentSelector />
          </div>
          <div className="md:col-span-3">
            <ChatInterface />
          </div>
        </div>
      </Suspense>
    </div>
  )
}
```

### **3.2 API Client (`frontend/src/lib/api/`)**

```typescript
// frontend/src/lib/api/client.ts

import axios from 'axios'

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

```typescript
// frontend/src/lib/api/chat.ts

import apiClient from './client'

export interface ChatQueryRequest {
  query: string
  session_id?: string
  document_ids?: string[]
}

export interface Source {
  document_id: string
  page_number: number
  score: number
  content: string
}

export async function* streamChatQuery(
  request: ChatQueryRequest
): AsyncGenerator<{ type: string; data: any }> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/query`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
      },
      body: JSON.stringify(request),
    }
  )

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n\n')

    for (const line of lines) {
      if (!line.trim()) continue

      const [eventLine, dataLine] = line.split('\n')
      const eventType = eventLine.replace('event: ', '')
      const data = JSON.parse(dataLine.replace('data: ', ''))

      yield { type: eventType, data }
    }
  }
}
```

---

## 4. Configuration Management

### **4.1 Service Configuration (`config.py`)**

```python
# services/chat-service/config.py

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Service info
    SERVICE_NAME: str = "chat-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_TTL: int = 3600
    
    # External services
    RETRIEVAL_SERVICE_URL: str
    LLM_SERVICE_URL: str
    
    # LLM config
    LLM_MODEL: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 512
    
    # RAG config
    RETRIEVAL_TOP_K: int = 50
    RERANK_TOP_K: int = 5
    MAX_CONTEXT_LENGTH: int = 2048
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Observability
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    JAEGER_AGENT_HOST: str = "jaeger"
    JAEGER_AGENT_PORT: int = 6831
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 5. Makefile for Common Commands

```makefile
# Makefile

.PHONY: help install dev build test deploy clean

help:
	@echo "Enterprise RAG System - Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install all dependencies"
	@echo "  make dev           - Start development environment"
	@echo "  make build         - Build all Docker images"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linters"
	@echo "  make deploy-dev    - Deploy to development"
	@echo "  make deploy-prod   - Deploy to production"
	@echo "  make clean         - Clean up"

install:
	@echo "Installing dependencies..."
	cd frontend && npm install
	pip install -r requirements.txt

dev:
	@echo "Starting development environment..."
	docker-compose up -d

dev-logs:
	docker-compose logs -f

build:
	@echo "Building Docker images..."
	docker-compose build

test:
	@echo "Running tests..."
	pytest tests/ -v --cov=services --cov-report=html

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

lint:
	@echo "Running linters..."
	black services/
	flake8 services/
	mypy services/
	cd frontend && npm run lint

format:
	black services/
	cd frontend && npm run format

migrate:
	@echo "Running database migrations..."
	alembic upgrade head

seed:
	@echo "Seeding database..."
	python scripts/development/seed_data.py

deploy-staging:
	@echo "Deploying to staging..."
	./scripts/deployment/deploy_k8s.sh staging

deploy-prod:
	@echo "Deploying to production..."
	./scripts/deployment/deploy_k8s.sh production

k8s-apply:
	kubectl apply -f k8s/base/
	kubectl apply -f k8s/deployments/
	kubectl apply -f k8s/services/

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	cd frontend && rm -rf .next node_modules

download-models:
	@echo "Downloading models..."
	python scripts/setup/download_models.py

health-check:
	@echo "Checking service health..."
	python scripts/monitoring/check_health.py
```

---

## 6. Docker Compose for Development

See `deployment.md` for full docker-compose.yml

**Quick start:**
```bash
# Start all services
make dev

# View logs
make dev-logs

# Run migrations
make migrate

# Seed test data
make seed
```

---

## Summary

This project structure provides:

- ✅ **Clear separation** between services
- ✅ **Shared libraries** for code reuse
- ✅ **Production-ready** folder organization
- ✅ **Easy navigation** for developers
- ✅ **Testability** with dedicated test directories
- ✅ **Documentation** co-located with code
- ✅ **K8s-ready** deployment manifests
- ✅ **Developer experience** with Makefile shortcuts

**Key Principles:**
1. Each service is independently deployable
2. Shared code is in `services/shared/`
3. Tests are co-located with code
4. Configuration is environment-based
5. Documentation is version-controlled

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** Engineering Team

