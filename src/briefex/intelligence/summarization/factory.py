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
        class_name = _default_summarizer_cls.__name__
        _log.debug("Instantiating default summarizer class '%s'", class_name)

        try:
            instance = _default_summarizer_cls(
                *self._summarizer_args,
                **self._summarizer_kwargs,
            )
            _log.info("Summarizer '%s' instantiated successfully", class_name)
            return instance

        except Exception as exc:
            _log.error("Failed to instantiate summarizer '%s': %s", class_name, exc)
            raise IntelligenceConfigurationError(
                issue=f"Summarizer instantiation failed for '{class_name}': {exc}",
                stage="summarizer_instantiation",
            ) from exc
