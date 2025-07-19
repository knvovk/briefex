import logging
from typing import override

from briefex import llm
from briefex.llm.exceptions import LLMException

from ..exceptions import SummarizationError
from .base import Summarizer

logger = logging.getLogger(__name__)


class SummarizerImpl(Summarizer):
    """Implementation of the Summarizer interface.

    This class provides a concrete implementation of the Summarizer
    abstract base class, using LLM to generate text summaries.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new SummarizerImpl.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments. Expected keys include:
                summarization_prompt: The prompt to use for summarization.
                summarization_model: The LLM model to use.
                summarization_temperature: The temperature parameter for the model.
                summarization_max_tokens: The maximum number of tokens in the response.
                chat_completion_dispatcher: The dispatcher for chat completion requests.
        """
        super().__init__(*args, **kwargs)
        self._prompt = kwargs.get("summarization_prompt")
        self._model = kwargs.get("summarization_model")
        self._temperature = kwargs.get("summarization_temperature")
        self._max_tokens = kwargs.get("summarization_max_tokens")
        self._chat_completion_dispatcher = kwargs.get("chat_completion_dispatcher")
        logger.info("%s initialized", self.__class__.__name__)

    @override
    def summarize(self, text: str) -> str:
        """Summarize the given text using LLM.

        This method creates a chat completion request with the input text,
        sends it to the LLM, and returns the generated summary.

        Args:
            text: The text to summarize.

        Returns:
            A concise summary of the input text.

        Raises:
            SummarizationError: If the text cannot be summarized due to LLM errors
                or other unexpected issues.
        """
        logger.info("Starting summarization for text (length=%d)", len(text))

        try:
            request = self._create_chat_completion_request(text)
            response = self._chat_completion_dispatcher.complete(request)
            content = response.message.content
            logger.info("Finished summarization for text (length=%d)", len(content))
            return content

        except LLMException as exc:
            logger.error("Summarization failed: %s", exc.message)
            raise SummarizationError(
                reason=exc.details.get("reason", exc.message)
            ) from exc

        except Exception as exc:
            logger.error("Unexpected error during summarization: %s", exc)
            raise SummarizationError(reason=str(exc)) from exc

    def _create_chat_completion_request(self, text: str) -> llm.ChatCompletionRequest:
        """Create a chat completion request for summarization.

        This method constructs a ChatCompletionRequest object with the appropriate
        model, parameters, and messages for summarizing the given text.

        Args:
            text: The text to be summarized.

        Returns:
            A configured ChatCompletionRequest object ready to be sent to the LLM.
        """
        return llm.ChatCompletionRequest(
            model=self._model,
            params=llm.ChatCompletionParams(
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            ),
            messages=[
                llm.ChatCompletionMessage(
                    role=llm.Role.ASSISTANT,
                    content=self._prompt,
                ),
                llm.ChatCompletionMessage(
                    role=llm.Role.USER,
                    content=text,
                ),
            ],
        )
