# Phase 1: Project Scaffolding

**Goal:** Create the complete project structure, configuration files, and foundational setup.

**Duration:** 2-3 hours

**Dependencies:** Environment setup complete

---

## 📋 Phase Objectives

By the end of this phase, you will have:

- ✅ Complete folder structure
- ✅ `.env` and `.env.example` files
- ✅ `docker-compose.yml` for infrastructure
- ✅ `Makefile` with common commands
- ✅ `.gitignore` properly configured
- ✅ `requirements.txt` for backend
- ✅ `package.json` for frontend
- ✅ Basic README updates

---

## 📂 Step 1: Create Folder Structure

### Execute these commands:

```bash
# Ensure you're in project root
cd /Users/JMM9/Documents/projects/ai_specifics/enterprise-rag-system

# Backend structure
mkdir -p backend/app/{models,schemas,routes,services,utils}
mkdir -p backend/workers
mkdir -p backend/migrations

# ML services
mkdir -p ml-services/embedding-service/app
mkdir -p ml-services/reranker-service/app
mkdir -p ml-services/llm-service

# Frontend structure
mkdir -p frontend/src/{app,components,lib}
mkdir -p frontend/src/components/{chat,documents}
mkdir -p frontend/src/lib/api
mkdir -p frontend/public

# Data directories (gitignored)
mkdir -p data/uploads
mkdir -p data/models

# Scripts
mkdir -p scripts

# Verify structure
tree -L 3 -I 'node_modules|venv|__pycache__|.next'
```

---

## 📝 Step 2: Create `.env.example`

Create `.env.example` at project root:

```bash
# ===================================
# DATABASE
# ===================================
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/enterprise_rag
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ===================================
# REDIS
# ===================================
REDIS_URL=redis://redis:6379/0

# ===================================
# PINECONE (REQUIRED - Get from pinecone.io)
# ===================================
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=enterprise-rag

# ===================================
# STORAGE
# ===================================
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE_MB=50
MODEL_CACHE_DIR=./data/models

# ===================================
# ML MODELS
# ===================================
EMBEDDING_MODEL_NAME=BAAI/bge-m3
# Use this same embedding model for both:
# - document chunk embeddings stored in the vector DB
# - query embeddings used during retrieval
RERANKER_MODEL_NAME=BAAI/bge-reranker-v2-m3
# LOCAL MAC: Ollama model name (no GPU required)
LLM_MODEL_NAME=llama3.1:8b

# ===================================
# ML SERVICE URLS (Docker Compose)
# ===================================
EMBEDDING_SERVICE_URL=http://embedding-service:8001
RERANKER_SERVICE_URL=http://reranker-service:8002
# LOCAL MAC: Ollama runs on the host, not in Docker
# When calling from Docker containers use host.docker.internal
# When running backend locally use localhost
LLM_SERVICE_URL=http://localhost:11434/v1

# ===================================
# RAG CONFIGURATION
# ===================================
RETRIEVAL_TOP_K=50
RERANK_TOP_K=5
MAX_CONTEXT_TOKENS=2048
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=512

# ===================================
# APPLICATION
# ===================================
ENVIRONMENT=development
LOG_LEVEL=INFO
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# ===================================
# FRONTEND
# ===================================
NEXT_PUBLIC_API_URL=http://localhost:8000

# ===================================
# CELERY
# ===================================
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

**Then create actual `.env`:**
```bash
cp .env.example .env
# Edit .env and add your actual Pinecone API key
```

---

## 🐳 Step 3: Create `docker-compose.yml`

Create at project root:

```yaml
version: '3.8'

services:
  # ==========================================
  # Infrastructure Services
  # ==========================================
  
  postgres:
    image: postgres:16-alpine
    container_name: enterprise-rag-postgres
    environment:
      POSTGRES_DB: enterprise_rag
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - rag-network

  redis:
    image: redis:7-alpine
    container_name: enterprise-rag-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - rag-network

  # ==========================================
  # Backend Service
  # ==========================================
  
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: enterprise-rag-backend
    env_file:
      - .env
    volumes:
      - ./backend:/app
      - ./data/uploads:/data/uploads
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - rag-network

  # ==========================================
  # Celery Worker
  # ==========================================
  
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: enterprise-rag-worker
    env_file:
      - .env
    volumes:
      - ./backend:/app
      - ./data/uploads:/data/uploads
      - ./data/models:/data/models
    depends_on:
      - postgres
      - redis
    command: celery -A workers.celery_app worker --loglevel=info --concurrency=2
    networks:
      - rag-network

  # ==========================================
  # ML Services
  # ==========================================
  
  embedding-service:
    build:
      context: ./ml-services/embedding-service
      dockerfile: Dockerfile
    container_name: enterprise-rag-embeddings
    env_file:
      - .env
    volumes:
      - ./data/models:/data/models
    ports:
      - "8001:8001"
    # No GPU reservation needed — runs on CPU on local Mac
    networks:
      - rag-network

  reranker-service:
    build:
      context: ./ml-services/reranker-service
      dockerfile: Dockerfile
    container_name: enterprise-rag-reranker
    env_file:
      - .env
    volumes:
      - ./data/models:/data/models
    ports:
      - "8002:8002"
    networks:
      - rag-network

  # ==========================================
  # LLM Service
  # LOCAL MAC: Ollama runs natively, not in Docker.
  # Start it with: ollama serve
  # The backend calls http://host.docker.internal:11434/v1
  # or http://localhost:11434/v1 when running outside Docker.
  #
  # FUTURE GPU: Replace with vllm/vllm-openai:latest when a GPU is available.
  # ==========================================

  # llm-service is intentionally omitted from Docker Compose for local Mac dev.
  # Ollama runs as a system service on the Mac host.

  # ==========================================
  # Frontend Service
  # ==========================================
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: enterprise-rag-frontend
    env_file:
      - .env
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - rag-network

volumes:
  postgres_data:
  redis_data:

networks:
  rag-network:
    driver: bridge
```

---

## 🛠️ Step 4: Create `Makefile`

Create at project root:

```makefile
.PHONY: help install dev dev-infra dev-backend dev-worker dev-ml dev-frontend \
        stop clean logs test migrate seed

help:
	@echo "Enterprise RAG System - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install all dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            Start all services"
	@echo "  make dev-infra      Start infrastructure only (DB, Redis)"
	@echo "  make dev-backend    Start backend only"
	@echo "  make dev-worker     Start Celery worker"
	@echo "  make dev-ml         Start ML services"
	@echo "  make dev-frontend   Start frontend only"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Run database migrations"
	@echo "  make seed           Seed database with test data"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs           View all logs"
	@echo "  make stop           Stop all services"
	@echo "  make clean          Stop and remove all data"
	@echo "  make test           Run tests"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done!"

dev:
	docker compose up -d

dev-infra:
	docker compose up -d postgres redis

dev-backend:
	docker compose up -d postgres redis backend

dev-worker:
	docker compose up -d postgres redis worker

dev-ml:
	docker compose up -d embedding-service reranker-service llm-service

dev-frontend:
	docker compose up -d frontend

stop:
	docker compose down

clean:
	docker compose down -v
	@echo "Cleaned all containers and volumes"

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f worker

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python scripts/seed_data.py

test:
	docker compose exec backend pytest tests/ -v

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U postgres -d enterprise_rag

shell-redis:
	docker compose exec redis redis-cli

download-models:
	python scripts/download_models.py
```

---

## 📦 Step 5: Create `backend/requirements.txt`

Create `backend/requirements.txt`:

```txt
# FastAPI & Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
python-dotenv==1.0.0

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# Redis & Caching
redis==5.0.1
hiredis==2.3.2

# Celery
celery==5.3.6
flower==2.0.1

# Pydantic
pydantic==2.5.3
pydantic-settings==2.1.0

# PDF Processing
pypdfium2==4.26.0
python-magic==0.4.27

# Text Processing
langchain==0.1.4
langchain-community==0.0.16
tiktoken==0.5.2

# ML & Embeddings
sentence-transformers==2.3.1
torch==2.1.2
transformers==4.37.0

# Vector Database
pinecone-client==3.0.0

# HTTP Client
httpx==0.26.0
requests==2.31.0

# Utilities
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
aiofiles==23.2.1

# Logging & Observability
structlog==24.1.0
python-json-logger==2.0.7

# Development
black==24.1.1
flake8==7.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

---

## 📦 Step 6: Create `frontend/package.json`

Create `frontend/package.json`:

```json
{
  "name": "enterprise-rag-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18",
    "react-dom": "^18",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-toast": "^1.1.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.309.0",
    "tailwind-merge": "^2.2.0",
    "tailwindcss-animate": "^1.0.7",
    "zustand": "^4.5.0",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "tailwindcss": "^3.3.0",
    "eslint": "^8",
    "eslint-config-next": "14.1.0"
  }
}
```

---

## 🐳 Step 7: Create Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Default command (overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🐳 Step 8: Create Frontend Dockerfile

Create `frontend/Dockerfile.dev`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]
```

---

## 📄 Step 9: Create `.gitignore`

Create `.gitignore` at project root:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
ENV/
env/

# Node
node_modules/
.next/
out/
.npm
.eslintcache

# Environment
.env
.env.local
.env.production

# Database
*.db
*.sqlite

# Data
data/uploads/*
data/models/*
!data/uploads/.gitkeep
!data/models/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Docker
*.pid
```

---

## 📄 Step 10: Create Empty Marker Files

```bash
# Create .gitkeep files to preserve empty directories
touch data/uploads/.gitkeep
touch data/models/.gitkeep
touch backend/app/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/routes/__init__.py
touch backend/app/services/__init__.py
touch backend/app/utils/__init__.py
touch backend/workers/__init__.py
```

---

## ✅ Step 11: Verify Phase 1 Completion

### Check folder structure:

```bash
tree -L 3 -I 'node_modules|venv|__pycache__|.next|.git'
```

**Expected output:**
```
enterprise-rag-system/
├── .env
├── .env.example
├── .gitignore
├── Makefile
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   └── workers/
├── ml-services/
│   ├── embedding-service/
│   ├── reranker-service/
│   └── llm-service/
├── frontend/
│   ├── package.json
│   ├── Dockerfile.dev
│   └── src/
├── data/
│   ├── uploads/
│   └── models/
└── scripts/
```

### Test Docker Compose:

```bash
# Start infrastructure only
make dev-infra

# Check services
docker compose ps

# Should show:
# postgres - running
# redis - running

# Check logs
docker compose logs postgres
docker compose logs redis

# Stop services
make stop
```

### Verify files created:

```bash
# Check all required files exist
ls -la .env .env.example .gitignore Makefile docker-compose.yml
ls -la backend/Dockerfile backend/requirements.txt
ls -la frontend/Dockerfile.dev frontend/package.json
```

---

## 🎯 Phase 1 Checklist

- [ ] Created complete folder structure
- [ ] Created `.env` and `.env.example`
- [ ] Created `docker-compose.yml`
- [ ] Created `Makefile`
- [ ] Created `.gitignore`
- [ ] Created `backend/requirements.txt`
- [ ] Created `backend/Dockerfile`
- [ ] Created `frontend/package.json`
- [ ] Created `frontend/Dockerfile.dev`
- [ ] Created `.gitkeep` files
- [ ] Tested `docker compose up -d postgres redis`
- [ ] Verified PostgreSQL is running
- [ ] Verified Redis is running

---

## 📝 Commit Phase 1

```bash
git add .
git commit -m "feat: Phase 1 - Project scaffolding complete

- Created complete folder structure
- Setup environment configuration (.env)
- Created Docker Compose for infrastructure
- Created Makefile for development workflows
- Setup backend and frontend base configuration
- Added .gitignore and documentation"
```

---

## ➡️ Next Phase

**Phase 2: Database Setup**
- Read: `docs/implementation-plan/03-phase-02-database.md`
- Create SQLAlchemy models
- Setup Alembic migrations
- Create initial schema

---

**Phase 1 Complete! 🎉**

**Estimated Time:** 2-3 hours  
**Status:** ✅ Ready for Phase 2

