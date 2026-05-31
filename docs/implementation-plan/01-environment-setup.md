# Environment Setup Guide

## Prerequisites

Before starting implementation, ensure you have the following installed:

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.11+ | Backend development |
| **Node.js** | 20+ | Frontend development |
| **Docker** | 24+ | Containerization |
| **Docker Compose** | 2.20+ | Multi-container orchestration |
| **PostgreSQL** | 16+ | Database (via Docker) |
| **Redis** | 7+ | Cache & queue (via Docker) |
| **Git** | Latest | Version control |

### Optional (Recommended)

| Software | Purpose |
|----------|---------|
| **Make** | Build automation |
| **VS Code** | IDE with Copilot |
| **Postman** | API testing |
| **pgAdmin** | Database management |

### Hardware Requirements

| Environment | Hardware | Notes |
|-------------|----------|-------|
| **Local Mac (this project)** | Apple Silicon or Intel Mac, 16GB+ RAM | No GPU needed — all ML runs on CPU; Ollama uses Apple MPS if available |
| **Future GPU upgrade** | NVIDIA RTX 3060+ / A10G | Switch to vLLM for LLM once GPU is available |

**For this implementation:** The entire stack runs on your local Mac CPU. No GPU is required to start.

- Embedding service → BGE-M3 on CPU (slower but fully functional)
- Reranker service → BGE-reranker on CPU (fast enough)
- LLM → **Ollama** running Llama 3.1:8B locally (OpenAI-compatible API)
- Vector DB → **Pinecone** (cloud, free tier)
- All other infra (Postgres, Redis) → Docker on Mac

**GPU note:** vLLM requires a CUDA GPU and does **not** run on Mac. We use Ollama instead, which works natively on Mac and leverages Apple MPS (Metal) on Apple Silicon for faster inference than pure CPU.

---

## Installation Steps

### 1. Install Python 3.11

**macOS (Homebrew):**
```bash
brew install python@3.11
python3.11 --version
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 --version
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

### 2. Install Node.js 20

**macOS (Homebrew):**
```bash
brew install node@20
node --version
npm --version
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
```

**Windows:**
Download from [nodejs.org](https://nodejs.org/)

### 3. Install Docker & Docker Compose

**macOS:**
Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)

**Ubuntu:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Verify
docker --version
docker compose version
```

**Windows:**
Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

### 4. Install Ollama (Required — LLM runtime)

Ollama is the LLM runtime for local Mac development. It replaces vLLM which requires a GPU.

**macOS:**
```bash
brew install ollama
```

Or download from [ollama.com](https://ollama.com/download).

After install, pull the LLM model:

```bash
ollama pull llama3.1:8b
```

This downloads ~4.7 GB. It runs on CPU on all Macs and on Apple MPS (Metal GPU) on Apple Silicon, giving noticeably faster token generation on M1/M2/M3/M4.

Verify it works:

```bash
ollama run llama3.1:8b "Say hello in one sentence."
```

Verify the API is accessible:

```bash
curl http://localhost:11434/v1/models
```

Ollama exposes an OpenAI-compatible API at `http://localhost:11434/v1` — the backend client uses this endpoint directly.

---

### 5. Install Make (Optional but Recommended)

**macOS:**
```bash
xcode-select --install
```

**Ubuntu:**
```bash
sudo apt install make
```

**Windows:**
```bash
choco install make
```

---

## Development Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/enterprise-rag-system.git
cd enterprise-rag-system
```

### 2. Create Python Virtual Environment

```bash
# Create venv
python3.11 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
# OR
.\venv\Scripts\activate   # Windows

# Verify
which python
python --version  # Should show 3.11.x
```

### 3. Install Python Dependencies (Backend)

```bash
# Install base requirements
pip install --upgrade pip
pip install wheel setuptools

# Install backend requirements (we'll create this in Phase 1)
cd backend
pip install -r requirements.txt
cd ..
```

### 4. Install Node Dependencies (Frontend)

```bash
cd frontend
npm install
cd ..
```

---

## Service Configuration

### 1. Pinecone Account Setup

**Sign up for free tier:**
1. Go to [Pinecone.io](https://www.pinecone.io/)
2. Create account (free tier: 1M vectors)
3. Create API key
4. Note your environment (e.g., `us-east-1-aws`)
5. Create index:
   - **Name:** `enterprise-rag`
   - **Dimensions:** `1024`
   - **Metric:** `cosine`
   - **Pod Type:** `starter` (free)

**Save credentials:**
```bash
PINECONE_API_KEY=your-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
```

### 2. Hugging Face Token (Optional)

Some models may require HF token:

1. Go to [Hugging Face](https://huggingface.co/)
2. Sign up/login
3. Settings → Access Tokens → New Token
4. Save token:
```bash
HF_TOKEN=hf_xxxxxxxxxxxx
```

---

## Environment Variables Setup

### Create `.env` File

**Copy template:**
```bash
cp .env.example .env
```

**Edit `.env`:**
```bash
# Open in your editor
code .env  # VS Code
# OR
nano .env  # Terminal editor
```

**Minimum required variables:**
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/enterprise_rag

# Redis
REDIS_URL=redis://localhost:6379/0

# Pinecone (REQUIRED - add your credentials)
PINECONE_API_KEY=your-actual-api-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=enterprise-rag

# Storage
UPLOAD_DIR=./data/uploads
MODEL_CACHE_DIR=./data/models

# ML Services
EMBEDDING_SERVICE_URL=http://localhost:8001
RERANKER_SERVICE_URL=http://localhost:8002

# LLM — Ollama (local Mac, no GPU needed)
# Ollama exposes an OpenAI-compatible API
LLM_SERVICE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3.1:8b

# Embedding rule
# Use the same embedding model for:
# - document chunk indexing
# - query embedding during retrieval
# For this project that model is BAAI/bge-m3.

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Verify Installation

### 1. Check Python

```bash
python --version
# Output: Python 3.11.x

pip --version
# Output: pip 24.x
```

### 2. Check Node.js

```bash
node --version
# Output: v20.x.x

npm --version
# Output: 10.x.x
```

### 3. Check Docker

```bash
docker --version
# Output: Docker version 24.x.x

docker compose version
# Output: Docker Compose version 2.x.x
```

### 4. Test Docker

```bash
docker run hello-world
# Should download and run successfully
```

---

## IDE Setup (VS Code)

### Recommended Extensions

Install these VS Code extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-toolsai.jupyter",
    "github.copilot",
    "github.copilot-chat",
    "bradlc.vscode-tailwindcss",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker"
  ]
}
```

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## Test Infrastructure

### Start Database & Redis

```bash
# Create docker-compose.yml for infrastructure only
docker compose up -d postgres redis

# Check status
docker compose ps

# Check logs
docker compose logs -f postgres
```

**Expected output:**
```
enterprise-rag-postgres-1  running
enterprise-rag-redis-1     running
```

### Test PostgreSQL Connection

```bash
# Using psql
docker compose exec postgres psql -U postgres

# Should see PostgreSQL prompt:
postgres=#

# Test query
SELECT version();

# Exit
\q
```

### Test Redis Connection

```bash
# Using redis-cli
docker compose exec redis redis-cli

# Should see Redis prompt:
127.0.0.1:6379>

# Test command
PING
# Output: PONG

# Exit
exit
```

---

## Download ML Models (Optional - Can do later)

### Create Download Script

We'll create this in Phase 1, but here's a preview:

```python
# scripts/download_models.py
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel

# Download embedding model
print("Downloading BGE-M3...")
SentenceTransformer('BAAI/bge-m3', cache_folder='./data/models')

# Download reranker
print("Downloading BGE-reranker-v2-m3...")
AutoModel.from_pretrained('BAAI/bge-reranker-v2-m3', cache_dir='./data/models')

print("Models downloaded successfully!")
```

**Run:**
```bash
python scripts/download_models.py
```

**This downloads ~3GB of models** - can skip for now.

---

## Troubleshooting

### Python Virtual Environment Issues

**Problem:** `venv` activation doesn't work

**Solution:**
```bash
# Make sure you're in project root
pwd

# Remove old venv
rm -rf venv

# Create new venv
python3.11 -m venv venv

# Activate
source venv/bin/activate
```

### Docker Permission Issues (Linux)

**Problem:** `docker: permission denied`

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in
# OR restart
sudo reboot
```

### PostgreSQL Connection Refused

**Problem:** Can't connect to PostgreSQL

**Solution:**
```bash
# Check if running
docker compose ps

# Restart
docker compose restart postgres

# Check logs
docker compose logs postgres
```

### Port Already in Use

**Problem:** Port 5432 or 6379 already in use

**Solution:**
```bash
# Find process using port
lsof -i :5432  # macOS/Linux
netstat -ano | findstr :5432  # Windows

# Kill process or use different port in .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/enterprise_rag
```

### Pinecone Connection Issues

**Problem:** Can't connect to Pinecone

**Solution:**
1. Verify API key is correct in `.env`
2. Check index exists with correct dimensions (1024)
3. Check environment matches (us-east-1-aws, etc.)
4. Test connection:
```python
import pinecone
pinecone.init(api_key="your-key", environment="us-east-1-aws")
print(pinecone.list_indexes())
```

---

## Development Workflow

### Daily Workflow

```bash
# 1. Start infrastructure
docker compose up -d postgres redis

# 2. Activate Python environment
source venv/bin/activate

# 3. Start backend (once implemented)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Start frontend (in another terminal)
cd frontend
npm run dev

# 5. Start workers (in another terminal)
cd backend
celery -A workers.celery_app worker --loglevel=info
```

### Stopping Services

```bash
# Stop backend/frontend (Ctrl+C in terminal)

# Stop Docker services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

---

## Health Check Checklist

Before starting Phase 1, verify:

- [ ] Python 3.11+ installed and working
- [ ] Node.js 20+ installed and working
- [ ] Docker and Docker Compose working
- [ ] Ollama installed and `llama3.1:8b` downloaded
- [ ] Ollama API responds (`curl http://localhost:11434/v1/models`)
- [ ] PostgreSQL starts via `docker compose up -d postgres redis`
- [ ] Redis starts via `docker compose up -d postgres redis`
- [ ] Can connect to PostgreSQL
- [ ] Can connect to Redis
- [ ] `.env` file created with Pinecone credentials
- [ ] VS Code setup with recommended extensions
- [ ] Virtual environment created and activated

---

## Next Steps

Once your environment is ready:

1. ✅ Environment verified
2. → Proceed to **Phase 1: Project Scaffolding**
   - Read: `docs/implementation-plan/02-phase-01-scaffolding.md`

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Ready to code!** 🚀

