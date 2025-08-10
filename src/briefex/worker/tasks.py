from __future__ import annotations

from briefex.worker.celery import app
from briefex.workflow import create_crawl_workflow, create_summarize_workflow


@app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_backoff_max=600,
    max_retries=5,
)
def crawl():
    create_crawl_workflow().run()


@app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_backoff_max=600,
    max_retries=5,
)
def summarize() -> None:
    create_summarize_workflow().run()


@app.task
def clean(): ...
