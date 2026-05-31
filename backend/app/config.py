from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict



def _detect_root_dir() -> Path:
    current = Path(__file__).resolve()
    candidates = [*current.parents, Path.cwd().resolve()]
    for candidate in candidates:
        if (candidate / "req.txt").exists() or (candidate / "docker-compose.yml").exists():
            return candidate
    return current.parents[1]


ROOT_DIR = _detect_root_dir()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql://postgres:postgres@postgres:5432/enterprise_rag"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    redis_url: str = "redis://redis:6379/0"

    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "enterprise-rag"
    pinecone_host: str = ""
    pinecone_index_dimension: int = 1024
    pinecone_metric: str = "cosine"

    upload_dir: str = "./data/uploads"
    model_cache_dir: str = "./data/models"
    max_upload_size_mb: int = 50

    embedding_model_name: str = "BAAI/bge-m3"
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    llm_model_name: str = "llama3.1:8b"

    embedding_service_url: str = "http://embedding-service:8001"
    reranker_service_url: str = "http://reranker-service:8002"
    llm_service_url: str = "http://localhost:11434/v1"

    retrieval_top_k: int = 50
    rerank_top_k: int = 5
    max_context_tokens: int = 2048
    llm_temperature: float = 0.1
    llm_max_tokens: int = 512

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3002",
            "http://localhost:3000",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:3000",
        ]
    )

    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return [
                "http://localhost:3002",
                "http://localhost:3000",
                "http://127.0.0.1:3002",
                "http://127.0.0.1:3000",
            ]
        if isinstance(value, list):
            return value
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @field_validator("max_upload_size_mb", "retrieval_top_k", "rerank_top_k", "max_context_tokens", "llm_max_tokens")
    @classmethod
    def validate_positive_numbers(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be greater than zero")
        return value


settings = Settings()

