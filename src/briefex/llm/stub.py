from __future__ import annotations

import logging
from typing import override

from briefex.llm.base import Provider
from briefex.llm.exceptions import LLMRequestError
from briefex.llm.models import (
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStatus,
    ChatCompletionUsage,
    Model,
    Role,
)
from briefex.llm.registry import register

_log = logging.getLogger(__name__)


@register(["STUB", "Stub", "stub"])
class Stub(Provider):
    """Echo-style LLM provider used as a lightweight stand-in."""

    @override
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Return a completion that echoes the input content.

        Args:
            request: Chat-completion request containing model, params, and messages.

        Returns:
            ChatCompletionResponse whose assistant message mirrors the input content.

        Raises:
            LLMRequestError: If an unexpected error occurs while producing a response.
        """
        _log.info("Sending completion request to Stub (model='%s')", request.model)

        try:
            _log.debug(
                "SDK request configured: temperature=%.2f, max_tokens=%d, stream=%s",
                request.params.temperature,
                request.params.max_tokens,
                request.params.stream,
            )
            response = self._create_completion_response(
                model=request.model,
                content=request.messages[1].content,
            )
            _log.info(
                "Received response from Stub (finish_reason='%s')",
                response.status,
            )
            return response

        except Exception as exc:
            _log.error("Unexpected error during Stub completion: %s", exc)
            raise LLMRequestError(
                issue=f"Completion error: {exc}",
                provider=self.__class__.__name__,
            ) from exc

    def _create_completion_response(
        self,
        model: Model,
        content: str,
    ) -> ChatCompletionResponse:
        """Build a ChatCompletionResponse.FINISHED with zeroed usage."""
        usage = ChatCompletionUsage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )
        status = ChatCompletionStatus.FINISHED
        message = ChatCompletionMessage(
            role=Role.ASSISTANT,
            content=content,
        )
        _log.debug(
            "Creating ChatCompletionResponse (model='%s', status='%s')",
            model,
            status,
        )
        return ChatCompletionResponse(
            model=model,
            usage=usage,
            status=status,
            message=message,
        )
