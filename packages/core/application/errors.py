from __future__ import annotations

class AppError(Exception):
    """Base application error."""

class AlreadyExists(AppError):
    """Entity already exists (e.g., email)."""

class AuthenticationError(AppError):
    """Bad credentials or unauthorized."""

class AuthorizationError(AppError):
    """Forbidden action."""

class NotFound(AppError):
    """Entity not found."""
