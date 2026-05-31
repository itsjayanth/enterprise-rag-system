from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
import os
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .model import EmbeddingModel, EmbeddingSettings


@dataclass(slots=True)
class AppState:
    embedding_model: EmbeddingModel | None = None
    model_status: str = "not_loaded"
    model_name: str = "BAAI/bge-m3"
    model_cache_dir: str = "/data/models"
    model_error: str | None = None


state = AppState()


def load_model_in_background() -> None:
    state.model_status = "loading"
    try:
        settings = EmbeddingSettings(model_name=state.model_name, model_cache_dir=state.model_cache_dir)
        state.embedding_model = EmbeddingModel(settings)
        state.model_status = "ready"
        state.model_error = None
    except Exception as exc:  # pragma: no cover - startup-path robustness
        state.embedding_model = None
        state.model_status = "failed"
        state.model_error = str(exc)


class EmbedDocumentsRequest(BaseModel):
    texts: list[str] = Field(default_factory=list)


class EmbedDocumentsResponse(BaseModel):
    embeddings: list[list[float]]
    count: int
    dimensions: int


class EmbedQueryRequest(BaseModel):
    text: str


class EmbedQueryResponse(BaseModel):
    embedding: list[float]
    dimensions: int


@asynccontextmanager
async def lifespan(_: FastAPI):
    state.model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
    state.model_cache_dir = os.getenv("MODEL_CACHE_DIR", "/data/models")
    threading.Thread(target=load_model_in_background, daemon=True).start()
    yield
    state.embedding_model = None
    state.model_status = "not_loaded"
    state.model_error = None


app = FastAPI(title="Embedding Service", version="0.1.0", lifespan=lifespan)


def get_model() -> EmbeddingModel:
    if state.embedding_model is None:
        detail = "Model is not loaded"
        if state.model_status == "loading":
            detail = "Model is still loading"
        elif state.model_status == "failed":
            detail = f"Model failed to load: {state.model_error or 'unknown error'}"
        raise HTTPException(status_code=503, detail=detail)
    return state.embedding_model


@app.get("/health")
def health() -> dict[str, str]:
    model = state.embedding_model
    return {
        "status": "healthy" if state.model_status == "ready" else "starting",
        "service": "embedding-service",
        "model": state.model_name,
        "device": model.device if model is not None else "unknown",
        "model_status": state.model_status,
    }


@app.post("/embed/documents", response_model=EmbedDocumentsResponse)
def embed_documents(payload: EmbedDocumentsRequest) -> EmbedDocumentsResponse:
    model = get_model()
    if not payload.texts:
        raise HTTPException(status_code=400, detail="texts must contain at least one item")

    embeddings = model.embed_documents(payload.texts)
    dimensions = len(embeddings[0]) if embeddings else 0
    return EmbedDocumentsResponse(embeddings=embeddings, count=len(embeddings), dimensions=dimensions)


@app.post("/embed/query", response_model=EmbedQueryResponse)
def embed_query(payload: EmbedQueryRequest) -> EmbedQueryResponse:
    model = get_model()
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must not be empty")

    embedding = model.embed_query(text)
    return EmbedQueryResponse(embedding=embedding, dimensions=len(embedding))

