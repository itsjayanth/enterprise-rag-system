from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import redis
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routes import api_router
from app.utils.logging_config import configure_logging
from app.utils.tracing import RequestContextMiddleware

configure_logging(settings.log_level)
logger = structlog.get_logger("app.main")


def check_database() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("database_health_check_failed")
        return False


def check_redis() -> bool:
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        return bool(client.ping())
    except Exception:
        logger.exception("redis_health_check_failed")
        return False


async def check_http_service(url: str) -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
        return {"status": "reachable" if response.is_success else "unhealthy", "url": url}
    except Exception:
        return {"status": "unreachable", "url": url}


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("app_startup", environment=settings.environment)
    yield
    logger.info("app_shutdown", environment=settings.environment)


app = FastAPI(
    title="Enterprise RAG API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware)

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    logger.info("health_check")
    return {
        "status": "healthy",
        "service": "backend",
        "environment": settings.environment,
    }


@app.get("/health/deep")
async def health_deep() -> dict[str, object]:
    database_ok = check_database()
    redis_ok = check_redis()

    llm_probe_url = (
        f"{settings.llm_service_url.rstrip('/')}/models"
        if settings.llm_service_url.rstrip("/").endswith("/v1")
        else settings.llm_service_url
    )

    services = {
        "embedding_service": await check_http_service(f"{settings.embedding_service_url.rstrip('/')}/health"),
        "reranker_service": await check_http_service(f"{settings.reranker_service_url.rstrip('/')}/health"),
        "llm_service": await check_http_service(llm_probe_url),
    }

    checks = {
        "database": "healthy" if database_ok else "unhealthy",
        "redis": "healthy" if redis_ok else "unhealthy",
        **services,
    }
    payload = {
        "status": "healthy" if database_ok and redis_ok else "unhealthy",
        "service": "backend",
        "environment": settings.environment,
        "checks": checks,
    }

    logger.info("deep_health_check", status=payload["status"], checks=checks)
    if not database_ok or not redis_ok:
        raise HTTPException(status_code=503, detail=payload)
    return payload

