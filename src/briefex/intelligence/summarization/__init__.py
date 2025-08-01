from __future__ import annotations

from typing import Any

from briefex.intelligence.summarization.base import SummarizerFactory
from briefex.intelligence.summarization.factory import DefaultSummarizerFactory

_summarizer_factory: SummarizerFactory | None = None


def get_default_summarizer_factory(*args: Any, **kwargs: Any) -> SummarizerFactory:
    global _summarizer_factory

    if _summarizer_factory is None:
        _summarizer_factory = DefaultSummarizerFactory(*args, **kwargs)

    return _summarizer_factory
