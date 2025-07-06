import logging
from typing import NoReturn, override

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._models.completions.model import BaseGPTModel
from yandex_cloud_ml_sdk._models.completions.result import (
    AlternativeStatus,
    GPTModelResult,
)
from yandex_cloud_ml_sdk.auth import APIKeyAuth

from ..exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMContentFilterError,
    LLMException,
    LLMParsingError,
    LLMRequestError,
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
                    client=self.__class__.__name__,
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

            logger.debug(
                "Sending request to model: %s (messages_count=%d)",
                request.model,
                len(messages),
            )
            result = configured_model.run(messages)
            self._raise_for_status(result)

            response = self._create_completion_response(request.model, result)
            return response

        except LLMException:
            raise

        except Exception as exc:
            logger.error("Failed to complete chat: %s", exc)
            self._process_exception(exc)

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
            logger.debug(
                "Configuring model: %s (temperature=%.2f, max_tokens=%d)",
                model,
                params.temperature,
                params.max_tokens,
            )

            instance = self._client.models.completions(model)
            return instance.configure(
                temperature=params.temperature,
                max_tokens=params.max_tokens,
            )

        except Exception as exc:
            err_msg = str(exc).lower()
            if "model" in err_msg and ("not found" in err_msg or "invalid" in err_msg):
                logger.error("Model %s not found or invalid: %s", model, exc)
                raise LLMConfigurationError(
                    issue=f"Model {model} not found or invalid",
                    component=f"{self.__class__.__name__}_model_configuration",
                ) from exc

            logger.error("Failed to configure model %s: %s", model, exc)
            raise LLMConfigurationError(
                issue=f"Failed to configure model {model}: {exc}",
                component=f"{self.__class__.__name__}_model_configuration",
            ) from exc

    def _raise_for_status(self, result: GPTModelResult) -> None:
        """Check the result status and raise appropriate exceptions if needed.

        Args:
            result: The result from the model run.

        Raises:
            LLMParsingError: If the result is empty or has an invalid structure.
            LLMContentFilterError: If the content was filtered by the model.
        """
        if not result or not hasattr(result, "status"):
            logger.error(
                "Response validation error: Empty or invalid response structure"
            )
            raise LLMParsingError(
                client=self.__class__.__name__,
                reason="Empty or invalid response structure",
                raw_response=str(result),
            )

        if result.status == AlternativeStatus.CONTENT_FILTER:
            logger.warning("Content filtered by model during response parsing")
            raise LLMContentFilterError(
                client=self.__class__.__name__,
                reason="Content filter",
            )

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
                message=ChatCompletionMessage(
                    role=Role.ASSISTANT,
                    content=result.alternatives[0].text,
                ),
            )
        except Exception as exc:
            logger.error(
                "Failed to parse %s response: %s",
                self.__class__.__name__,
                exc,
            )
            raise LLMParsingError(
                client=self.__class__.__name__,
                reason=f"Failed to extract data from response: {exc}",
                raw_response=str(result),
            ) from exc

    def _process_exception(self, exc: Exception) -> NoReturn:
        """Process an exception and raise an appropriate LLM exception.

        This method analyzes the exception message and raises a more specific
        LLM exception based on the content.

        Args:
            exc: The exception to process.

        Raises:
            LLMConfigurationError: If the exception is related to folder ID mismatch.
            LLMRequestError: For all other exceptions.

        Returns:
            This method never returns as it always raises an exception.
        """
        err_msg = str(exc).lower()

        if (
            "does not match with service account folder id" in err_msg
            or "specified folder id" in err_msg
        ):
            logger.error(
                "Authentication error during %s request: %s",
                self.__class__.__name__,
                exc,
            )
            raise LLMConfigurationError(
                issue=f"Incorrect folder_id: {self._folder_id} has been specified, "
                f"which does not match the folder_id of the service account.",
                component=f"{self.__class__.__name__}_request",
            ) from exc

        raise LLMRequestError(
            client=self.__class__.__name__,
            reason=str(exc),
        )
