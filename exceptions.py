
"""Custom exceptions for the OpenAI Assistant application."""

class AssistantError(Exception):
    """Base exception for assistant-related errors."""
    pass

class ImageValidationError(AssistantError):
    """Raised when image validation fails."""
    pass

class ThreadCreationError(AssistantError):
    """Raised when thread creation fails."""
    pass

class MessageCreationError(AssistantError):
    """Raised when message creation fails."""
    pass

class FileUploadError(AssistantError):
    """Raised when file upload fails."""
    pass

class ResponseTimeoutError(AssistantError):
    """Raised when assistant response times out."""
    pass
