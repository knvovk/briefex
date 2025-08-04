from __future__ import annotations


class IntelligenceError(Exception):
    """Base exception for intelligence operations with message and optional details."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details!r})"
        return self.message

    def __str__(self) -> str:
        return repr(self)


class IntelligenceConfigurationError(IntelligenceError):
    """Raised when intelligence component configuration is invalid."""

    def __init__(self, issue: str, stage: str) -> None:
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "stage": stage,
            },
        )


class IntelligenceContentCensoredError(IntelligenceError):
    """Raised when content is filtered or censored during processing."""

    def __init__(self, issue: str, provider: str) -> None:
        super().__init__(
            message=f"Censored: {issue}",
            details={
                "issue": issue,
                "provider": provider,
            },
        )


class IntelligenceSummarizationError(IntelligenceError):
    """Raised when summarization fails in an intelligence provider."""

    def __init__(self, issue: str, provider: str) -> None:
        super().__init__(
            message=f"Summarization error: {issue}",
            details={
                "issue": issue,
                "provider": provider,
            },
        )
