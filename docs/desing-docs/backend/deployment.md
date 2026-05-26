# Deployment Architecture - Enterprise RAG System

## Executive Summary

This document defines the **deployment architecture** for the enterprise RAG platform, covering Docker containerization, Kubernetes orchestration, local development setup, and production best practices.

---

## 1. Deployment Environments

### **1.1 Environment Overview**

| Environment | Purpose | Infrastructure | Scale |
|-------------|---------|----------------|-------|
| **Local** | Development | Docker Compose | Single machine |
| **Staging** | Testing | Kubernetes (single node) | 1 node + GPU |
| **Production** | Live traffic | Kubernetes (multi-node) | 3+ nodes + GPU pool |

---

## 2. Docker Architecture

### **2.1 Container Images**

```
enterprise-rag-system/
├── services/
│   ├── api-gateway/
│   │   └── Dockerfile
│   ├── user-service/
│   │   └── Dockerfile
│   ├── document-service/
│   │   └── Dockerfile
│   ├── ingestion-service/
│   │   └── Dockerfile
│   ├── embedding-service/
│   │   └── Dockerfile
│   ├── retrieval-service/
│   │   └── Dockerfile
│   ├── reranker-service/
│   │   └── Dockerfile
│   ├── chat-service/
│   │   └── Dockerfile
│   └── worker-service/
│       └── Dockerfile
└── frontend/
    └── Dockerfile
```

### **2.2 Multi-Stage Dockerfile Example**

```dockerfile
# services/embedding-service/Dockerfile

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Add to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **2.3 GPU-Enabled Dockerfile**

```dockerfile
# services/llm-service/Dockerfile (vLLM)

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install Python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install vLLM
RUN pip install --no-cache-dir vllm==0.4.0

# Download model at build time (optional, or use init container)
# ENV HF_HOME=/models
# RUN python -c "from vllm import LLM; LLM('meta-llama/Meta-Llama-3.1-8B-Instruct')"

EXPOSE 8000

CMD ["vllm", "serve", \
     "meta-llama/Meta-Llama-3.1-8B-Instruct", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--dtype", "float16", \
     "--max-model-len", "8192"]
```

### **2.4 Frontend Dockerfile (Next.js)**

```dockerfile
# frontend/Dockerfile

# Stage 1: Dependencies
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --only=production

# Stage 2: Builder
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

---

## 3. Docker Compose (Local Development)

### **3.1 Full Stack docker-compose.yml**

```yaml
version: '3.8'

services:
  # ============================================
  # Infrastructure Services
  # ============================================
  
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: enterprise_rag
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
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

  # ============================================
  # Backend Services
  # ============================================

  api-gateway:
    build:
      context: ./services/api-gateway
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/enterprise_rag
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=your-secret-key-change-in-prod
      - ENVIRONMENT=development
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./services/api-gateway:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  document-service:
    build:
      context: ./services/document-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/enterprise_rag
      - REDIS_URL=redis://redis:6379/0
      - UPLOAD_DIR=/data/uploads
    depends_on:
      - postgres
      - redis
    volumes:
      - ./services/document-service:/app
      - uploads_data:/data/uploads
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  ingestion-service:
    build:
      context: ./services/ingestion-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/enterprise_rag
      - REDIS_URL=redis://redis:6379/0
      - UPLOAD_DIR=/data/uploads
    depends_on:
      - postgres
      - redis
    volumes:
      - ./services/ingestion-service:/app
      - uploads_data:/data/uploads
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  embedding-service:
    build:
      context: ./services/embedding-service
      dockerfile: Dockerfile
    environment:
      - MODEL_NAME=BAAI/bge-m3
      - MODEL_CACHE_DIR=/models
      - DEVICE=cuda  # Use 'cpu' if no GPU
    volumes:
      - ./services/embedding-service:/app
      - models_cache:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  reranker-service:
    build:
      context: ./services/reranker-service
      dockerfile: Dockerfile
    environment:
      - MODEL_NAME=BAAI/bge-reranker-v2-m3
      - MODEL_CACHE_DIR=/models
      - DEVICE=cuda
    volumes:
      - ./services/reranker-service:/app
      - models_cache:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  retrieval-service:
    build:
      context: ./services/retrieval-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/enterprise_rag
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_ENVIRONMENT=${PINECONE_ENVIRONMENT}
      - PINECONE_INDEX_NAME=enterprise-rag-vectors
      - EMBEDDING_SERVICE_URL=http://embedding-service:8000
      - RERANKER_SERVICE_URL=http://reranker-service:8000
    depends_on:
      - postgres
      - embedding-service
      - reranker-service
    volumes:
      - ./services/retrieval-service:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  llm-service:
    image: vllm/vllm-openai:latest
    environment:
      - HF_HOME=/models
    volumes:
      - models_cache:/models
    command:
      - --model=meta-llama/Meta-Llama-3.1-8B-Instruct
      - --dtype=float16
      - --max-model-len=8192
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "8001:8000"

  chat-service:
    build:
      context: ./services/chat-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/enterprise_rag
      - REDIS_URL=redis://redis:6379/0
      - RETRIEVAL_SERVICE_URL=http://retrieval-service:8000
      - LLM_SERVICE_URL=http://llm-service:8000
    depends_on:
      - postgres
      - redis
      - retrieval-service
      - llm-service
    volumes:
      - ./services/chat-service:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  worker-service:
    build:
      context: ./services/worker-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/enterprise_rag
      - REDIS_URL=redis://redis:6379/0
      - UPLOAD_DIR=/data/uploads
      - EMBEDDING_SERVICE_URL=http://embedding-service:8000
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_ENVIRONMENT=${PINECONE_ENVIRONMENT}
    depends_on:
      - postgres
      - redis
      - embedding-service
    volumes:
      - ./services/worker-service:/app
      - uploads_data:/data/uploads
    command: celery -A tasks worker --loglevel=info --concurrency=4

  # ============================================
  # Frontend
  # ============================================

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

  # ============================================
  # Monitoring (Optional for local)
  # ============================================

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

volumes:
  postgres_data:
  redis_data:
  uploads_data:
  models_cache:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: enterprise-rag-network
```

### **3.2 Environment Variables (.env)**

```bash
# .env file for local development

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/enterprise_rag

# Redis
REDIS_URL=redis://localhost:6379/0

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=enterprise-rag-vectors

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Storage
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_SIZE_MB=50

# Models
MODEL_CACHE_DIR=/models

# Services
EMBEDDING_SERVICE_URL=http://embedding-service:8000
RERANKER_SERVICE_URL=http://reranker-service:8000
LLM_SERVICE_URL=http://llm-service:8000
RETRIEVAL_SERVICE_URL=http://retrieval-service:8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### **3.3 Local Development Commands**

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api-gateway

# View logs
docker-compose logs -f chat-service

# Rebuild after code changes
docker-compose up -d --build embedding-service

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Scale workers
docker-compose up -d --scale worker-service=3

# Run migrations
docker-compose exec postgres psql -U postgres -d enterprise_rag -f /migrations/001_initial.sql
```

---

## 4. Kubernetes Architecture

### **4.1 Cluster Architecture**

```
┌────────────────────────────────────────────────────────┐
│                   KUBERNETES CLUSTER                    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Namespace: production                │ │
│  │                                                   │ │
│  │  ┌─────────────┐  ┌─────────────┐               │ │
│  │  │   Ingress   │  │   Ingress   │               │ │
│  │  │  Controller │  │   (NGINX)   │               │ │
│  │  └──────┬──────┘  └──────┬──────┘               │ │
│  │         │                 │                       │ │
│  │         └────────┬────────┘                       │ │
│  │                  │                                 │ │
│  │         ┌────────▼─────────┐                      │ │
│  │         │   API Gateway    │                      │ │
│  │         │   (3 replicas)   │                      │ │
│  │         └────────┬─────────┘                      │ │
│  │                  │                                 │ │
│  │    ┌─────────────┼─────────────┐                 │ │
│  │    │             │             │                  │ │
│  │  ┌─▼──────┐  ┌──▼─────┐  ┌───▼────┐             │ │
│  │  │  User  │  │  Doc   │  │  Chat  │             │ │
│  │  │Service │  │Service │  │Service │             │ │
│  │  └────────┘  └────────┘  └────────┘             │ │
│  │                                                   │ │
│  │  ┌─────────────────────────────────────────┐    │ │
│  │  │       Processing Layer                   │    │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌────────┐ │    │ │
│  │  │  │Ingestion │  │Retrieval │  │Worker  │ │    │ │
│  │  │  └──────────┘  └──────────┘  └────────┘ │    │ │
│  │  └─────────────────────────────────────────┘    │ │
│  │                                                   │ │
│  │  ┌─────────────────────────────────────────┐    │ │
│  │  │       GPU Node Pool                      │    │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌────────┐ │    │ │
│  │  │  │Embedding │  │Reranker  │  │  LLM   │ │    │ │
│  │  │  │  (T4)    │  │  (T4)    │  │ (A10G) │ │    │ │
│  │  │  └──────────┘  └──────────┘  └────────┘ │    │ │
│  │  └─────────────────────────────────────────┘    │ │
│  │                                                   │ │
│  │  ┌─────────────────────────────────────────┐    │ │
│  │  │       Data Layer                         │    │ │
│  │  │  ┌──────────┐  ┌──────┐  ┌───────────┐  │    │ │
│  │  │  │PostgreSQL│  │Redis │  │ PVC       │  │    │ │
│  │  │  │(StatefulS│  │      │  │(uploads)  │  │    │ │
│  │  │  │et)       │  │      │  │           │  │    │ │
│  │  │  └──────────┘  └──────┘  └───────────┘  │    │ │
│  │  └─────────────────────────────────────────┘    │ │
│  └───────────────────────────────────────────────── │ │
└────────────────────────────────────────────────────────┘
```

### **4.2 Namespace Structure**

```yaml
# namespaces.yaml

apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    environment: staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    environment: shared
```

### **4.3 ConfigMaps & Secrets**

```yaml
# k8s/base/configmap.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  UPLOAD_DIR: "/data/uploads"
  MAX_UPLOAD_SIZE_MB: "50"
  MODEL_CACHE_DIR: "/models"
  
  # Service URLs
  EMBEDDING_SERVICE_URL: "http://embedding-service:8000"
  RERANKER_SERVICE_URL: "http://reranker-service:8000"
  LLM_SERVICE_URL: "http://llm-service:8000"
  RETRIEVAL_SERVICE_URL: "http://retrieval-service:8000"
```

```yaml
# k8s/base/secrets.yaml (use sealed-secrets or external secret manager in prod)

apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres:5432/enterprise_rag"
  REDIS_URL: "redis://:password@redis:6379/0"
  JWT_SECRET: "your-super-secret-jwt-key"
  PINECONE_API_KEY: "your-pinecone-api-key"
  PINECONE_ENVIRONMENT: "us-east-1-aws"
```

### **4.4 Deployment Example (API Gateway)**

```yaml
# k8s/deployments/api-gateway.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: production
  labels:
    app: api-gateway
    tier: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: api-gateway
        image: myregistry/api-gateway:1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: ENVIRONMENT
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: REDIS_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: production
  labels:
    app: api-gateway
spec:
  type: ClusterIP
  selector:
    app: api-gateway
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### **4.5 GPU Deployment (LLM Service)**

```yaml
# k8s/deployments/llm-service.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-service
  namespace: production
  labels:
    app: llm-service
    tier: ml
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-service
  template:
    metadata:
      labels:
        app: llm-service
    spec:
      nodeSelector:
        gpu-type: a10g  # Schedule on GPU nodes
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      
      # Init container to download model
      initContainers:
      - name: model-downloader
        image: python:3.11-slim
        command:
        - /bin/bash
        - -c
        - |
          pip install huggingface_hub
          python -c "
          from huggingface_hub import snapshot_download
          snapshot_download(
              'meta-llama/Meta-Llama-3.1-8B-Instruct',
              cache_dir='/models',
              local_dir='/models/Meta-Llama-3.1-8B-Instruct'
          )"
        volumeMounts:
        - name: models
          mountPath: /models
      
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        args:
        - --model=/models/Meta-Llama-3.1-8B-Instruct
        - --dtype=float16
        - --max-model-len=8192
        - --tensor-parallel-size=1
        - --trust-remote-code
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: HF_HOME
          value: /models
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        resources:
          requests:
            cpu: 8
            memory: 16Gi
            nvidia.com/gpu: 1
          limits:
            cpu: 16
            memory: 24Gi
            nvidia.com/gpu: 1
        volumeMounts:
        - name: models
          mountPath: /models
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 180  # Model loading takes time
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
      
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: llm-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: llm-service
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
```

### **4.6 StatefulSet (PostgreSQL)**

```yaml
# k8s/statefulsets/postgres.yaml

apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: production
spec:
  type: ClusterIP
  clusterIP: None  # Headless service
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: production
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_DB
          value: enterprise_rag
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U $POSTGRES_USER
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U $POSTGRES_USER
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: standard
      resources:
        requests:
          storage: 100Gi
```

### **4.7 PersistentVolumeClaim (File Uploads)**

```yaml
# k8s/storage/uploads-pvc.yaml

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
  namespace: production
spec:
  accessModes:
    - ReadWriteMany  # Shared across pods
  storageClassName: nfs-client  # Or appropriate storage class
  resources:
    requests:
      storage: 500Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: models-pvc
  namespace: production
spec:
  accessModes:
    - ReadOnlyMany  # Models are read-only after download
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi
```

### **4.8 Ingress**

```yaml
# k8s/ingress/ingress.yaml

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: enterprise-rag-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.enterprise-rag.com
    - app.enterprise-rag.com
    secretName: tls-secret
  rules:
  - host: api.enterprise-rag.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
  - host: app.enterprise-rag.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

---

## 5. Deployment Workflows

### **5.1 CI/CD Pipeline (GitHub Actions)**

```yaml
# .github/workflows/deploy.yml

name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
          - api-gateway
          - document-service
          - ingestion-service
          - embedding-service
          - retrieval-service
          - chat-service
          - worker-service
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=sha,prefix={{branch}}-
          type=semver,pattern={{version}}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: ./services/${{ matrix.service }}
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure Kubernetes context
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy to staging
      run: |
        kubectl apply -f k8s/namespace/staging.yaml
        kubectl apply -f k8s/configmap/ -n staging
        kubectl apply -f k8s/secrets/ -n staging
        kubectl apply -f k8s/deployments/ -n staging
        kubectl rollout status deployment/api-gateway -n staging

  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure Kubernetes context
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG_PROD }}
    
    - name: Deploy to production
      run: |
        kubectl apply -f k8s/namespace/production.yaml
        kubectl apply -f k8s/configmap/ -n production
        kubectl apply -f k8s/secrets/ -n production
        kubectl apply -f k8s/deployments/ -n production
        kubectl rollout status deployment/api-gateway -n production
```

---

## 6. Observability Setup

```yaml
# k8s/monitoring/prometheus-config.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
```

---

## Summary

This deployment architecture provides:

- ✅ **Local development** with Docker Compose (GPU support)
- ✅ **Production-ready** Kubernetes manifests
- ✅ **Horizontal scaling** with HPA
- ✅ **GPU scheduling** for ML workloads
- ✅ **Persistent storage** for databases and files
- ✅ **CI/CD pipeline** with automated deployments
- ✅ **Health checks** and monitoring
- ✅ **Secure secrets management**

**Next:** Observability and monitoring strategy.

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** DevOps Team

