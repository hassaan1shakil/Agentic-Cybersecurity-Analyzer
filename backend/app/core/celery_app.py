from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL,  # Optional: stores result/status
)

# path may still be wrong
celery.conf.task_routes = {
    "app.langchain_pipeline.run_pipeline.run_chain": {"queue": "langchain"},
}