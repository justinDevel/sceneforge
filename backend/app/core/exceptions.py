"""
Custom exceptions for SceneForge backend.
"""

from typing import Any, Dict, Optional


class SceneForgeException(Exception):
    """Base exception for SceneForge application."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SceneForgeException):
    """Raised when input validation fails."""
    pass


class GenerationError(SceneForgeException):
    """Raised when scene generation fails."""
    pass


class BriaAPIError(SceneForgeException):
    """Raised when Bria AI API calls fail."""
    pass


class AgentError(SceneForgeException):
    """Raised when AI agent processing fails."""
    pass


class StorageError(SceneForgeException):
    """Raised when file storage operations fail."""
    pass


class RateLimitError(SceneForgeException):
    """Raised when rate limits are exceeded."""
    pass


class AuthenticationError(SceneForgeException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(SceneForgeException):
    """Raised when authorization fails."""
    pass


class ResourceNotFoundError(SceneForgeException):
    """Raised when requested resource is not found."""
    pass


class ResourceConflictError(SceneForgeException):
    """Raised when resource conflicts occur."""
    pass