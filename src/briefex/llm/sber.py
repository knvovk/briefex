from __future__ import annotations

import logging
from typing import override

import gigachat as sdk
import httpx
from gigachat import models as sdk_models

from briefex.llm.base import Provider
from briefex.llm.exceptions import (
    LLMConfigurationError,
    LLMException,
    LLMRequestError,
    LLMResponseError,
)
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


def _msg_to_sdk_msg(message: ChatCompletionMessage) -> sdk_models.Messages:
    """Convert ChatCompletionMessage to SDK Messages format."""
    return sdk_models.Messages(
        role=sdk_models.MessagesRole(message.role.value),
        content=message.content,
    )


def _status_from_sdk_status(status: str) -> ChatCompletionStatus:
    """Map SDK finish reason to ChatCompletionStatus."""
    match status:
        case "stop":
            return ChatCompletionStatus.FINISHED

        case "length":
            return ChatCompletionStatus.TRUNCATED

        case "function_call":
            return ChatCompletionStatus.FUNCTION_CALL

        case "blacklist":
            return ChatCompletionStatus.CONTENT_FILTERED

        case "error":
            return ChatCompletionStatus.ERROR

        case _:
            return ChatCompletionStatus.UNDEFINED


@register(["GigaChat-2", "GigaChat-2-Pro", "GigaChat-2-Max"])
class GigaChat(Provider):
    """Provider implementation using the GigaChat SDK."""

    def __init__(
        self,
        gigachat_credentials: str,
        gigachat_model: Model,
        gigachat_scope: str,
        gigachat_verify_ssl_certs: bool,
        gigachat_timeout: int = 30,
        **kwargs,
    ) -> None:
        super().__init__(
            gigachat_credentials,
            gigachat_model,
            gigachat_scope,
            gigachat_verify_ssl_certs,
            gigachat_timeout,
            **kwargs,
        )
        self._credentials = gigachat_credentials
        self._model = gigachat_model
        self._scope = gigachat_scope
        self._verify_ssl_certs = gigachat_verify_ssl_certs
        self._timeout = gigachat_timeout

    @override
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Send chat completion request and return provider response.

        Args:
            request: ChatCompletionRequest containing messages and params.

        Returns:
            ChatCompletionResponse with model output and usage.

        Raises:
            LLMRequestError: On request or timeout failures.
            LLMResponseError: On response parsing failures.
        """
        try:
            with self._get_configured_client() as client:
                payload = self._get_configured_sdk_request(request)
                _log.info("Sending request to model: %s", request.model)
                result = client.chat(payload)

                response = self._create_completion_response(request.model, result)
                return response

        except LLMException:
            raise

        except httpx.TimeoutException as exc:
            _log.error("Timeout error during chat completion: %s", exc)
            raise LLMRequestError(
                issue=f"Timeout error during chat completion: {exc}",
                provider=self.__class__.__name__,
            ) from exc

        except Exception as exc:
            _log.error("Unexpected error during chat completion: %s", exc)
            raise LLMRequestError(
                issue=f"Unexpected error during chat completion: {exc}",
                provider=self.__class__.__name__,
            ) from exc

    def _get_configured_client(self) -> sdk.GigaChat:
        """Instantiate and return a configured GigaChat SDK client."""
        try:
            return sdk.GigaChat(
                credentials=self._credentials,
                scope=self._scope,
                model=self._model,
                verify_ssl_certs=self._verify_ssl_certs,
                timeout=self._timeout,
            )
        except Exception as exc:
            raise LLMConfigurationError(
                issue=f"Client instantiation failed for {self._model}: {exc}",
                stage=f"{self.__class__.__name__}_instantiation",
            ) from exc

    def _get_configured_sdk_request(
        self,
        request: ChatCompletionRequest,
    ) -> sdk_models.Chat:
        """Build and return an SDK Chat request from ChatCompletionRequest."""
        _log.info(
            "Configuring request for model: %s "
            "(temperature=%.2f, max_tokens=%d, stream=%s)",
            request.model,
            request.params.temperature,
            request.params.max_tokens,
            request.params.stream,
        )

        try:
            messages = [_msg_to_sdk_msg(msg) for msg in request.messages]
            chat = sdk_models.Chat(
                model=request.model,
                messages=messages,
                temperature=request.params.temperature,
                max_tokens=request.params.max_tokens,
                stream=request.params.stream,
            )
            return chat

        except Exception as exc:
            _log.error("Unexpected error during request configuration: %s", exc)
            raise LLMRequestError(
                issue=f"Request configuration failed for {self._model}: {exc}",
                provider=self.__class__.__name__,
            ) from exc

    def _create_completion_response(
        self,
        model: Model,
        result: sdk_models.ChatCompletion,
    ) -> ChatCompletionResponse:
        """Convert SDK ChatCompletion into ChatCompletionResponse."""
        try:
            return ChatCompletionResponse(
                model=model,
                usage=ChatCompletionUsage(
                    prompt_tokens=result.usage.prompt_tokens,
                    completion_tokens=result.usage.completion_tokens,
                    total_tokens=result.usage.total_tokens,
                ),
                status=_status_from_sdk_status(result.choices[0].finish_reason),
                message=ChatCompletionMessage(
                    role=Role.ASSISTANT,
                    content=result.choices[0].message.content,
                ),
            )

        except Exception as exc:
            _log.error("Unexpected error during response creation: %s", exc)
            raise LLMResponseError(
                issue=f"Response creation failed for {model}: {exc}",
                provider=self.__class__.__name__,
            ) from exc
