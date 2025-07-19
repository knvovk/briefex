class LLMException(Exception):
    """Base exception class for all LLM-related exceptions.

    This class provides a common structure for all LLM exceptions,
    including a message and optional details' dictionary.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing additional error details.
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize the LLM exception.

        Args:
            message: A descriptive error message.
            details: A dictionary containing additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            A string containing the message and details if available.
        """
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            A string representation of the exception.
        """
        return repr(self)


class LLMConfigurationError(LLMException):
    """Exception raised for configuration errors in LLM components.

    This exception is raised when there is an issue with the configuration
    of an LLM component.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the issue and component details.
    """

    def __init__(self, issue: str, component: str) -> None:
        """Initialize the configuration error.

        Args:
            issue: Description of the configuration issue.
            component: The component where the configuration issue occurred.
        """
        super().__init__(
            message=f"Configuration error: {issue}",
            details={
                "issue": issue,
                "component": component,
            },
        )


class LLMAuthenticationError(LLMException):
    """Exception raised for authentication errors with LLM providers.

    This exception is raised when there is an issue authenticating with
    an LLM provider.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the provider and reason details.
    """

    def __init__(self, provider: str, reason: str) -> None:
        """Initialize the authentication error.

        Args:
            provider: The LLM provider where authentication failed.
            reason: The reason for the authentication failure.
        """
        super().__init__(
            message="Authentication error",
            details={
                "provider": provider,
                "reason": reason,
            },
        )


class LLMAuthorizationError(LLMException):
    """Exception raised for authorization errors with LLM providers.

    This exception is raised when there is an issue with authorization
    to access a specific resource from an LLM provider.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the provider, reason, and resource details.
    """

    def __init__(self, provider: str, reason: str, resource: str) -> None:
        """Initialize the authorization error.

        Args:
            provider: The LLM provider where authorization failed.
            reason: The reason for the authorization failure.
            resource: The resource that could not be accessed.
        """
        super().__init__(
            message="Authorization error",
            details={
                "provider": provider,
                "reason": reason,
                "resource": resource,
            },
        )


class LLMNetworkError(LLMException):
    """Exception raised for network errors when communicating with LLM providers.

    This exception is raised when there is a network-related issue while
    communicating with an LLM provider.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the provider and reason details.
    """

    def __init__(self, provider: str, reason: str) -> None:
        """Initialize the network error.

        Args:
            provider: The LLM provider where the network error occurred.
            reason: The reason for the network error.
        """
        super().__init__(
            message="Network error",
            details={
                "provider": provider,
                "reason": reason,
            },
        )


class LLMTimeoutError(LLMException):
    """Exception raised for timeout errors when communicating with LLM providers.

    This exception is raised when a request to an LLM provider times out.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the provider and timeout details.
    """

    def __init__(self, provider: str, timeout: int) -> None:
        """Initialize the timeout error.

        Args:
            provider: The LLM provider where the timeout occurred.
            timeout: The timeout value in seconds.
        """
        super().__init__(
            message="Timeout error",
            details={
                "provider": provider,
                "timeout": timeout,
            },
        )


class LLMValidationError(LLMException):
    """Exception raised for validation errors in LLM requests.

    This exception is raised when a parameter in an LLM request fails validation.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing validation details.
    """

    def __init__(
        self,
        provider: str,
        parameter: str,
        actual_value: str,
        expected_value: str,
    ) -> None:
        """Initialize the validation error.

        Args:
            provider: The LLM provider where validation failed.
            parameter: The parameter that failed validation.
            actual_value: The actual value of the parameter.
            expected_value: The expected value or format of the parameter.
        """
        super().__init__(
            message="Validation error",
            details={
                "provider": provider,
                "parameter": parameter,
                "actual_value": actual_value,
                "expected_value": expected_value,
            },
        )


class LLMRequestError(LLMException):
    """Exception raised for errors in LLM requests.

    This exception is raised when there is an issue with the request
    sent to an LLM provider.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the provider and reason details.
    """

    def __init__(self, provider: str, reason: str) -> None:
        """Initialize the request error.

        Args:
            provider: The LLM provider where the request error occurred.
            reason: The reason for the request error.
        """
        super().__init__(
            message="Request error",
            details={
                "provider": provider,
                "reason": reason,
            },
        )


class LLMResponseError(LLMException):
    """Exception raised for errors in LLM responses.

    This exception is raised when there is an issue with the response
    received from an LLM provider.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing response error details.
    """

    def __init__(self, provider: str, reason: str, raw_response: str = "") -> None:
        """Initialize the response error.

        Args:
            provider: The LLM provider that returned the error response.
            reason: The reason for the response error.
            raw_response: The raw response from the provider, if available.
        """
        super().__init__(
            message="Response error",
            details={
                "provider": provider,
                "reason": reason,
                "raw_response": raw_response,
            },
        )


class LLMCompletionError(LLMException):
    """Exception raised for errors during chat completion.

    This exception is raised when there is an error during the chat
    completion process.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the provider and reason details.
    """

    def __init__(self, provider: str, reason: str) -> None:
        """Initialize the completion error.

        Args:
            provider: The LLM provider where the completion error occurred.
            reason: The reason for the completion error.
        """
        super().__init__(
            message="Chat completion error",
            details={
                "provider": provider,
                "reason": reason,
            },
        )


class LLMParsingError(LLMException):
    """Exception raised for errors when parsing LLM responses.

    This exception is raised when there is an error parsing the response
    from an LLM provider.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing parsing error details.
    """

    def __init__(self, provider: str, reason: str, raw_response: str = "") -> None:
        """Initialize the parsing error.

        Args:
            provider: The LLM provider whose response could not be parsed.
            reason: The reason for the parsing error.
            raw_response: The raw response that could not be parsed, if available.
        """
        super().__init__(
            message="Parse error",
            details={
                "provider": provider,
                "reason": reason,
                "raw_response": raw_response,
            },
        )


class LLMRateLimitError(LLMException):
    """Exception raised when rate limits are exceeded for LLM providers.

    This exception is raised when a rate limit is exceeded when making
    requests to an LLM provider.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing rate limit details.
    """

    def __init__(
        self,
        provider: str,
        limit_type: str,
        retry_after: int | None = None,
    ) -> None:
        """Initialize the rate limit error.

        Args:
            provider: The LLM provider where the rate limit was exceeded.
            limit_type: The type of rate limit that was exceeded.
            retry_after: The number of seconds after which to retry, if available.
        """
        super().__init__(
            message="Rate limit exceeded",
            details={
                "provider": provider,
                "limit_type": limit_type,
                "retry_after": retry_after,
            },
        )


class LLMQuotaExceededError(LLMException):
    """Exception raised when quotas are exceeded for LLM providers.

    This exception is raised when a quota is exceeded when making
    requests to an LLM provider.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing quota details.
    """

    def __init__(
        self,
        provider: str,
        quota_type: str,
        reset_time: str | None = None,
    ) -> None:
        """Initialize the quota exceeded the error.

        Args:
            provider: The LLM provider where the quota was exceeded.
            quota_type: The type of quota that was exceeded.
            reset_time: The time when the quota will reset, if available.
        """
        super().__init__(
            message="Quota exceeded",
            details={
                "provider": provider,
                "quota_type": quota_type,
                "reset_time": reset_time,
            },
        )


class LLMContentFilterError(LLMException):
    """Exception raised when content is filtered by LLM providers.

    This exception is raised when content is filtered or blocked by
    an LLM provider's content filtering system.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the provider and reason details.
    """

    def __init__(self, provider: str, reason: str) -> None:
        """Initialize the content filter error.

        Args:
            provider: The LLM provider that filtered the content.
            reason: The reason for the content being filtered.
        """
        super().__init__(
            message="Content filtered",
            details={
                "provider": provider,
                "reason": reason,
            },
        )
