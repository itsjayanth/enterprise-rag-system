from __future__ import annotations

import time
from typing import Any

import httpx
import structlog

from ..config import settings
from .vector_service import VectorService

logger = structlog.get_logger("app.services.retrieval")


class RetrievalService:
    def __init__(self) -> None:
        self.vector_service = VectorService()

    def retrieve(
        self,
        query: str,
        document_ids: list[str] | None = None,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("query must not be empty")

        vector_top_k = top_k or settings.retrieval_top_k

        embedding_started = time.perf_counter()
        query_embedding = self._embed_query(cleaned_query)
        embedding_seconds = time.perf_counter() - embedding_started

        vector_started = time.perf_counter()
        candidates = self.vector_service.search(
            query_embedding=query_embedding,
            top_k=vector_top_k,
            document_ids=document_ids,
        )
        vector_seconds = time.perf_counter() - vector_started

        rerank_started = time.perf_counter()
        reranked = self._rerank(cleaned_query, candidates)
        rerank_seconds = time.perf_counter() - rerank_started

        context_started = time.perf_counter()
        context, final_chunks = self._build_context(reranked)
        context_seconds = time.perf_counter() - context_started

        timings = {
            "embedding_seconds": round(embedding_seconds, 4),
            "vector_search_seconds": round(vector_seconds, 4),
            "rerank_seconds": round(rerank_seconds, 4),
            "context_build_seconds": round(context_seconds, 4),
            "total_seconds": round(time.perf_counter() - started_at, 4),
        }

        logger.info(
            "retrieval_completed",
            query_length=len(cleaned_query),
            candidates=len(candidates),
            final_chunks=len(final_chunks),
            timings=timings,
        )

        return {"context": context, "chunks": final_chunks, "timings": timings}

    @staticmethod
    def _embed_query(query: str) -> list[float]:
        response = httpx.post(
            f"{settings.embedding_service_url.rstrip('/')}/embed/query",
            json={"text": query},
            timeout=30.0,
        )
        if response.status_code != 200:
            raise ValueError(f"Embedding service returned {response.status_code}: {response.text}")

        payload = response.json()
        embedding = payload.get("embedding")
        if not embedding:
            raise ValueError("Embedding service returned an empty query embedding")
        return embedding

    @staticmethod
    def _rerank(query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not candidates:
            return []

        documents = [candidate.get("content") or "" for candidate in candidates]
        response = httpx.post(
            f"{settings.reranker_service_url.rstrip('/')}/rerank",
            json={
                "query": query,
                "documents": documents,
                "top_k": min(settings.rerank_top_k, len(documents)),
            },
            timeout=60.0,
        )
        if response.status_code != 200:
            raise ValueError(f"Reranker service returned {response.status_code}: {response.text}")

        payload = response.json()
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise ValueError("Reranker response has invalid results")

        reranked: list[dict[str, Any]] = []
        for item in results:
            index = item.get("index")
            if not isinstance(index, int) or index < 0 or index >= len(candidates):
                continue
            chunk = dict(candidates[index])
            chunk["rerank_score"] = item.get("score")
            reranked.append(chunk)

        return reranked

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        return max(1, len(text) // 4)

    def _build_context(self, chunks: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        lines: list[str] = []
        selected_chunks: list[dict[str, Any]] = []
        used_tokens = 0

        for position, chunk in enumerate(chunks, start=1):
            content = (chunk.get("content") or "").strip()
            if not content:
                continue

            source_file = chunk.get("source_file") or chunk.get("document_id") or "unknown"
            page_number = chunk.get("page_number")
            header = f"[Source {position}] Document: {source_file} | Page: {page_number or 'n/a'}"
            block = f"{header}\n{content}"
            block_tokens = self._estimate_token_count(block)

            if used_tokens + block_tokens > settings.max_context_tokens:
                break

            used_tokens += block_tokens
            lines.append(block)
            selected_chunks.append(chunk)

        return "\n\n".join(lines), selected_chunks

