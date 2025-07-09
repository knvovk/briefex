import logging
from typing import override

import llm
from llm.exceptions import LLMException

from ..exceptions import SummarizationError
from .base import Summarizer

logger = logging.getLogger(__name__)


class SummarizerImpl(Summarizer):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._prompt = kwargs.get("summarization_prompt")
        self._model = kwargs.get("summarization_model")
        self._temperature = kwargs.get("summarization_temperature")
        self._max_tokens = kwargs.get("summarization_max_tokens")
        self._chat_completion_dispatcher = kwargs.get("chat_completion_dispatcher")
        logger.info("%s initialized", self.__class__.__name__)

    @override
    def summarize(self, text: str) -> str:
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
