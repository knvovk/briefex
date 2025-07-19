class IntelligenceException(Exception):
    """Base exception class for all intelligence-related exceptions.

    This class provides a common structure for all intelligence exceptions,
    including a message and optional details dictionary.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing additional error details.
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize the intelligence exception.

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


class IntelligenceConfigurationError(IntelligenceException):
    """Exception raised for configuration errors in intelligence components.

    This exception is raised when there is an issue with the configuration
    of an intelligence component.

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


class IntelligenceInputError(IntelligenceException):
    """Exception raised for invalid input to intelligence components.

    This exception is raised when the input provided to an intelligence
    component is invalid or cannot be processed.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the input type and reason details.
    """

    def __init__(self, input_type: str, reason: str) -> None:
        """Initialize the input error.

        Args:
            input_type: The type of input that was invalid.
            reason: The reason why the input was invalid.
        """
        super().__init__(
            message=f"Invalid input: {reason}",
            details={
                "input_type": input_type,
                "reason": reason,
            },
        )


class IntelligenceProcessingError(IntelligenceException):
    """Exception raised for errors during processing in intelligence components.

    This exception is raised when an error occurs during the processing
    of data in an intelligence component.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the operation and reason details.
    """

    def __init__(self, operation: str, reason: str) -> None:
        """Initialize the processing error.

        Args:
            operation: The operation that was being performed.
            reason: The reason for the processing error.
        """
        super().__init__(
            message=f"Processing error during {operation}: {reason}",
            details={
                "operation": operation,
                "reason": reason,
            },
        )


class IntelligenceModelError(IntelligenceException):
    """Exception raised for errors related to the underlying model.

    This exception is raised when there is an issue with the model
    used by an intelligence component.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the model and reason details.
    """

    def __init__(self, model: str, reason: str) -> None:
        """Initialize the model error.

        Args:
            model: The model that encountered an error.
            reason: The reason for the model error.
        """
        super().__init__(
            message=f"Model error: {reason}",
            details={
                "model": model,
                "reason": reason,
            },
        )


class IntelligenceFactoryError(IntelligenceException):
    """Exception raised for errors during factory operations.

    This exception is raised when there is an error creating an
    intelligence component using a factory.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing the factory type and reason details.
    """

    def __init__(self, factory_type: str, reason: str) -> None:
        """Initialize the factory error.

        Args:
            factory_type: The type of factory that encountered an error.
            reason: The reason for the factory error.
        """
        super().__init__(
            message=f"Factory error: {reason}",
            details={
                "factory_type": factory_type,
                "reason": reason,
            },
        )


class SummarizationError(IntelligenceException):
    """Exception raised for errors during summarization.

    This exception is raised when there is an error during the
    summarization process.

    Attributes:
        message: A descriptive error message.
        details: A dictionary containing error details.
    """

    def __init__(self, reason: str, text_length: int | None = None) -> None:
        """Initialize the summarization error.

        Args:
            reason: The reason for the summarization error.
            text_length: The length of the text that was being summarized, if available.
        """
        details = {"reason": reason}
        if text_length is not None:
            details["text_length"] = text_length

        super().__init__(
            message=f"Summarization error: {reason}",
            details=details,
        )
