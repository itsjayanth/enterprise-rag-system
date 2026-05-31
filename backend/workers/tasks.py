from __future__ import annotations

import structlog
from celery import Task

from app.database import SessionLocal
from app.services.ingestion_service import IngestionService
from .celery_app import celery_app

logger = structlog.get_logger("workers.tasks")

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 10


class _BaseTask(Task):
    """Base task with structured logging and DB session cleanup."""

    abstract = True

    def on_failure(self, exc: Exception, task_id: str, args: list, kwargs: dict, einfo) -> None:
        logger.error(
            "task_failed",
            task_id=task_id,
            task_name=self.name,
            args=args,
            exc=str(exc),
        )

    def on_retry(self, exc: Exception, task_id: str, args: list, kwargs: dict, einfo) -> None:
        logger.warning(
            "task_retrying",
            task_id=task_id,
            task_name=self.name,
            args=args,
            exc=str(exc),
        )

    def on_success(self, retval, task_id: str, args: list, kwargs: dict) -> None:
        logger.info(
            "task_succeeded",
            task_id=task_id,
            task_name=self.name,
            args=args,
        )


@celery_app.task(
    base=_BaseTask,
    bind=True,
    name="workers.tasks.process_document_task",
    max_retries=_MAX_RETRIES,
    default_retry_delay=_RETRY_DELAY_SECONDS,
    queue="document_ingestion",
)
def process_document_task(self, document_id: str) -> dict:
    """Parse, chunk, embed, and vector-index a document."""
    logger.info("process_document_task_started", document_id=document_id)
    db = SessionLocal()
    try:
        import uuid
        service = IngestionService(db)
        document = service.process_document(uuid.UUID(document_id))
        return {
            "document_id": document_id,
            "status": document.status,
            "total_chunks": document.total_chunks,
        }
    except ValueError as exc:
        # Non-retryable: bad document ID, missing file, corrupt PDF etc.
        logger.error("process_document_task_unrecoverable", document_id=document_id, exc=str(exc))
        raise
    except Exception as exc:
        # Transient failure — retry with exponential backoff
        logger.warning("process_document_task_transient_error", document_id=document_id, exc=str(exc))
        raise self.retry(exc=exc, countdown=_RETRY_DELAY_SECONDS * (2 ** self.request.retries))
    finally:
        db.close()
