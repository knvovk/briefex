from __future__ import annotations

import functools

from briefex.config import load_settings
from briefex.storage import init_connection
from briefex.workflow import CrawlWorkflow, SummarizeWorkflow

settings = load_settings()

init_connection(
    url=str(settings.sqlalchemy.url),
    echo=settings.sqlalchemy.echo,
    autoflush=settings.sqlalchemy.autoflush,
    autocommit=settings.sqlalchemy.autocommit,
    expire_on_commit=settings.sqlalchemy.expire_on_commit,
)


@functools.lru_cache(maxsize=1)
def create_crawl_workflow() -> CrawlWorkflow:
    """Configure and return a cached CrawlWorkflow instance."""
    from briefex.crawler import get_default_crawler_factory
    from briefex.crawler.fetchers import get_default_fetcher_factory
    from briefex.crawler.parsers import get_default_parser_factory
    from briefex.storage import (
        get_default_post_storage_factory,
        get_default_source_storage_factory,
    )

    fetcher_factory = get_default_fetcher_factory(
        request_timeout=settings.crawler.req_timeout,
        pool_connections=settings.crawler.pool_conn,
        pool_maxsize=settings.crawler.pool_max_size,
        max_retries=settings.crawler.max_retries,
        retry_delay=settings.crawler.retry_delay,
        max_retry_delay=settings.crawler.max_retry_delay,
    )
    parser_factory = get_default_parser_factory()
    crawler_factory = get_default_crawler_factory(
        fetcher_factory=fetcher_factory,
        parser_factory=parser_factory,
    )
    crawler = crawler_factory.create()

    post_storage_factory = get_default_post_storage_factory()
    source_storage_factory = get_default_source_storage_factory()
    post_storage = post_storage_factory.create()
    source_storage = source_storage_factory.create()

    return CrawlWorkflow(
        crawl=crawler,
        post_storage=post_storage,
        source_storage=source_storage,
        lookback_days=settings.crawler.lookback_days,
    )


@functools.lru_cache(maxsize=1)
def create_summarize_workflow() -> SummarizeWorkflow:
    """Configure and return a cached SummarizeWorkflow instance."""
    from briefex.intelligence.summarization import get_default_summarizer_factory
    from briefex.llm import get_default_provider_factory
    from briefex.storage import get_default_post_storage_factory

    post_storage_factory = get_default_post_storage_factory()
    post_storage = post_storage_factory.create()

    provider_factory = get_default_provider_factory(
        yandex_gpt_folder_id=settings.llm.yandex_gpt_folder_id,
        yandex_gpt_api_key=settings.llm.yandex_gpt_api_key,
        gigachat_credentials=settings.llm.gigachat_auth_key,
        gigachat_model=settings.llm.gigachat_model,
        gigachat_scope=settings.llm.gigachat_scope,
        gigachat_verify_ssl_certs=settings.llm.gigachat_verify_ssl_certs,
    )

    summarizer_factory = get_default_summarizer_factory(
        provider_factory=provider_factory,
        summarization_prompt=settings.intelligence.summarization_prompt,
        summarization_model=settings.intelligence.summarization_model,
        summarization_temperature=settings.intelligence.summarization_temperature,
        summarization_max_tokens=settings.intelligence.summarization_max_tokens,
    )
    summarizer = summarizer_factory.create()

    return SummarizeWorkflow(
        post_storage=post_storage,
        summarizer=summarizer,
    )
