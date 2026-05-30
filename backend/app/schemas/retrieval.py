from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1)
    document_ids: list[str] | None = None
    top_k: int | None = Field(default=None, ge=1)


class RetrievedChunk(BaseModel):
    chunk_id: str | None
    document_id: str | None
    page_number: int | None
    chunk_index: int | None
    score: float | None
    rerank_score: float | None = None
    content: str


class RetrievalResponse(BaseModel):
    context: str
    chunks: list[RetrievedChunk]
    timings: dict[str, float] | None = None

