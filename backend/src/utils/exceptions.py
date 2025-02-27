"""Custom exceptions for the backend application."""

class BackendError(Exception):
    """Base class for all backend exceptions."""
    pass

class ConfigurationError(BackendError):
    """Exception raised for configuration errors."""
    pass

class APIError(BackendError):
    """Exception raised for API errors."""
    pass

class AssistantError(APIError):
    """Exception raised for errors related to AI assistants."""
    pass

class FileProcessingError(BackendError):
    """Exception raised for errors during file processing."""
    pass

class PDFProcessingError(FileProcessingError):
    """Exception raised for errors during PDF processing."""
    pass

class DataProcessingError(BackendError):
    """Exception raised for errors during data processing."""
    pass

class ValidationError(BackendError):
    """Exception raised for validation errors."""
    pass 