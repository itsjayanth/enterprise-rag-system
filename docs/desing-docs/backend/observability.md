# Observability & Monitoring - Enterprise RAG System

## Executive Summary

This document defines the **observability strategy** for the enterprise RAG platform, covering metrics, logging, tracing, alerting, and GenAI-specific monitoring patterns.

**Pillars of Observability:**
1. **Metrics** - Quantitative performance data (Prometheus + Grafana)
2. **Logging** - Structured event logs (JSON logs + aggregation)
3. **Tracing** - Request flow tracking (OpenTelemetry)
4. **Alerting** - Proactive issue detection (Alertmanager)
5. **GenAI Observability** - LLM/RAG-specific tracking (LangFuse)

---

## 1. Metrics Architecture

### **1.1 Metrics Stack**

```
Application Metrics → Prometheus → Grafana Dashboards
                           ↓
                     Alertmanager → PagerDuty/Slack
```

### **1.2 Core Application Metrics**

```python
# shared/metrics.py

from prometheus_client import Counter, Histogram, Gauge, Info

# ============================================
# API Gateway Metrics
# ============================================

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

api_concurrent_requests = Gauge(
    'api_concurrent_requests',
    'Number of concurrent API requests'
)

# ============================================
# Document Processing Metrics
# ============================================

documents_uploaded_total = Counter(
    'documents_uploaded_total',
    'Total documents uploaded',
    ['file_type', 'status']
)

document_processing_duration = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration',
    ['file_type'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)
)

document_pages_processed = Counter(
    'document_pages_processed_total',
    'Total pages processed',
    ['file_type']
)

chunks_generated_total = Counter(
    'chunks_generated_total',
    'Total chunks generated'
)

# ============================================
# Embedding Service Metrics
# ============================================

embeddings_generated_total = Counter(
    'embeddings_generated_total',
    'Total embeddings generated',
    ['type']  # 'query' or 'document'
)

embedding_latency = Histogram(
    'embedding_latency_seconds',
    'Embedding generation latency',
    ['type', 'batch_size'],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0)
)

embedding_batch_size = Histogram(
    'embedding_batch_size',
    'Embedding batch size distribution',
    buckets=(1, 4, 8, 16, 32, 64, 128)
)

gpu_memory_usage = Gauge(
    'gpu_memory_usage_bytes',
    'GPU memory usage',
    ['device', 'service']
)

gpu_utilization = Gauge(
    'gpu_utilization_percent',
    'GPU utilization percentage',
    ['device', 'service']
)

# ============================================
# Retrieval Pipeline Metrics
# ============================================

retrieval_latency = Histogram(
    'retrieval_latency_seconds',
    'Retrieval pipeline latency by stage',
    ['stage'],  # 'embedding', 'vector_search', 'reranking', 'total'
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0)
)

vector_search_results = Histogram(
    'vector_search_results_count',
    'Number of results from vector search',
    buckets=(1, 5, 10, 20, 50, 100)
)

reranking_score_distribution = Histogram(
    'reranking_score',
    'Distribution of reranking scores',
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

# ============================================
# LLM Service Metrics
# ============================================

llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'status']
)

llm_tokens_generated = Counter(
    'llm_tokens_generated_total',
    'Total tokens generated',
    ['model']
)

llm_time_to_first_token = Histogram(
    'llm_time_to_first_token_seconds',
    'Time to first token',
    ['model'],
    buckets=(0.1, 0.2, 0.5, 1.0, 2.0, 5.0)
)

llm_generation_latency = Histogram(
    'llm_generation_latency_seconds',
    'Total generation latency',
    ['model'],
    buckets=(1, 5, 10, 20, 30, 60, 120)
)

llm_throughput = Gauge(
    'llm_throughput_tokens_per_second',
    'LLM throughput in tokens per second',
    ['model']
)

llm_queue_depth = Gauge(
    'llm_queue_depth',
    'Number of requests waiting in LLM queue'
)

# ============================================
# Chat Session Metrics
# ============================================

chat_sessions_total = Counter(
    'chat_sessions_total',
    'Total chat sessions created'
)

chat_messages_total = Counter(
    'chat_messages_total',
    'Total chat messages',
    ['role']  # 'user' or 'assistant'
)

chat_session_duration = Histogram(
    'chat_session_duration_seconds',
    'Chat session duration',
    buckets=(60, 300, 600, 1800, 3600, 7200)
)

# ============================================
# Celery Worker Metrics
# ============================================

celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']  # 'success', 'failure', 'retry'
)

celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration',
    ['task_name'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)
)

celery_queue_depth = Gauge(
    'celery_queue_depth',
    'Number of tasks in Celery queue',
    ['queue_name']
)

# ============================================
# Database Metrics
# ============================================

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

db_connection_pool_available = Gauge(
    'db_connection_pool_available',
    'Available database connections'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation']
)

# ============================================
# Cache Metrics
# ============================================

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']  # 'embedding', 'retrieval', 'llm'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate',
    ['cache_type']
)
```

### **1.3 Metrics Instrumentation Example**

```python
# services/retrieval-service/main.py

from fastapi import FastAPI
from prometheus_client import make_asgi_app
import time

app = FastAPI()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.post("/retrieve")
async def retrieve(request: RetrievalRequest):
    start_time = time.time()
    
    try:
        # Stage 1: Embedding
        with retrieval_latency.labels(stage='embedding').time():
            query_embedding = await embed_query(request.query)
        
        # Stage 2: Vector search
        with retrieval_latency.labels(stage='vector_search').time():
            candidates = await vector_search(
                query_embedding,
                user_id=request.user_id,
                top_k=50
            )
        vector_search_results.observe(len(candidates))
        
        # Stage 3: Reranking
        with retrieval_latency.labels(stage='reranking').time():
            reranked = await rerank(request.query, candidates, top_k=5)
        
        for result in reranked:
            reranking_score_distribution.observe(result.score)
        
        # Total latency
        total_latency = time.time() - start_time
        retrieval_latency.labels(stage='total').observe(total_latency)
        
        return {"results": reranked}
        
    except Exception as e:
        api_requests_total.labels(
            method='POST',
            endpoint='/retrieve',
            status='error'
        ).inc()
        raise
    finally:
        api_requests_total.labels(
            method='POST',
            endpoint='/retrieve',
            status='success'
        ).inc()
```

---

## 2. Logging Architecture

### **2.1 Structured Logging**

```python
# shared/logging_config.py

import logging
import json
import sys
from datetime import datetime
from typing import Any

class StructuredFormatter(logging.Formatter):
    """JSON structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": os.getenv("SERVICE_NAME", "unknown"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            
            # Context
            "correlation_id": getattr(record, "correlation_id", None),
            "user_id": getattr(record, "user_id", None),
            "request_id": getattr(record, "request_id", None),
            
            # Source
            "file": record.pathname,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

def setup_logging(service_name: str, level: str = "INFO"):
    """Setup structured logging for service"""
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=[handler]
    )
    
    # Set service name
    os.environ["SERVICE_NAME"] = service_name
    
    return logging.getLogger(service_name)
```

### **2.2 Logging Usage**

```python
# services/chat-service/main.py

from shared.logging_config import setup_logging

logger = setup_logging("chat-service")

@app.post("/chat/query")
async def chat_query(request: ChatQueryRequest):
    # Add context to logger
    log_extra = {
        "user_id": request.user_id,
        "session_id": request.session_id,
        "correlation_id": generate_correlation_id()
    }
    
    logger.info(
        "Processing chat query",
        extra={
            "extra": {
                **log_extra,
                "query_length": len(request.query),
                "has_document_filter": bool(request.document_ids)
            }
        }
    )
    
    try:
        # Retrieval
        logger.debug("Starting retrieval", extra={"extra": log_extra})
        retrieval_result = await retrieval_service.retrieve(...)
        
        logger.info(
            "Retrieval completed",
            extra={
                "extra": {
                    **log_extra,
                    "sources_count": len(retrieval_result.sources),
                    "top_score": retrieval_result.sources[0].score
                }
            }
        )
        
        # Generation
        logger.debug("Starting LLM generation", extra={"extra": log_extra})
        response = await llm_service.generate(...)
        
        logger.info(
            "Chat query completed",
            extra={
                "extra": {
                    **log_extra,
                    "response_length": len(response),
                    "sources_used": len(retrieval_result.sources)
                }
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Chat query failed: {str(e)}",
            exc_info=True,
            extra={"extra": log_extra}
        )
        raise
```

### **2.3 Log Aggregation**

```yaml
# k8s/logging/fluentd-config.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: monitoring
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type json
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>
    
    <filter kubernetes.**>
      @type kubernetes_metadata
    </filter>
    
    <filter kubernetes.**>
      @type parser
      key_name log
      <parse>
        @type json
      </parse>
      reserve_data true
    </filter>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.monitoring.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix k8s
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.system.buffer
        flush_mode interval
        flush_interval 5s
      </buffer>
    </match>
```

---

## 3. Distributed Tracing

### **3.1 OpenTelemetry Setup**

```python
# shared/tracing.py

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def setup_tracing(service_name: str):
    """Setup OpenTelemetry tracing"""
    
    # Initialize tracer provider
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({
                "service.name": service_name,
                "service.version": "1.0.0"
            })
        )
    )
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger"),
        agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
    )
    
    # Add span processor
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Auto-instrument libraries
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    
    return trace.get_tracer(service_name)

def instrument_fastapi(app: FastAPI, service_name: str):
    """Instrument FastAPI application"""
    FastAPIInstrumentor.instrument_app(app)
```

### **3.2 Custom Spans for RAG Pipeline**

```python
# services/chat-service/rag_pipeline.py

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def rag_pipeline(query: str, user_id: str):
    """RAG pipeline with distributed tracing"""
    
    with tracer.start_as_current_span("rag_pipeline") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("query_length", len(query))
        
        # Stage 1: Retrieval
        with tracer.start_as_current_span("retrieval") as retrieval_span:
            # Embed query
            with tracer.start_as_current_span("embed_query") as embed_span:
                embedding = await embedding_service.embed_query(query)
                embed_span.set_attribute("embedding_dim", len(embedding))
            
            # Vector search
            with tracer.start_as_current_span("vector_search") as search_span:
                candidates = await pinecone_search(embedding, user_id)
                search_span.set_attribute("candidates_count", len(candidates))
            
            # Rerank
            with tracer.start_as_current_span("rerank") as rerank_span:
                reranked = await rerank(query, candidates)
                rerank_span.set_attribute("final_count", len(reranked))
                rerank_span.set_attribute("top_score", reranked[0].score)
        
        # Stage 2: Generation
        with tracer.start_as_current_span("generation") as gen_span:
            context = prepare_context(reranked)
            gen_span.set_attribute("context_length", len(context))
            
            response = await llm_service.generate(query, context)
            gen_span.set_attribute("response_length", len(response))
        
        span.set_attribute("sources_count", len(reranked))
        
        return response, reranked
```

---

## 4. GenAI-Specific Observability

### **4.1 LangFuse Integration**

```python
# shared/langfuse_config.py

from langfuse import Langfuse

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def trace_rag_query(func):
    """Decorator to trace RAG queries in LangFuse"""
    
    @functools.wraps(func)
    async def wrapper(query: str, user_id: str, **kwargs):
        # Create trace
        trace = langfuse.trace(
            name="rag_query",
            user_id=user_id,
            metadata={
                "query": query,
                **kwargs
            }
        )
        
        try:
            # Execute function
            result = await func(query, user_id, **kwargs)
            
            # Log successful completion
            trace.update(
                output=result["response"],
                metadata={
                    "sources_count": len(result["sources"]),
                    "retrieval_latency_ms": result["metrics"]["retrieval_ms"],
                    "generation_latency_ms": result["metrics"]["generation_ms"]
                }
            )
            
            return result
            
        except Exception as e:
            trace.update(
                level="ERROR",
                status_message=str(e)
            )
            raise
    
    return wrapper
```

### **4.2 Detailed RAG Tracing**

```python
# services/chat-service/main.py

@trace_rag_query
async def process_chat_query(query: str, user_id: str):
    """Process chat query with full observability"""
    
    trace = langfuse.get_current_trace()
    
    # Retrieval span
    retrieval_span = trace.span(
        name="retrieval",
        input={"query": query}
    )
    
    # Embedding generation
    embedding_gen = retrieval_span.generation(
        name="query_embedding",
        model="BAAI/bge-m3",
        input=query,
        metadata={"prompt": f"Represent this query for retrieving: {query}"}
    )
    embedding = await embedding_service.embed_query(query)
    embedding_gen.end(output={"dimension": len(embedding)})
    
    # Vector search
    vector_search_span = retrieval_span.span(
        name="vector_search",
        input={"top_k": 50}
    )
    candidates = await pinecone_search(embedding, user_id, top_k=50)
    vector_search_span.end(
        output={"candidates_count": len(candidates)},
        metadata={
            "scores": [c.score for c in candidates[:5]]
        }
    )
    
    # Reranking
    rerank_gen = retrieval_span.generation(
        name="reranking",
        model="BAAI/bge-reranker-v2-m3",
        input={
            "query": query,
            "candidates_count": len(candidates)
        }
    )
    reranked = await rerank(query, candidates, top_k=5)
    rerank_gen.end(
        output={"final_count": len(reranked)},
        metadata={
            "scores": [r.score for r in reranked]
        }
    )
    
    retrieval_span.end()
    
    # Generation span
    generation_span = trace.span(
        name="llm_generation",
        input={"query": query, "sources_count": len(reranked)}
    )
    
    context = prepare_context(reranked)
    prompt = build_rag_prompt(query, context)
    
    llm_gen = generation_span.generation(
        name="answer_generation",
        model="meta-llama/Meta-Llama-3.1-8B-Instruct",
        input=prompt,
        metadata={
            "temperature": 0.1,
            "max_tokens": 512,
            "context_length": len(context)
        }
    )
    
    response = await llm_service.generate(prompt)
    
    llm_gen.end(
        output=response,
        usage={
            "input_tokens": estimate_tokens(prompt),
            "output_tokens": estimate_tokens(response),
            "total_tokens": estimate_tokens(prompt) + estimate_tokens(response)
        }
    )
    
    generation_span.end()
    
    # User feedback tracking
    trace.score(
        name="user_feedback",
        value=None,  # Set later when user provides feedback
        comment="Awaiting user feedback"
    )
    
    return {
        "response": response,
        "sources": reranked,
        "trace_id": trace.id
    }
```

### **4.3 Custom Metrics for RAG Quality**

```python
# services/chat-service/quality_metrics.py

from prometheus_client import Histogram, Counter

# Context quality
context_relevance_score = Histogram(
    'context_relevance_score',
    'Relevance score of retrieved context',
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

# Answer quality
answer_length_chars = Histogram(
    'answer_length_chars',
    'Length of generated answers in characters',
    buckets=(50, 100, 200, 500, 1000, 2000, 5000)
)

# User feedback
user_feedback_score = Histogram(
    'user_feedback_score',
    'User feedback scores (1-5)',
    buckets=(1, 2, 3, 4, 5)
)

user_feedback_total = Counter(
    'user_feedback_total',
    'Total user feedback received',
    ['score']
)

# Citations
citations_provided = Counter(
    'citations_provided_total',
    'Total citations provided in answers'
)

# Hallucination detection (if implemented)
hallucination_detected = Counter(
    'hallucination_detected_total',
    'Total hallucinations detected',
    ['detection_method']
)
```

---

## 5. Alerting Rules

### **5.1 Prometheus Alerting Rules**

```yaml
# monitoring/prometheus/alerts.yml

groups:
- name: api_alerts
  interval: 30s
  rules:
  
  # High error rate
  - alert: HighErrorRate
    expr: |
      sum(rate(api_requests_total{status="error"}[5m])) 
      / 
      sum(rate(api_requests_total[5m])) 
      > 0.05
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API error rate (>5%)"
      description: "Error rate is {{ $value | humanizePercentage }}"
  
  # Slow API response
  - alert: SlowAPIResponse
    expr: |
      histogram_quantile(0.95, 
        rate(api_request_duration_seconds_bucket[5m])
      ) > 2.0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Slow API response (p95 > 2s)"
      description: "95th percentile latency is {{ $value }}s"
  
  # LLM service down
  - alert: LLMServiceDown
    expr: up{job="llm-service"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "LLM service is down"
      description: "LLM service has been down for more than 1 minute"
  
  # High GPU memory usage
  - alert: HighGPUMemoryUsage
    expr: gpu_memory_usage_bytes / 24_000_000_000 > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High GPU memory usage (>90%)"
      description: "GPU memory usage is {{ $value | humanizePercentage }}"
  
  # Celery queue backlog
  - alert: CeleryQueueBacklog
    expr: celery_queue_depth > 100
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Large Celery queue backlog"
      description: "Queue depth is {{ $value }}"
  
  # Database connection pool exhaustion
  - alert: DatabaseConnectionPoolExhaustion
    expr: |
      db_connection_pool_available 
      / 
      db_connection_pool_size 
      < 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Database connection pool nearly exhausted"
      description: "Only {{ $value | humanizePercentage }} connections available"

- name: genai_alerts
  interval: 30s
  rules:
  
  # Slow embedding generation
  - alert: SlowEmbeddingGeneration
    expr: |
      histogram_quantile(0.95, 
        rate(embedding_latency_seconds_bucket[5m])
      ) > 1.0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Slow embedding generation (p95 > 1s)"
      description: "Embedding latency is {{ $value }}s"
  
  # Slow LLM first token
  - alert: SlowLLMFirstToken
    expr: |
      histogram_quantile(0.95, 
        rate(llm_time_to_first_token_seconds_bucket[5m])
      ) > 2.0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Slow LLM time to first token (p95 > 2s)"
  
  # Low retrieval scores
  - alert: LowRetrievalScores
    expr: |
      histogram_quantile(0.5, 
        rate(reranking_score_bucket[10m])
      ) < 0.3
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Low retrieval quality scores"
      description: "Median reranking score is {{ $value }}"
  
  # Poor user feedback
  - alert: PoorUserFeedback
    expr: |
      sum(rate(user_feedback_total{score=~"1|2"}[1h])) 
      / 
      sum(rate(user_feedback_total[1h])) 
      > 0.3
    for: 30m
    labels:
      severity: warning
    annotations:
      summary: "High rate of poor user feedback (>30%)"
```

---

## 6. Dashboards

### **6.1 Main Overview Dashboard (Grafana)**

```json
{
  "dashboard": {
    "title": "Enterprise RAG - Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "sum(rate(api_requests_total[5m])) by (endpoint)"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "sum(rate(api_requests_total{status='error'}[5m])) / sum(rate(api_requests_total[5m]))"
        }]
      },
      {
        "title": "API Latency (p50, p95, p99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "Documents Processed",
        "targets": [{
          "expr": "sum(rate(documents_uploaded_total{status='completed'}[1h]))"
        }]
      }
    ]
  }
}
```

### **6.2 RAG Pipeline Dashboard**

```json
{
  "dashboard": {
    "title": "RAG Pipeline Performance",
    "panels": [
      {
        "title": "Retrieval Pipeline Latency by Stage",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(retrieval_latency_seconds_bucket[5m])) by (stage)"
        }]
      },
      {
        "title": "LLM Throughput (tokens/sec)",
        "targets": [{
          "expr": "rate(llm_tokens_generated_total[1m])"
        }]
      },
      {
        "title": "Embedding Batch Size",
        "targets": [{
          "expr": "histogram_quantile(0.50, rate(embedding_batch_size_bucket[5m]))"
        }]
      },
      {
        "title": "Reranking Score Distribution",
        "targets": [{
          "expr": "histogram_quantile(0.50, rate(reranking_score_bucket[10m]))"
        }]
      },
      {
        "title": "Context Quality Scores",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(context_relevance_score_bucket[10m]))"
        }]
      }
    ]
  }
}
```

### **6.3 GPU Monitoring Dashboard**

```json
{
  "dashboard": {
    "title": "GPU Resource Monitoring",
    "panels": [
      {
        "title": "GPU Utilization by Service",
        "targets": [{
          "expr": "gpu_utilization_percent"
        }]
      },
      {
        "title": "GPU Memory Usage (GB)",
        "targets": [{
          "expr": "gpu_memory_usage_bytes / 1024 / 1024 / 1024"
        }]
      },
      {
        "title": "Embedding Service Throughput",
        "targets": [{
          "expr": "rate(embeddings_generated_total[1m])"
        }]
      },
      {
        "title": "LLM Queue Depth",
        "targets": [{
          "expr": "llm_queue_depth"
        }]
      }
    ]
  }
}
```

---

## 7. Cost Monitoring

### **7.1 Token Usage Tracking**

```python
# shared/cost_tracking.py

from prometheus_client import Counter, Gauge

# Token usage
tokens_processed_total = Counter(
    'tokens_processed_total',
    'Total tokens processed',
    ['model', 'type']  # type: 'input' or 'output'
)

# Estimated costs (if using paid APIs like Pinecone)
pinecone_read_units = Counter(
    'pinecone_read_units_total',
    'Total Pinecone read units consumed'
)

pinecone_write_units = Counter(
    'pinecone_write_units_total',
    'Total Pinecone write units consumed'
)

# Resource usage
gpu_hours_used = Counter(
    'gpu_hours_used_total',
    'Total GPU hours used',
    ['gpu_type', 'service']
)

# Track per-user costs
user_token_usage = Counter(
    'user_token_usage_total',
    'Token usage per user',
    ['user_id', 'model']
)
```

---

## Summary

This observability architecture provides:

- ✅ **Comprehensive metrics** with Prometheus (50+ custom metrics)
- ✅ **Structured logging** with correlation IDs
- ✅ **Distributed tracing** with OpenTelemetry
- ✅ **GenAI-specific observability** with LangFuse
- ✅ **Proactive alerting** with actionable thresholds
- ✅ **Rich dashboards** for different personas
- ✅ **Cost tracking** for resource optimization
- ✅ **Quality metrics** for RAG performance

**Key Observability Targets:**
- API p95 latency < 2s
- LLM time-to-first-token < 500ms
- Retrieval latency < 500ms
- Error rate < 1%
- GPU utilization 70-90%

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Owner:** Platform Engineering Team

