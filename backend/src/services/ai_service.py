"""AI Service Module

Centralized service for managing AI providers and content generation.
Provides a high-level interface for the application to interact with AI models.
"""

import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from src.core.ai_providers import AIProviderFactory, BaseAIProvider, AIResponse
from src.core.ai_providers.exceptions import (
    AIProviderError, 
    ProviderInitializationError,
    ModelNotSupportedError,
    ContentGenerationError
)

logger = logging.getLogger(__name__)


class AIService:
    """Centralized AI service for managing multiple providers."""
    
    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._default_provider: Optional[str] = None
        self._initialized = False
    
    async def add_provider(
        self, 
        name: str, 
        provider_type: str, 
        api_key: str, 
        is_default: bool = False,
        **kwargs
    ) -> None:
        """Add a new AI provider to the service.
        
        Args:
            name: Unique name for this provider instance
            provider_type: Type of provider (gemini, groq, openai_router)
            api_key: API key for the provider
            is_default: Whether this should be the default provider
            **kwargs: Additional provider-specific configuration
        """
        try:
            provider = AIProviderFactory.create_provider(
                provider_type=provider_type,
                api_key=api_key,
                **kwargs
            )
            
            # Initialize the provider
            await provider.initialize()
            
            self._providers[name] = provider
            
            if is_default or not self._default_provider:
                self._default_provider = name
            
            logger.info(f"Added AI provider '{name}' of type '{provider_type}'")
            
        except Exception as e:
            logger.error(f"Failed to add provider '{name}': {e}")
            raise ProviderInitializationError(f"Failed to add provider '{name}': {e}")
    
    async def remove_provider(self, name: str) -> None:
        """Remove a provider from the service.
        
        Args:
            name: Name of the provider to remove
        """
        if name in self._providers:
            provider = self._providers.pop(name)
            # Cleanup provider if it has an async context manager
            if hasattr(provider, '__aexit__'):
                await provider.__aexit__(None, None, None)
            
            # Update default provider if necessary
            if self._default_provider == name:
                self._default_provider = next(iter(self._providers.keys()), None)
            
            logger.info(f"Removed AI provider '{name}'")
    
    def get_provider(self, name: str = None) -> BaseAIProvider:
        """Get a specific provider or the default provider.
        
        Args:
            name: Name of the provider to get (uses default if None)
            
        Returns:
            BaseAIProvider: The requested provider
            
        Raises:
            ValueError: If provider not found
        """
        if name is None:
            name = self._default_provider
        
        if name is None or name not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(
                f"Provider '{name}' not found. Available providers: {available}"
            )
        
        return self._providers[name]
    
    def list_providers(self) -> Dict[str, str]:
        """List all available providers.
        
        Returns:
            Dict mapping provider names to their types
        """
        return {
            name: provider.provider_name 
            for name, provider in self._providers.items()
        }
    
    def get_default_provider_name(self) -> Optional[str]:
        """Get the name of the default provider."""
        return self._default_provider
    
    def set_default_provider(self, name: str) -> None:
        """Set the default provider.
        
        Args:
            name: Name of the provider to set as default
            
        Raises:
            ValueError: If provider not found
        """
        if name not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(
                f"Provider '{name}' not found. Available providers: {available}"
            )
        
        self._default_provider = name
        logger.info(f"Set default provider to '{name}'")
    
    async def generate_content(
        self,
        prompt: str,
        provider_name: str = None,
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """Generate content using the specified or default provider.
        
        Args:
            prompt: Input prompt for content generation
            provider_name: Name of provider to use (uses default if None)
            model: Specific model to use
            **kwargs: Additional generation parameters
            
        Returns:
            AIResponse: Generated content response
            
        Raises:
            ContentGenerationError: If content generation fails
        """
        try:
            provider = self.get_provider(provider_name)
            
            logger.info(
                f"Generating content with provider '{provider_name or self._default_provider}' "
                f"using model '{model or 'default'}'"
            )
            
            response = await provider.generate_content(
                prompt=prompt,
                model=model,
                **kwargs
            )
            
            logger.info(f"Content generated successfully, length: {len(response.content)}")
            return response
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise ContentGenerationError(f"Content generation failed: {e}")
    
    async def health_check(self, provider_name: str = None) -> Dict[str, bool]:
        """Check health of providers.
        
        Args:
            provider_name: Specific provider to check (checks all if None)
            
        Returns:
            Dict mapping provider names to their health status
        """
        results = {}
        
        if provider_name:
            # Check specific provider
            provider = self.get_provider(provider_name)
            results[provider_name] = await provider.health_check()
        else:
            # Check all providers
            for name, provider in self._providers.items():
                try:
                    results[name] = await provider.health_check()
                except Exception as e:
                    logger.error(f"Health check failed for provider '{name}': {e}")
                    results[name] = False
        
        return results
    
    @asynccontextmanager
    async def provider_context(self, provider_name: str = None):
        """Context manager for using a specific provider.
        
        Args:
            provider_name: Name of provider to use
        """
        provider = self.get_provider(provider_name)
        async with provider:
            yield provider
    
    async def cleanup(self) -> None:
        """Cleanup all providers."""
        for name in list(self._providers.keys()):
            await self.remove_provider(name)
        
        self._default_provider = None
        self._initialized = False
        logger.info("AI service cleanup completed")
    
    def is_initialized(self) -> bool:
        """Check if the service has any providers configured."""
        return bool(self._providers)


# Global AI service instance
ai_service = AIService()