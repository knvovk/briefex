from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

_log = logging.getLogger(__name__)


class Workflow(ABC):
    """Base class for workflow that encapsulate a sequence of steps."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._args = args
        self._kwargs = kwargs

        _log.info(
            "%s initialized with args=%r, kwargs=%r",
            self.__class__.__name__,
            self._args,
            self._kwargs,
        )

    @abstractmethod
    def run(self) -> None:
        """Execute the workflow steps."""
