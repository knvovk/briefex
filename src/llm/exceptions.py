class LLMException(Exception):

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def __str__(self) -> str:
        return repr(self)


class LLMConfigurationError(LLMException):

    def __init__(self, issue: str, component: str) -> None:
        super().__init__(
            message="Configuration error",
            details={
                "issue": issue,
                "component": component,
            },
        )


class LLMAuthenticationError(LLMException):

    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            message="Authentication error",
            details={
                "provider": provider,
                "reason": reason,
            },
        )


class LLMAuthorizationError(LLMException):

    def __init__(self, provider: str, reason: str, resource: str) -> None:
        super().__init__(
            message="Authorization error",
            details={
                "provider": provider,
                "reason": reason,
                "resource": resource,
            },
        )


class LLMNetworkError(LLMException):

    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            message="Network error",
            details={
                "provider": provider,
                "reason": reason,
            },
        )


class LLMTimeoutError(LLMException):

    def __init__(self, provider: str, timeout: int) -> None:
        super().__init__(
            message="Timeout error",
            details={
                "provider": provider,
                "timeout": timeout,
            },
        )


class LLMValidationError(LLMException):

    def __init__(
        self,
        provider: str,
        parameter: str,
        actual_value: str,
        expected_value: str,
    ) -> None:
        super().__init__(
            message="Validation error",
            details={
                "provider": provider,
                "parameter": parameter,
                "actual_value": actual_value,
                "expected_value": expected_value,
            },
        )


class LLMResponseError(LLMException):

    def __init__(self, provider: str, reason: str, raw_response: str = "") -> None:
        super().__init__(
            message="Response error",
            details={
                "provider": provider,
                "reason": reason,
                "raw_response": raw_response,
            },
        )


class LLMParsingError(LLMException):

    def __init__(self, provider: str, reason: str, raw_response: str = "") -> None:
        super().__init__(
            message="Parse error",
            details={
                "provider": provider,
                "reason": reason,
                "raw_response": raw_response,
            },
        )


class LLMRateLimitError(LLMException):

    def __init__(
        self,
        provider: str,
        limit_type: str,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message="Rate limit exceeded",
            details={
                "provider": provider,
                "limit_type": limit_type,
                "retry_after": retry_after,
            },
        )


class LLMQuotaExceededError(LLMException):

    def __init__(
        self,
        provider: str,
        quota_type: str,
        reset_time: str | None = None,
    ) -> None:
        super().__init__(
            message="Quota exceeded",
            details={
                "provider": provider,
                "quota_type": quota_type,
                "reset_time": reset_time,
            },
        )


class LLMContentFilterError(LLMException):

    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            message="Content filtered",
            details={
                "provider": provider,
                "reason": reason,
            },
        )
