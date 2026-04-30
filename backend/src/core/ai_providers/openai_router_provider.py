"""OpenAI Router Provider

Implementation of the OpenAI Router provider for accessing multiple models.
"""

import asyncio
import logging
from typing import List, Dict, Any
import httpx

from .base import BaseAIProvider, AIResponse

logger = logging.getLogger(__name__)


class OpenAIRouterProvider(BaseAIProvider):
    """OpenAI Router provider implementation."""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://openrouter.ai/api/v1')
        self.site_url = kwargs.get('site_url', 'https://your-site.com')
        self.app_name = kwargs.get('app_name', 'AI Startup System')
    
    @property
    def provider_name(self) -> str:
        return "openai_router"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "openai/gpt-4o-mini", 
            "meta-llama/llama-3.1-70b-instruct",
            "google/gemini-pro-1.5",
            "mistralai/mixtral-8x7b-instruct"
        ]
    
    async def initialize(self) -> None:
        """Initialize the OpenAI Router client."""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.app_name
                },
                timeout=60.0
            )
            logger.info("OpenAI Router provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI Router provider: {e}")
            raise
    
    async def generate_content(
        self, 
        prompt: str, 
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """Generate content using OpenAI Router.
        
        Args:
            prompt: Input prompt
            model: Model to use
            **kwargs: Additional parameters
        """
        if not self._client:
            await self.initialize()
        
        if not model:
            model = self.get_default_model()
        
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not supported by OpenAI Router provider")
        
        try:
            # Extract parameters
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 1024)
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Extract usage information
            usage_info = data.get("usage", {})
            
            return AIResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                usage=usage_info,
                metadata={
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI Router content generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check OpenAI Router provider health."""
        try:
            if not self._client:
                await self.initialize()
            
            # Simple test generation
            test_response = await self.generate_content(
                prompt="Hello",
                model=self.get_default_model()
            )
            return bool(test_response.content)
            
        except Exception as e:
            logger.error(f"OpenAI Router health check failed: {e}")
            return False
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup OpenAI Router client."""
        if self._client:
            await self._client.aclose()