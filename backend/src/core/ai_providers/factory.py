"""AI Provider Factory

Factory class for creating AI provider instances based on configuration.
"""

import logging
from typing import Dict, Type, Optional
from enum import Enum

from .base import BaseAIProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .openai_router_provider import OpenAIRouterProvider

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported AI provider types."""
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI_ROUTER = "openai_router"


class AIProviderFactory:
    """Factory for creating AI provider instances."""
    
    _providers: Dict[str, Type[BaseAIProvider]] = {
        ProviderType.GEMINI: GeminiProvider,
        ProviderType.GROQ: GroqProvider,
        ProviderType.OPENAI_ROUTER: OpenAIRouterProvider,
    }
    
    _provider_instances: Dict[str, BaseAIProvider] = {}
    
    @classmethod
    def create_provider(
        cls, 
        provider_type: str, 
        api_key: str, 
        **kwargs
    ) -> BaseAIProvider:
        """Create an AI provider instance.
        
        Args:
            provider_type: Type of provider to create
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
            
        Returns:
            BaseAIProvider: Configured provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Available providers: {available}"
            )
        
        provider_class = cls._providers[provider_type]
        logger.info(f"Creating {provider_type} provider instance")
        
        return provider_class(api_key=api_key, **kwargs)
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider types.
        
        Returns:
            List of supported provider type strings
        """
        return list(cls._providers.keys())
    
    @classmethod
    async def get_provider(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Optional[BaseAIProvider]:
        """Get or create a provider instance.
        
        Args:
            provider_name: Name/type of the provider
            api_key: API key for the provider (if not already cached)
            **kwargs: Additional provider configuration
            
        Returns:
            BaseAIProvider instance or None if creation fails
        """
        # Check if provider is already cached
        if provider_name in cls._provider_instances:
            return cls._provider_instances[provider_name]
        
        # Create new provider instance
        try:
            if api_key is None:
                # Try to get API key from environment
                from ..config import GEMINI_API_KEY, GROQ_API_KEY, OPENAI_ROUTER_API_KEY
                
                if provider_name == "gemini":
                    api_key = GEMINI_API_KEY
                elif provider_name == "groq":
                    api_key = GROQ_API_KEY
                elif provider_name == "openai_router":
                    api_key = OPENAI_ROUTER_API_KEY
                
                if not api_key:
                    logger.error(f"No API key found for provider: {provider_name}")
                    return None
            
            provider = cls.create_provider(provider_name, api_key, **kwargs)
            
            # Initialize the provider
            await provider.initialize()
            
            # Cache the provider
            cls._provider_instances[provider_name] = provider
            
            logger.info(f"Successfully created and cached provider: {provider_name}")
            return provider
            
        except Exception as e:
            logger.error(f"Failed to create provider {provider_name}: {e}")
            return None
    
    @classmethod
    def register_provider(
        cls, 
        provider_type: str, 
        provider_class: Type[BaseAIProvider]
    ) -> None:
        """Register a new provider type.
        
        Args:
            provider_type: Unique identifier for the provider
            provider_class: Provider class that implements BaseAIProvider
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise ValueError(
                f"Provider class must inherit from BaseAIProvider"
            )
        
        cls._providers[provider_type] = provider_class
        logger.info(f"Registered new provider: {provider_type}")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the provider instance cache."""
        cls._provider_instances.clear()
        logger.info("Provider cache cleared")