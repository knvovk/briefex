import logging
from typing import override

import httpx
from gigachat import GigaChat
from gigachat import models as sdk_models

from ..exceptions import (
    LLMCompletionError,
    LLMConfigurationError,
    LLMContentFilterError,
    LLMException,
    LLMTimeoutError,
)
from ..models import (
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    Model,
    Role,
)
from .base import LLMProvider
from .registry import register

logger = logging.getLogger(__name__)


def _msg_to_sdk_msg(message: ChatCompletionMessage) -> sdk_models.Messages:
    """Convert a ChatCompletionMessage to a format expected by GigaChat SDK.

    Args:
        message: The chat completion message to convert.

    Returns:
        A Messages object compatible with the GigaChat SDK.
    """
    return sdk_models.Messages(
        role=sdk_models.MessagesRole(message.role.value),
        content=message.content,
    )


@register(["GigaChat-2", "GigaChat-2-Pro", "GigaChat-2-Max"])
class GigaChatProvider(LLMProvider):
    """Provider for GigaChat language models.

    This class implements the LLMProvider interface for GigaChat models,
    handling authentication, request formatting, and response parsing.

    Attributes:
        _client: The GigaChat client instance.
    """

    def __init__(
        self,
        gigachat_credentials: str,
        gigachat_model: Model,
        gigachat_scope: str,
        gigachat_verify_ssl_certs: bool,
        gigachat_timeout: int = 30,
        **kwargs,
    ) -> None:
        """Initialize the GigaChat provider.

        Args:
            gigachat_credentials: The credentials for GigaChat authentication.
            gigachat_scope: The scope for GigaChat API access.
            gigachat_model: The GigaChat model to use.
            gigachat_verify_ssl_certs: Whether to verify SSL certificates.
            **kwargs: Additional configuration parameters.

        Raises:
            LLMConfigurationError: If initialization fails.
        """
        super().__init__(**kwargs)
        self._credentials = gigachat_credentials
        self._model = gigachat_model
        self._scope = gigachat_scope
        self._verify_ssl_certs = gigachat_verify_ssl_certs
        self._timeout = gigachat_timeout

    @override
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Process a chat completion request and return a response.

        This method configures the payload, sends the request to the GigaChat API,
        and processes the response.

        Args:
            request: The chat completion request containing messages and model information.

        Returns:
            A chat completion response from the language model.

        Raises:
            LLMException: If an error occurs during completion.
            LLMCompletionError: If the chat completion fails.
        """
        try:
            with self._get_configured_client() as client:
                payload = self._get_configured_sdk_request(request)

                logger.info("Sending request to model: %s", request.model)
                result = client.chat(payload)
                self._raise_for_status(result)

                response = self._create_completion_response(request.model, result)
                return response

        except LLMException:
            raise

        except httpx.TimeoutException as exc:
            logger.error("Timeout error during chat completion: %s", exc)
            raise LLMTimeoutError(
                provider=self.__class__.__name__,
                timeout=self._timeout,
            ) from exc

        except Exception as exc:
            logger.error("Unexpected error during chat completion: %s", exc)
            raise LLMCompletionError(
                provider=self.__class__.__name__,
                reason=str(exc),
            ) from exc

    def _get_configured_client(self) -> GigaChat:
        """Get a configured GigaChat client instance.

        Returns:
            A configured GigaChat client instance.

        Raises:
            LLMConfigurationError: If the client cannot be initialized.
        """
        try:
            return GigaChat(
                credentials=self._credentials,
                scope=self._scope,
                model=self._model,
                verify_ssl_certs=self._verify_ssl_certs,
                timeout=self._timeout,
            )
        except Exception as exc:
            raise LLMConfigurationError(
                issue=f"Failed to initialize {self.__class__.__name__}: {exc}",
                component=f"{self.__class__.__name__}_initialization",
            ) from exc

    def _get_configured_sdk_request(
        self,
        request: ChatCompletionRequest,
    ) -> sdk_models.Chat:
        """Get a configured payload for the specified request.

        Args:
            request: The chat completion request to configure the payload for.

        Returns:
            A configured Chat payload for the GigaChat API.

        Raises:
            LLMConfigurationError: If payload configuration fails.
        """
        logger.info(
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
            logger.error("Unexpected error during request configuration: %s", exc)
            raise LLMConfigurationError(
                issue=f"Failed to configure request payload: {exc}",
                component=f"{self.__class__.__name__}_payload_configuration",
            ) from exc

    def _raise_for_status(self, result: sdk_models.ChatCompletion) -> None:
        """Check the result status and raise appropriate exceptions if needed.

        Args:
            result: The result from the chat completion.

        Note:
            Currently this method only prints the result for debugging purposes.
            It should be extended to handle error cases appropriately.
        """
        try:
            status = result.choices[0].finish_reason
            content = result.choices[0].message.content
            logger.info(
                "Response received from model: %s (status=%s)",
                result.model,
                status,
            )

            if status == "blacklist":
                logger.warning(
                    "Response content was filtered by the model: %s",
                    content[:64],
                )
                raise LLMContentFilterError(
                    provider=self.__class__.__name__,
                    reason="User content was filtered by the model",
                )

            elif status == "error":
                logger.error("Response has an error status: %s", content[:64])
                raise LLMCompletionError(
                    provider=self.__class__.__name__,
                    reason="Response has an error status",
                )

        except LLMException:
            raise

        except Exception as exc:
            logger.error("Unexpected error during response status check: %s", exc)
            raise LLMCompletionError(
                provider=self.__class__.__name__,
                reason=f"Failed to check response status: {exc}",
            )

    def _create_completion_response(
        self,
        model: Model,
        result: sdk_models.ChatCompletion,
    ) -> ChatCompletionResponse:
        """Create a ChatCompletionResponse from the model result.

        Args:
            model: The language model that generated the result.
            result: The result from the chat completion.

        Returns:
            A chat completion response.

        Raises:
            LLMCompletionError: If the response cannot be parsed.
        """
        try:
            return ChatCompletionResponse(
                model=model,
                usage=ChatCompletionUsage(
                    prompt_tokens=result.usage.prompt_tokens,
                    completion_tokens=result.usage.completion_tokens,
                    total_tokens=result.usage.total_tokens,
                ),
                message=ChatCompletionMessage(
                    role=Role.ASSISTANT,
                    content=result.choices[0].message.content,
                ),
            )

        except Exception as exc:
            logger.error("Unexpected error during response parsing: %s", exc)
            raise LLMCompletionError(
                provider=self.__class__.__name__,
                reason=f"Failed to parse response: {exc}",
            )
