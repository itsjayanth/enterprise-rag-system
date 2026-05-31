#!/usr/bin/env zsh
set -u

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
EMBED_URL="${EMBED_URL:-http://localhost:8001}"
RERANK_URL="${RERANK_URL:-http://localhost:8002}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
QUERY="${SMOKE_QUERY:-How are incidents escalated?}"
TOP_K="${SMOKE_TOP_K:-2}"

PASS=0
FAIL=0
RETRY_COUNT="${SMOKE_RETRY_COUNT:-6}"
RETRY_DELAY_SECONDS="${SMOKE_RETRY_DELAY_SECONDS:-2}"

print_step() {
  echo ""
  echo "==> $1"
}

record_result() {
  local label="$1"
  local ok="$2"
  local detail="$3"
  if [[ "$ok" == "1" ]]; then
    echo "[PASS] $label"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $label"
    if [[ -n "$detail" ]]; then
      echo "       $detail"
    fi
    FAIL=$((FAIL + 1))
  fi
}

check_get() {
  local label="$1"
  local url="$2"
  local expect="$3"

  local response=""
  local attempt=1
  while [[ "$attempt" -le "$RETRY_COUNT" ]]; do
    response=$(curl -sS "$url" 2>/dev/null) && break
    sleep "$RETRY_DELAY_SECONDS"
    attempt=$((attempt + 1))
  done
  if [[ -z "$response" ]]; then
    record_result "$label" 0 "curl failed"
    return
  fi

  if echo "$response" | grep -q "$expect"; then
    record_result "$label" 1 ""
  else
    record_result "$label" 0 "$response"
  fi
}

post_json() {
  local label="$1"
  local url="$2"
  local data="$3"
  local expect="$4"

  local response=""
  local attempt=1
  while [[ "$attempt" -le "$RETRY_COUNT" ]]; do
    response=$(curl -sS -X POST "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null) && break
    sleep "$RETRY_DELAY_SECONDS"
    attempt=$((attempt + 1))
  done
  if [[ -z "$response" ]]; then
    record_result "$label" 0 "curl failed"
    return
  fi

  if echo "$response" | grep -q "$expect"; then
    record_result "$label" 1 ""
  else
    record_result "$label" 0 "$response"
  fi
}

print_step "Core health"
check_get "backend /health" "$BACKEND_URL/health" '"status":"healthy"'
check_get "backend /health/deep" "$BACKEND_URL/health/deep" '"checks"'
check_get "embedding /health" "$EMBED_URL/health" '"model_status":"ready"'
check_get "reranker /health" "$RERANK_URL/health" '"model_status":"ready"'

print_step "LLM reachability"
check_get "ollama /v1/models" "$OLLAMA_URL/v1/models" '"id":"llama3.1:8b"'
post_json "ollama chat completion" "$OLLAMA_URL/v1/chat/completions" '{"model":"llama3.1:8b","messages":[{"role":"user","content":"Reply with exactly: ok"}],"stream":false,"max_tokens":8}' '"choices"'

print_step "Document APIs"
DOCS_JSON=$(curl -sS "$BACKEND_URL/api/documents") || DOCS_JSON="[]"
if echo "$DOCS_JSON" | grep -q '"id"'; then
  record_result "documents list" 1 ""
else
  record_result "documents list" 0 "$DOCS_JSON"
fi

DOC_ID=$(echo "$DOCS_JSON" | python -c 'import json,sys
try:
    docs = json.loads(sys.stdin.read() or "[]")
    print(docs[0].get("id", "") if isinstance(docs, list) and docs else "")
except Exception:
    print("")')

if [[ -n "$DOC_ID" ]]; then
  check_get "documents get by id" "$BACKEND_URL/api/documents/$DOC_ID" '"id"'
else
  record_result "documents get by id" 0 "no document id found"
fi

print_step "Embedding and reranking"
post_json "embed query" "$EMBED_URL/embed/query" '{"text":"How are uploaded documents processed?"}' '"dimensions":1024'
post_json "rerank sample" "$RERANK_URL/rerank" '{"query":"What is chunking?","documents":["Chunking splits documents into smaller units.","Redis is used for caching and queueing."],"top_k":2}' '"results"'

print_step "Retrieval"
if [[ -n "$DOC_ID" ]]; then
  RETRIEVAL_PAYLOAD="{\"query\":\"$QUERY\",\"document_ids\":[\"$DOC_ID\"],\"top_k\":$TOP_K}"
else
  RETRIEVAL_PAYLOAD="{\"query\":\"$QUERY\",\"top_k\":$TOP_K}"
fi
post_json "retrieval search" "$BACKEND_URL/api/retrieval/search" "$RETRIEVAL_PAYLOAD" '"chunks"'

print_step "Summary"
echo "Passed: $PASS"
echo "Failed: $FAIL"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi

