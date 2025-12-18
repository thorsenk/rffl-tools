"""RFFL exception hierarchy for clean error handling."""


class RFFLError(Exception):
    """Base exception for all RFFL errors."""
    pass


class ESPNAPIError(RFFLError):
    """ESPN API related errors (network, auth, data)."""
    pass


class AuthenticationError(ESPNAPIError):
    """Authentication failure for private leagues."""
    pass


class RateLimitError(ESPNAPIError):
    """Rate limit exceeded."""
    pass


class ValidationError(RFFLError):
    """Data validation errors."""
    pass


class LineupValidationError(ValidationError):
    """RFFL lineup rule violations."""
    pass


class RecipeError(RFFLError):
    """Recipe execution errors."""
    pass


class RecipeLockedError(RecipeError):
    """Attempt to execute locked baseline recipe."""
    pass


class PathResolutionError(RecipeError):
    """Failed to resolve recipe output path."""
    pass

