from celery import Celery

from app.config import settings

celery_app = Celery(
    "enterprise_rag",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "workers.tasks.process_document_task": {"queue": "document_ingestion"},
    },
    task_queues_default="document_ingestion",
)
