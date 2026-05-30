from celery import Celery

celery_app = Celery(
    "enterprise_rag",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

celery_app.conf.task_routes = {
    "workers.tasks.*": {"queue": "default"},
}

