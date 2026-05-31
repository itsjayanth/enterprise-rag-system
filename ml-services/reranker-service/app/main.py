from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
import os
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .model import RerankerModel, RerankerSettings


@dataclass(slots=True)
class AppState:
    reranker_model: RerankerModel | None = None
    model_status: str = "not_loaded"
    model_name: str = "BAAI/bge-reranker-v2-m3"
    model_cache_dir: str = "/data/models"
    model_error: str | None = None


state = AppState()


def load_model_in_background() -> None:
    state.model_status = "loading"
    try:
        settings = RerankerSettings(model_name=state.model_name, model_cache_dir=state.model_cache_dir)
        state.reranker_model = RerankerModel(settings)
        state.model_status = "ready"
        state.model_error = None
    except Exception as exc:  # pragma: no cover - startup-path robustness
        state.reranker_model = None
        state.model_status = "failed"
        state.model_error = str(exc)


class RerankRequest(BaseModel):
    query: str = Field(min_length=1)
    documents: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1)


class RerankResult(BaseModel):
    index: int
    score: float


class RerankResponse(BaseModel):
    results: list[RerankResult]


@asynccontextmanager
async def lifespan(_: FastAPI):
    state.model_name = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-v2-m3")
    state.model_cache_dir = os.getenv("MODEL_CACHE_DIR", "/data/models")
    threading.Thread(target=load_model_in_background, daemon=True).start()
    yield
    state.reranker_model = None
    state.model_status = "not_loaded"
    state.model_error = None


app = FastAPI(title="Reranker Service", version="0.1.0", lifespan=lifespan)


def get_model() -> RerankerModel:
    if state.reranker_model is None:
        detail = "Model is not loaded"
        if state.model_status == "loading":
            detail = "Model is still loading"
        elif state.model_status == "failed":
            detail = f"Model failed to load: {state.model_error or 'unknown error'}"
        raise HTTPException(status_code=503, detail=detail)
    return state.reranker_model


@app.get("/health")
def health() -> dict[str, str]:
    model = state.reranker_model
    return {
        "status": "healthy" if state.model_status == "ready" else "starting",
        "service": "reranker-service",
        "model": state.model_name,
        "device": model.device if model is not None else "unknown",
        "model_status": state.model_status,
    }


@app.post("/rerank", response_model=RerankResponse)
def rerank(payload: RerankRequest) -> RerankResponse:
    model = get_model()
    query = payload.query.strip()
    documents = [document.strip() for document in payload.documents if document.strip()]

    if not query:
        raise HTTPException(status_code=400, detail="query must not be empty")
    if not documents:
        raise HTTPException(status_code=400, detail="documents must contain at least one non-empty item")

    top_k = min(payload.top_k, len(documents))
    results = model.rerank(query=query, documents=documents, top_k=top_k)
    return RerankResponse(results=[RerankResult(index=int(item["index"]), score=float(item["score"])) for item in results])
