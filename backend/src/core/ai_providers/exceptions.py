"""AI Provider Exceptions

Custom exceptions for AI provider operations.
"""


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class ProviderInitializationError(AIProviderError):
    """Raised when a provider fails to initialize."""
    pass


class ModelNotSupportedError(AIProviderError):
    """Raised when a requested model is not supported by the provider."""
    pass


class ContentGenerationError(AIProviderError):
    """Raised when content generation fails."""
    pass


class ProviderHealthCheckError(AIProviderError):
    """Raised when provider health check fails."""
    pass


class APIKeyError(AIProviderError):
    """Raised when API key is invalid or missing."""
    pass


class RateLimitError(AIProviderError):
    """Raised when API rate limit is exceeded."""
    pass


class QuotaExceededError(AIProviderError):
    """Raised when API quota is exceeded."""
    pass