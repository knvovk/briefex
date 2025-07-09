import logging
from typing import override

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._models.completions.model import BaseGPTModel
from yandex_cloud_ml_sdk._models.completions.result import (
    AlternativeStatus,
    GPTModelResult,
)
from yandex_cloud_ml_sdk.auth import APIKeyAuth

from ..exceptions import (
    LLMAuthenticationError,
    LLMCompletionError,
    LLMConfigurationError,
    LLMContentFilterError,
    LLMException,
    LLMParsingError,
)
from ..models import (
    ChatCompletionMessage,
    ChatCompletionParams,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    Model,
    Role,
)
from .base import LLMProvider
from .registry import register

logger = logging.getLogger(__name__)


def _message_to_dict(message: ChatCompletionMessage) -> dict[str, str]:
    """Convert a ChatCompletionMessage to a dictionary format expected by Yandex API.

    Args:
        message: The chat completion message to convert.

    Returns:
        A dictionary with 'role' and 'text' keys.
    """
    return {"role": message.role, "text": message.content}


@register(["yandexgpt", "yandexgpt-lite"])
class YandexGPTProvider(LLMProvider):
    """Provider for Yandex GPT language models.

    This class implements the LLMProvider interface for Yandex GPT models,
    handling authentication, request formatting, and response parsing.

    Attributes:
        _folder_id: The Yandex Cloud folder ID.
        _api_key: The Yandex Cloud API key.
        _client: The Yandex Cloud ML client.
    """

    def __init__(
        self,
        yandex_gpt_folder_id: str,
        yandex_gpt_api_key: str,
        **kwargs,
    ) -> None:
        """Initialize the Yandex GPT provider.

        Args:
            yandex_gpt_folder_id: The Yandex Cloud folder ID.
            yandex_gpt_api_key: The Yandex Cloud API key.
            **kwargs: Additional configuration parameters.

        Raises:
            LLMAuthenticationError: If authentication fails.
            LLMConfigurationError: If initialization fails for other reasons.
        """
        super().__init__(**kwargs)
        try:
            self._folder_id = yandex_gpt_folder_id
            self._api_key = yandex_gpt_api_key
            self._client = YCloudML(
                folder_id=yandex_gpt_folder_id,
                auth=APIKeyAuth(yandex_gpt_api_key),
            )

        except Exception as exc:
            err_msg = str(exc).lower()
            if "auth" in err_msg or "key" in err_msg:
                logger.error(
                    "Authentication error during %s initialization: %s",
                    self.__class__.__name__,
                    exc,
                )
                raise LLMAuthenticationError(
                    provider=self.__class__.__name__,
                    reason=str(exc),
                ) from exc

            raise LLMConfigurationError(
                issue=f"Failed to initialize {self.__class__.__name__}: {exc}",
                component=f"{self.__class__.__name__}_initialization",
            ) from exc

    @override
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Process a chat completion request and return a response.

        This method configures the model, sends the request to the Yandex GPT API,
        and processes the response.

        Args:
            request: The chat completion request containing messages and model information.

        Returns:
            A chat completion response from the language model.

        Raises:
            LLMException: If an error occurs during completion.
        """
        try:
            configured_model = self._get_configured_model(request.model, request.params)
            messages = [_message_to_dict(msg) for msg in request.messages]

            logger.info("Sending request to model: %s", request.model)
            result = configured_model.run(messages)
            self._raise_for_status(request.model, result)

            response = self._create_completion_response(request.model, result)
            return response

        except LLMException:
            raise

        except Exception as exc:
            logger.error("Unexpected error during chat completion: %s", exc)
            raise LLMCompletionError(
                provider=self.__class__.__name__,
                reason=str(exc),
            ) from exc

    def _get_configured_model(
        self,
        model: Model,
        params: ChatCompletionParams,
    ) -> BaseGPTModel:
        """Get a configured model instance for the specified model and parameters.

        Args:
            model: The language model to configure.
            params: The parameters to configure the model with.

        Returns:
            A configured model instance.

        Raises:
            LLMConfigurationError: If the model is not found or configuration fails.
        """
        try:
            logger.info(
                "Configuring request for model: %s "
                "(temperature=%.2f, max_tokens=%d, stream=%s)",
                model,
                params.temperature,
                params.max_tokens,
                params.stream,
            )

            instance = self._client.models.completions(model)
            return instance.configure(
                temperature=params.temperature,
                max_tokens=params.max_tokens,
            )

        except Exception as exc:
            logger.error("Unexpected error during request configuration: %s", exc)
            raise LLMConfigurationError(
                issue=f"Failed to initialize {self.__class__.__name__}: {exc}",
                component=f"{self.__class__.__name__}_initialization",
            ) from exc

    def _raise_for_status(self, model: Model, result: GPTModelResult) -> None:
        """Check the result status and raise appropriate exceptions if needed.

        Args:
            result: The result from the model run.

        Raises:
            LLMParsingError: If the result is empty or has an invalid structure.
            LLMContentFilterError: If the content was filtered by the model.
        """
        try:
            logger.info(
                "Response received from model: %s (status=%s)",
                model,
                result.status,
            )

            if result.status == AlternativeStatus.CONTENT_FILTER:
                logger.warning("Response content was filtered by the model")
                raise LLMContentFilterError(
                    provider=self.__class__.__name__,
                    reason="User content was filtered by the model",
                )

        except LLMException:
            raise

        except Exception as exc:
            logger.error("Unexpected error during response status check: %s", exc)
            raise LLMParsingError(
                provider=self.__class__.__name__,
                reason=f"Failed to check response status: {exc}",
            ) from exc

    def _create_completion_response(
        self,
        model: Model,
        result: GPTModelResult,
    ) -> ChatCompletionResponse:
        """Create a ChatCompletionResponse from the model result.

        Args:
            model: The language model that generated the result.
            result: The result from the model run.

        Returns:
            A chat completion response.

        Raises:
            LLMParsingError: If the response cannot be parsed.
        """
        try:
            return ChatCompletionResponse(
                model=model,
                usage=ChatCompletionUsage(
                    prompt_tokens=result.usage.input_text_tokens,
                    completion_tokens=result.usage.completion_tokens,
                    total_tokens=result.usage.total_tokens,
                ),
                status=result.status,
                message=ChatCompletionMessage(
                    role=Role.ASSISTANT,
                    content=result.alternatives[0].text,
                ),
            )

        except Exception as exc:
            logger.error("Unexpected error during response parsing: %s", exc)
            raise LLMParsingError(
                provider=self.__class__.__name__,
                reason=f"Failed to parse response: {exc}",
            ) from exc
