"""Phase 7 Pinecone smoke test.

Runs a query embedding request against embedding-service,
then runs Pinecone vector search via backend VectorService.

Usage:
    python scripts/phase7_vector_smoke_test.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.vector_service import VectorService  # noqa: E402


def main() -> None:
    query_text = "What does the incident response playbook say?"

    embed_response = httpx.post(
        "http://localhost:8001/embed/query",
        json={"text": query_text},
        timeout=60.0,
    )
    embed_response.raise_for_status()
    query_embedding = embed_response.json()["embedding"]

    vector_service = VectorService()
    results = vector_service.search(query_embedding=query_embedding, top_k=5)

    print(json.dumps({"result_count": len(results), "first_result": results[0] if results else None}, indent=2))


if __name__ == "__main__":
    main()

