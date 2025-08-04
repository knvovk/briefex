from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._models.completions.result import (
    AlternativeStatus,
    GPTModelResult,
)
from yandex_cloud_ml_sdk.auth import APIKeyAuth

from briefex.llm.base import Provider
from briefex.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMError,
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

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._models.completions.model import BaseGPTModel

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
        _log.info(
            "Sending completion request to YandexGPT (model='%s')",
            request.model,
        )
        provider_name = self.__class__.__name__

        try:
            model_instance = self._get_configured_model(request)
            sdk_messages = [_msg_as_dict(msg) for msg in request.messages]
            _log.debug(
                "Prepared %d messages for YandexGPT request",
                len(sdk_messages),
            )

            result = model_instance.run(sdk_messages)
            _log.info(
                "Received response from YandexGPT (status='%s')",
                result.status,
            )

            response = self._create_completion_response(request.model, result)
            _log.debug(
                "Constructed ChatCompletionResponse (status='%s')",
                response.status,
            )
            return response

        except LLMError:
            raise

        except Exception as exc:
            _log.error("Unexpected error during YandexGPT completion: %s", exc)
            raise LLMRequestError(
                issue=f"Completion error: {exc}",
                provider=provider_name,
            ) from exc

    def _get_configured_client(self, folder_id: str, api_key: str) -> YCloudML:
        """Instantiate and configure the YCloudML client for requests."""
        try:
            client = YCloudML(folder_id=folder_id, auth=APIKeyAuth(api_key))
            _log.info("YCloudML client initialized successfully")
            return client

        except Exception as exc:
            err_msg = str(exc).lower()
            if "auth" in err_msg or "key" in err_msg:
                _log.error("Authentication failed for YCloudML client: %s", exc)
                raise LLMAuthenticationError(
                    issue=f"Authentication error: {exc}",
                    provider=self.__class__.__name__,
                ) from exc

            _log.error("Configuration error initializing YCloudML client: %s", exc)
            raise LLMConfigurationError(
                issue=f"Client instantiation failed: {exc}",
                stage="yandexgpt_instantiation",
            ) from exc

    def _get_configured_model(self, request: ChatCompletionRequest) -> BaseGPTModel:
        """Configure and return a GPT model instance for the request."""
        _log.debug(
            "Configuring model '%s' (temperature=%.2f, max_tokens=%d, stream=%s)",
            request.model,
            request.params.temperature,
            request.params.max_tokens,
            request.params.stream,
        )

        try:
            model_wrapper = self._client.models.completions(request.model)
            configured = model_wrapper.configure(
                temperature=request.params.temperature,
                max_tokens=request.params.max_tokens,
            )
            _log.info("Model '%s' configured successfully", request.model)
            return configured

        except Exception as exc:
            _log.error("Error configuring model '%s': %s", request.model, exc)
            raise LLMConfigurationError(
                issue=f"Model configuration failed: {exc}",
                stage="yandexgpt_model_configuration",
            ) from exc

    def _create_completion_response(
        self,
        model: Model,
        result: GPTModelResult,
    ) -> ChatCompletionResponse:
        """Build a ChatCompletionResponse from the GPTModelResult."""
        try:
            usage = ChatCompletionUsage(
                prompt_tokens=result.usage.input_text_tokens,
                completion_tokens=result.usage.completion_tokens,
                total_tokens=result.usage.total_tokens,
            )
            status = _status_from_sdk_status(result.status)
            message = ChatCompletionMessage(
                role=Role.ASSISTANT,
                content=result.alternatives[0].text,
            )
            _log.debug(
                "Creating response object for model='%s' (status='%s')",
                model,
                status,
            )
            return ChatCompletionResponse(
                model=model, usage=usage, status=status, message=message
            )

        except Exception as exc:
            _log.error("Error creating ChatCompletionResponse: %s", exc)
            raise LLMResponseError(
                issue=f"Response creation failed: {exc}",
                provider=self.__class__.__name__,
            ) from exc
