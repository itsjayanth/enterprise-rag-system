from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from ..schemas.retrieval import RetrievalRequest, RetrievalResponse, RetrievedChunk
from ..services.retrieval_service import RetrievalService

router = APIRouter()
logger = structlog.get_logger("app.routes.retrieval")


@router.post("/search", response_model=RetrievalResponse, status_code=status.HTTP_200_OK)
def search(payload: RetrievalRequest) -> RetrievalResponse:
    service = RetrievalService()
    try:
        result = service.retrieve(
            query=payload.query,
            document_ids=payload.document_ids,
            top_k=payload.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("retrieval_search_failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Retrieval pipeline failed") from exc

    chunks = [RetrievedChunk.model_validate(chunk) for chunk in result["chunks"]]
    return RetrievalResponse(context=result["context"], chunks=chunks, timings=result.get("timings"))

