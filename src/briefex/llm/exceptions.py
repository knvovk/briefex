from __future__ import annotations


class LLMError(Exception):
    """Base exception for LLM operations with message and optional details."""

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


class LLMConfigurationError(LLMError):
    """Raised when LLM provider configuration is invalid."""

    def __init__(self, issue: str, stage: str) -> None:
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "stage": stage,
            },
        )


class LLMAuthenticationError(LLMError):
    """Raised when authentication with the LLM provider fails."""

    def __init__(self, issue: str, provider: str) -> None:
        super().__init__(
            message=f"Authentication error: {issue}",
            details={
                "issue": issue,
                "provider": provider,
            },
        )


class LLMRequestError(LLMError):
    """Raised when a request to the LLM provider fails."""

    def __init__(self, issue: str, provider: str) -> None:
        super().__init__(
            message=f"Request error: {issue}",
            details={
                "issue": issue,
                "provider": provider,
            },
        )


class LLMResponseError(LLMError):
    """Raised when parsing or handling the LLM provider response fails."""

    def __init__(self, issue: str, provider: str) -> None:
        super().__init__(
            message=f"Response error: {issue}",
            details={
                "issue": issue,
                "provider": provider,
            },
        )
