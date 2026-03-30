"""Celery app configuration for ShlokVault background tasks."""

import sys
import ssl
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

_broker_url = settings.CELERY_BROKER_URL or settings.REDIS_URL
_backend_url = _broker_url

celery_app = Celery(
    "shlokvault",
    broker=_broker_url,
    backend=_backend_url,
    include=[
        "app.tasks.email_tasks",
    ],
)

_ssl_config = {"ssl_cert_reqs": ssl.CERT_NONE}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_pool="solo" if sys.platform == "win32" else "prefork",
    broker_use_ssl=_ssl_config
    if (_broker_url or "").startswith("rediss://")
    else None,
    redis_backend_use_ssl=_ssl_config
    if (_backend_url or "").startswith("rediss://")
    else None,
)
