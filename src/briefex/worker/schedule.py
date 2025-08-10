from __future__ import annotations

from datetime import timedelta

from celery.schedules import crontab

from briefex.worker.celery import app
from briefex.worker.tasks import clean, crawl, summarize

app.conf.beat_schedule = {
    "crawl-every-10-min": {
        "task": crawl.name,
        "schedule": timedelta(minutes=10),
        "options": {"expires": 600},
    },
    "summarize-every-hour": {
        "task": summarize.name,
        "schedule": timedelta(hours=1),
        "options": {"expires": 3600},
    },
    "clean-every-day": {
        "task": clean.name,
        "schedule": crontab(hour=0, minute=0),
        "options": {"expires": 3600},
    },
}
