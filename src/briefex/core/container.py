from __future__ import annotations

import logging
from dataclasses import dataclass

import briefex.crawlers.fetchers
import briefex.crawlers.parsers
import briefex.intelligence.summarization
import briefex.llm.providers  # noqa: F401
from briefex import crawlers, intelligence, llm, storage
from briefex.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Container:
    """Container for dependency injection.

    This class holds all the application's dependencies and provides a way to
    access them throughout the application. It follows the dependency injection
    pattern to manage component lifecycles and dependencies.

    Attributes:
        settings: Application configuration settings.
        parser_factory: Factory for creating content parsers.
        fetcher_factory: Factory for creating content fetchers.
        crawler_factory: Factory for creating crawlers.
        crawler: Main crawler instance.
        llm_provider_factory: Factory for creating LLM providers.
        chat_completion_dispatcher_factory: Factory for creating
                                            chat completion dispatchers.
        chat_completion_dispatcher: Main chat completion dispatcher instance.
        summarizer_factory: Factory for creating summarizers.
        summarizer: Main summarizer instance.
        storage_factory: Factory for creating storage instances.
        src_storage: Storage for source entities.
        post_storage: Storage for post entities.
    """

    settings: Settings

    parser_factory: crawlers.parsers.ParserFactory
    fetcher_factory: crawlers.fetchers.FetcherFactory
    crawler_factory: crawlers.CrawlerFactory
    crawler: crawlers.Crawler

    llm_provider_factory: llm.providers.LLMProviderFactory
    chat_completion_dispatcher_factory: llm.ChatCompletionDispatcherFactory
    chat_completion_dispatcher: llm.ChatCompletionDispatcher

    summarizer_factory: intelligence.summarization.SummarizerFactory
    summarizer: intelligence.summarization.Summarizer

    storage_factory: storage.StorageFactory
    src_storage: storage.Storage[storage.Source]
    post_storage: storage.Storage[storage.Post]

    @classmethod
    def build(cls, settings: Settings) -> Container:
        """Build a container with all dependencies initialized.

        This factory method creates and initializes all application components
        and their dependencies based on the provided settings.

        Args:
            settings: Application configuration settings.

        Returns:
            A fully initialized Container instance with all dependencies set up.
        """
        logger.debug("Building container with settings: %s", settings)

        # Crawler Module Initialization
        parser_factory = crawlers.parsers.create_parser_factory()
        fetcher_factory = crawlers.fetchers.create_fetcher_factory(
            req_timeout=settings.crawler.req_timeout,
            pool_conn=settings.crawler.pool_conn,
            pool_max_size=settings.crawler.pool_max_size,
            max_retries=settings.crawler.max_retries,
            retry_delay=settings.crawler.retry_delay,
            max_retry_delay=settings.crawler.max_retry_delay,
        )
        crawler_factory = crawlers.create_crawler_factory(
            fetcher_factory=fetcher_factory,
            parser_factory=parser_factory,
        )
        crawler = crawler_factory.create()

        # LLM Module Initialization
        llm_provider_factory = llm.providers.create_llm_provider_factory(
            yandex_gpt_folder_id=settings.llm.yandex_gpt_folder_id,
            yandex_gpt_api_key=settings.llm.yandex_gpt_api_key,
            gigachat_credentials=settings.llm.gigachat_auth_key,
            gigachat_model=settings.llm.gigachat_model,
            gigachat_scope=settings.llm.gigachat_scope,
            gigachat_verify_ssl_certs=settings.llm.gigachat_verify_ssl_certs,
        )
        chat_completion_dispatcher_factory = (
            llm.create_chat_completion_dispatcher_factory(
                provider_factory=llm_provider_factory
            )
        )
        chat_completion_dispatcher = chat_completion_dispatcher_factory.create()

        # Intelligence Module Initialization
        summarizer_factory = intelligence.summarization.create_summarizer_factory(
            summarization_prompt=settings.intelligence.summarization_prompt,
            summarization_model=settings.intelligence.summarization_model,
            summarization_temperature=settings.intelligence.summarization_temperature,
            summarization_max_tokens=settings.intelligence.summarization_max_tokens,
            chat_completion_dispatcher=chat_completion_dispatcher,
        )
        summarizer = summarizer_factory.create()

        # Storage Module Initialization
        storage_factory = storage.create_storage_factory()
        src_storage = storage_factory.create(storage.Source)
        post_storage = storage_factory.create(storage.Post)

        return cls(
            settings=settings,
            parser_factory=parser_factory,
            fetcher_factory=fetcher_factory,
            crawler_factory=crawler_factory,
            crawler=crawler,
            llm_provider_factory=llm_provider_factory,
            chat_completion_dispatcher_factory=chat_completion_dispatcher_factory,
            chat_completion_dispatcher=chat_completion_dispatcher,
            summarizer_factory=summarizer_factory,
            summarizer=summarizer,
            storage_factory=storage_factory,
            src_storage=src_storage,
            post_storage=post_storage,
        )
