from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.document import DocumentProcessResponse, DocumentResponse, DocumentStatusResponse
from ..services.document_service import DocumentService
from ..services.ingestion_service import IngestionService

router = APIRouter()
logger = structlog.get_logger("app.routes.documents")


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DocumentResponse:
    service = DocumentService(db)
    document = service.upload_document(file)

    # Queue background processing — import here to avoid circular import at module load
    try:
        from workers.tasks import process_document_task  # noqa: PLC0415

        document.status = "queued"
        db.commit()
        db.refresh(document)
        process_document_task.delay(str(document.id))
        logger.info(
            "document_task_queued",
            document_id=str(document.id),
            filename=document.filename,
        )
    except Exception as exc:
        # Worker not available (dev/test without Celery): leave as uploaded and log
        logger.warning(
            "document_task_queue_failed",
            document_id=str(document.id),
            exc=str(exc),
        )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    service = DocumentService(db)
    documents = service.list_documents()
    return [DocumentResponse.model_validate(document) for document in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentResponse:
    service = DocumentService(db)
    document = service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.post("/{document_id}/process", response_model=DocumentStatusResponse)
def process_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentStatusResponse:
    """Synchronous processing — kept for direct CLI/test use."""
    service = IngestionService(db)
    document = service.process_document(document_id)
    logger.info(
        "document_route_process_success",
        document_id=str(document.id),
        status=document.status,
        total_chunks=document.total_chunks,
    )
    return DocumentStatusResponse.model_validate(document)
