"""Custom exception handlers."""
from typing import Optional


class ClaimsValidatorError(Exception):
    """Base exception for claims validator."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(ClaimsValidatorError):
    """Raised when validation fails."""

    pass


class DataQualityError(ClaimsValidatorError):
    """Raised when data quality checks fail."""

    pass


class LLMError(ClaimsValidatorError):
    """Raised when LLM evaluation fails."""

    pass


class FileProcessingError(ClaimsValidatorError):
    """Raised when file processing fails."""

    pass

