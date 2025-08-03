from __future__ import annotations

import logging
from typing import override

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._models.completions.model import BaseGPTModel
from yandex_cloud_ml_sdk._models.completions.result import (
    AlternativeStatus,
    GPTModelResult,
)
from yandex_cloud_ml_sdk.auth import APIKeyAuth

from briefex.llm.base import Provider
from briefex.llm.exceptions import (
    LLMAuthenticationError,
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


def _msg_as_dict(message: ChatCompletionMessage) -> dict[str, str]:
    """Convert a ChatCompletionMessage to a dict format for YCloudML."""
    return {"role": message.role.value, "text": message.content}


def _status_from_sdk_status(status: AlternativeStatus) -> ChatCompletionStatus:
    """Map SDK AlternativeStatus to ChatCompletionStatus."""
    match status:
        case AlternativeStatus.FINAL:
            return ChatCompletionStatus.FINISHED

        case (AlternativeStatus.TRUNCATED_FINAL, AlternativeStatus.PARTIAL):
            return ChatCompletionStatus.TRUNCATED

        case AlternativeStatus.TOOL_CALLS:
            return ChatCompletionStatus.FUNCTION_CALL

        case AlternativeStatus.CONTENT_FILTER:
            return ChatCompletionStatus.CONTENT_FILTERED

        case _:
            return ChatCompletionStatus.UNDEFINED


@register(["yandexgpt", "yandexgpt-lite"])
class YandexGPT(Provider):
    """Provider for chat completions using Yandex Cloud ML."""

    def __init__(
        self,
        yandex_gpt_folder_id: str,
        yandex_gpt_api_key: str,
        **kwargs,
    ) -> None:
        kwargs.update(
            {
                "yandex_gpt_folder_id": yandex_gpt_folder_id,
                "yandex_gpt_api_key": yandex_gpt_api_key,
            }
        )
        super().__init__(*[], **kwargs)
        self._folder_id = yandex_gpt_folder_id
        self._api_key = yandex_gpt_api_key
        self._client = self._get_configured_client(
            folder_id=yandex_gpt_folder_id,
            api_key=yandex_gpt_api_key,
        )

    @override
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Send a chat completion request and return the response.

        Args:
            request: ChatCompletionRequest with messages and params.

        Returns:
            ChatCompletionResponse with output and usage statistics.

        Raises:
            LLMRequestError: If an unexpected error occurs during completion.
        """
        try:
            configured_model = self._get_configured_model(request)
            messages = [_msg_as_dict(msg) for msg in request.messages]
            _log.info("Sending request to model: %s", request.model)
            result = configured_model.run(messages)

            response = self._create_completion_response(request.model, result)
            return response

        except LLMException:
            raise

        except Exception as exc:
            _log.error("Unexpected error during chat completion: %s", exc)
            raise LLMRequestError(
                issue=f"Unexpected error during chat completion: {exc}",
                provider=self.__class__.__name__,
            ) from exc

    def _get_configured_client(self, folder_id: str, api_key: str) -> YCloudML:
        """Instantiate and configure the YCloudML client for requests."""
        try:
            return YCloudML(
                folder_id=folder_id,
                auth=APIKeyAuth(api_key),
            )

        except Exception as exc:
            err_msg = str(exc).lower()
            if "auth" in err_msg or "key" in err_msg:
                _log.error(
                    "Authentication error during %s initialization: %s",
                    self.__class__.__name__,
                    exc,
                )
                raise LLMAuthenticationError(
                    issue=f"Failed to initialize YCloudML: {exc}",
                    provider=self.__class__.__name__,
                ) from exc

            raise LLMConfigurationError(
                issue=f"Client instantiation failed for YCloudML: {exc}",
                stage=f"{self.__class__.__name__}_instantiation",
            ) from exc

    def _get_configured_model(self, request: ChatCompletionRequest) -> BaseGPTModel:
        """Configure and return a GPT model instance for the request."""
        try:
            _log.info(
                "Configuring request for model: %s "
                "(temperature=%.2f, max_tokens=%d, stream=%s)",
                request.model,
                request.params.temperature,
                request.params.max_tokens,
                request.params.stream,
            )

            instance = self._client.models.completions(request.model)
            return instance.configure(
                temperature=request.params.temperature,
                max_tokens=request.params.max_tokens,
            )

        except Exception as exc:
            _log.error("Unexpected error during request configuration: %s", exc)
            raise LLMConfigurationError(
                issue=f"Failed to initialize {self.__class__.__name__}: {exc}",
                stage=f"{self.__class__.__name__}_initialization",
            ) from exc

    def _create_completion_response(
        self,
        model: Model,
        result: GPTModelResult,
    ) -> ChatCompletionResponse:
        """Build a ChatCompletionResponse from the GPTModelResult."""
        try:
            return ChatCompletionResponse(
                model=model,
                usage=ChatCompletionUsage(
                    prompt_tokens=result.usage.input_text_tokens,
                    completion_tokens=result.usage.completion_tokens,
                    total_tokens=result.usage.total_tokens,
                ),
                status=_status_from_sdk_status(result.status),
                message=ChatCompletionMessage(
                    role=Role.ASSISTANT,
                    content=result.alternatives[0].text,
                ),
            )

        except Exception as exc:
            _log.error("Unexpected error during response creation: %s", exc)
            raise LLMResponseError(
                issue=f"Response creation failed for {model}: {exc}",
                provider=self.__class__.__name__,
            ) from exc
