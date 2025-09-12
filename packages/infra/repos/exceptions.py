
class RepositoryError(Exception):
    """Base class for repository errors."""

class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""

class NotSoftDeletable(RepositoryError):
    """Raised when soft_delete/restore is called for a model without deleted_at."""
