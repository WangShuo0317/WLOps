"""
Celery 应用配置
"""
from celery import Celery
from config import config

# 创建 Celery 应用
celery_app = Celery(
    "data_optimizer",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=["tasks"]
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=config.TASK_TIMEOUT,
    task_soft_time_limit=config.TASK_TIMEOUT - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
