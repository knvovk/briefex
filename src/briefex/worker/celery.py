from __future__ import annotations

import logging.config
from pathlib import Path

from celery import Celery, signals

from briefex.config import load_settings

settings = load_settings()

app = Celery(
    "briefex",
    broker=str(settings.celery.broker_url),
    backend=str(settings.celery.result_backend),
    include=["briefex.worker.tasks"],
)

app.conf.update(
    task_serializer=settings.celery.task_serializer,
    result_serializer=settings.celery.result_serializer,
    accept_content=settings.celery.accept_content,
    timezone=settings.celery.timezone,
    enable_utc=settings.celery.enable_utc,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=360,
    worker_max_tasks_per_child=100,
    worker_hijack_root_logger=False,
    worker_send_task_events=True,
    worker_enable_remote_control=True,
)


@signals.setup_logging.connect
def setup_logging(**_: object) -> None:
    ini = Path(__file__).parent.parent / "config" / "logging.ini"
    logging.config.fileConfig(ini)
