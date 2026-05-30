from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from pinecone import Pinecone, ServerlessSpec

from ..config import settings

logger = structlog.get_logger("app.services.vector")


@dataclass(slots=True)
class ChunkVectorPayload:
    vector_id: str
    values: list[float]
    metadata: dict[str, Any]


class VectorService:
    def __init__(self) -> None:
        if not settings.pinecone_api_key or settings.pinecone_api_key.startswith("replace-with"):
            raise ValueError("PINECONE_API_KEY is not configured")

        self.client = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.dimension = settings.pinecone_index_dimension
        self.metric = settings.pinecone_metric
        self.host = settings.pinecone_host.strip()
        self.index = self.ensure_index()

    def ensure_index(self):
        indexes = self.client.list_indexes().names()

        if self.index_name not in indexes:
            region = "us-east-1"
            if settings.pinecone_environment and "-" in settings.pinecone_environment:
                region = settings.pinecone_environment.split("-")[:3]
                region = "-".join(region)

            logger.info(
                "pinecone_index_create_requested",
                index_name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                region=region,
            )
            self.client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(cloud="aws", region=region),
            )

        index = self.client.Index(self.index_name, host=self.host or None)
        stats = index.describe_index_stats()
        logger.info("pinecone_index_ready", index_name=self.index_name, stats=str(stats))
        return index

    def describe_index(self) -> dict[str, Any]:
        stats = self.index.describe_index_stats()
        return {
            "index_name": self.index_name,
            "dimension": self.dimension,
            "metric": self.metric,
            "total_vector_count": getattr(stats, "total_vector_count", None),
        }

    def upsert_chunk_embeddings(self, payloads: list[ChunkVectorPayload], batch_size: int = 100) -> int:
        total = 0
        for i in range(0, len(payloads), batch_size):
            batch = payloads[i : i + batch_size]
            vectors = [
                {
                    "id": payload.vector_id,
                    "values": payload.values,
                    "metadata": payload.metadata,
                }
                for payload in batch
            ]
            if vectors:
                self.index.upsert(vectors=vectors)
                total += len(vectors)

        logger.info("pinecone_vectors_upserted", count=total)
        return total

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 50,
        document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        filter_obj: dict[str, Any] | None = None
        if document_ids:
            filter_obj = {"document_id": {"$in": document_ids}}

        response = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_obj,
        )

        matches = getattr(response, "matches", [])
        results: list[dict[str, Any]] = []
        for match in matches:
            metadata = getattr(match, "metadata", {}) or {}
            results.append(
                {
                    "score": getattr(match, "score", None),
                    "chunk_id": metadata.get("chunk_id"),
                    "document_id": metadata.get("document_id"),
                    "page_number": metadata.get("page_number"),
                    "content": metadata.get("content"),
                    "chunk_index": metadata.get("chunk_index"),
                }
            )
        return results

    def delete_document_vectors(self, document_id: str) -> None:
        self.index.delete(filter={"document_id": {"$eq": document_id}})
        logger.info("pinecone_document_vectors_deleted", document_id=document_id)

