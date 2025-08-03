from __future__ import annotations

import logging
from typing import override

from briefex.intelligence.exceptions import IntelligenceConfigurationError
from briefex.intelligence.summarization.base import Summarizer, SummarizerFactory
from briefex.intelligence.summarization.summarizer import DefaultSummarizer

_log = logging.getLogger(__name__)

_default_summarizer_cls: type[Summarizer] = DefaultSummarizer


class DefaultSummarizerFactory(SummarizerFactory):
    """Factory that selects and instantiates the default Summarizer."""

    @override
    def create(self) -> Summarizer:
        """Instantiate and return the default Summarizer.

        Returns:
            The default Summarizer instance.

        Raises:
            IntelligenceConfigurationError: If instantiation fails or no default is set.
        """
        _log.info(
            "Initializing summarizer by default: %s",
            _default_summarizer_cls.__name__,
        )
        try:
            instance = _default_summarizer_cls(
                *self._summarizer_args,
                **self._summarizer_kwargs,
            )
            _log.info(
                "%s initialized as default summarizer",
                _default_summarizer_cls.__name__,
            )
            return instance

        except Exception as exc:
            _log.error("Unexpected error during summarizer initialization: %s", exc)
            cls = _default_summarizer_cls.__name__
            raise IntelligenceConfigurationError(
                issue=f"Summarizer instantiation failed for {cls}: {exc}",
                stage="summarizer_instantiation",
            ) from exc
