"""Base AI Provider Interface

Defines the abstract base class that all AI providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class AIResponse(BaseModel):
    """Standardized AI response model."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAIProvider(ABC):
    """Abstract base class for AI providers.
    
    All AI providers must implement this interface to ensure
    consistent behavior across different models and services.
    """
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize the AI provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        self._client = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the AI provider."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported models for this provider."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client and validate configuration."""
        pass
    
    @abstractmethod
    async def generate_content(
        self, 
        prompt: str, 
        model: str,
        **kwargs
    ) -> AIResponse:
        """Generate content using the AI model.
        
        Args:
            prompt: The input prompt for content generation
            model: The specific model to use
            **kwargs: Additional model-specific parameters
            
        Returns:
            AIResponse: Standardized response object
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible.
        
        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass
    
    def get_default_model(self) -> str:
        """Get the default model for this provider.
        
        Returns:
            str: Default model name
        """
        if self.supported_models:
            return self.supported_models[0]
        raise NotImplementedError("No supported models defined")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Cleanup if needed
        pass