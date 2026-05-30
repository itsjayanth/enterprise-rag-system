from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

_QUERY_PREFIX = "Represent this query for retrieving relevant documents:"


@dataclass(slots=True)
class EmbeddingSettings:
    model_name: str = "BAAI/bge-m3"
    model_cache_dir: str = "/data/models"


class EmbeddingModel:
    def __init__(self, settings: EmbeddingSettings):
        self.settings = settings
        self.device = self._detect_device()
        self.batch_size = 32 if self.device in {"mps", "cuda"} else 8
        self.cache_dir = self._resolve_cache_dir(settings.model_cache_dir)
        self.model = SentenceTransformer(
            settings.model_name,
            device=self.device,
            cache_folder=str(self.cache_dir),
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

        # In local Docker this path is mounted and preferred.
        docker_cache = Path("/data/models")
        if docker_cache.exists():
            return docker_cache

        return configured.resolve()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        enriched_query = f"{_QUERY_PREFIX} {text.strip()}"
        vector = self.model.encode(
            [enriched_query],
            batch_size=1,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return vector.tolist()

