from app.core.celery_app import celery

celery.autodiscover_tasks(["app.langchain_pipeline"])