from __future__ import annotations

import logging
from typing import Any, override

from briefex.intelligence.exceptions import (
    IntelligenceContentCensoredError,
    IntelligenceSummarizationError,
)
from briefex.intelligence.summarization.base import Summarizer
from briefex.llm import (
    ChatCompletionMessage,
    ChatCompletionParams,
    ChatCompletionRequest,
    ChatCompletionStatus,
    Provider,
    ProviderFactory,
    Role,
)

_log = logging.getLogger(__name__)


class DefaultSummarizer(Summarizer):
    """Summarizer that uses an LLM provider for text summarization."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._provider_factory: ProviderFactory = kwargs.get("provider_factory")
        self._prompt = kwargs.get("summarization_prompt")
        self._model = kwargs.get("summarization_model")
        self._temperature = kwargs.get("summarization_temperature")
        self._max_tokens = kwargs.get("summarization_max_tokens")

    @override
    def summarize(self, text: str) -> str:
        """Generate a concise summary of the input text.

        Args:
            text: The text to summarize.

        Returns:
            The summarized text.

        Raises:
            IntelligenceContentCensoredError: If content is filtered by the provider.
            IntelligenceSummarizationError: If an unexpected error occurs.
        """
        _log.info("Starting text summarization (input length: %d chars)", len(text))

        provider: Provider | None = None
        try:
            request = self._build_completion_request(text)
            provider = self._provider_factory.create(self._model)
            response = provider.complete(request)

            if response.status == ChatCompletionStatus.CONTENT_FILTERED:
                _log.warning(
                    "Summarization aborted: content was filtered by provider %s",
                    provider.__class__.__name__,
                )
                raise IntelligenceContentCensoredError(
                    issue=response.message.content,
                    provider=provider.__class__.__name__,
                )

            _log.info(
                "Summarization completed successfully "
                "(output length: %d chars, model: %s, status: %s, "
                "prompt tokens: %d, completion tokens: %d, total tokens: %d)",
                len(response.message.content),
                response.model,
                response.status,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                response.usage.total_tokens,
            )
            return response.message.content

        except IntelligenceContentCensoredError:
            raise

        except Exception as exc:
            _log.error("Summarization failed due to unexpected error: %s", exc)
            raise IntelligenceSummarizationError(
                issue=str(exc),
                provider=provider.__class__.__name__ if provider else None,
            ) from exc

    def _build_completion_request(self, text: str) -> ChatCompletionRequest:
        return ChatCompletionRequest(
            model=self._model,
            params=ChatCompletionParams(
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                stream=False,
            ),
            messages=[
                ChatCompletionMessage(
                    role=Role.ASSISTANT,
                    content=self._prompt,
                ),
                ChatCompletionMessage(
                    role=Role.USER,
                    content=text,
                ),
            ],
        )
