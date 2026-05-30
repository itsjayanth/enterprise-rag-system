from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import os
import torch
from sentence_transformers import CrossEncoder


@dataclass(slots=True)
class RerankerSettings:
    model_name: str = "BAAI/bge-reranker-v2-m3"
    model_cache_dir: str = "/data/models"


class RerankerModel:
    def __init__(self, settings: RerankerSettings):
        self.settings = settings
        self.device = self._detect_device()
        self.cache_dir = self._resolve_cache_dir(settings.model_cache_dir)
        os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(self.cache_dir))
        self.model = CrossEncoder(
            model_name=settings.model_name,
            device=self.device,
            trust_remote_code=True,
        )

    @staticmethod
    def _detect_device() -> str:
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @staticmethod
    def _resolve_cache_dir(configured_path: str) -> Path:
        configured = Path(configured_path)
        if configured.is_absolute():
            return configured

        docker_cache = Path("/data/models")
        if docker_cache.exists():
            return docker_cache

        return configured.resolve()

    def rerank(self, query: str, documents: list[str], top_k: int) -> list[dict[str, float | int]]:
        if not documents:
            return []

        pairs = [[query, document] for document in documents]
        scores = self.model.predict(pairs, show_progress_bar=False)
        indexed_scores = [{"index": idx, "score": float(score)} for idx, score in enumerate(scores)]
        indexed_scores.sort(key=lambda item: item["score"], reverse=True)
        return indexed_scores[:top_k]
