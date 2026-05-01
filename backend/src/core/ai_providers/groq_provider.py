"""Groq AI Provider

Implementation of the Groq AI provider.
"""

import asyncio
import logging
from typing import List, Dict, Any
import httpx

from .base import BaseAIProvider, AIResponse

logger = logging.getLogger(__name__)


class GroqProvider(BaseAIProvider):
    """Groq AI provider implementation."""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.groq.com/openai/v1')
    
    @property
    def provider_name(self) -> str:
        return "groq"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
    
    async def initialize(self) -> None:
        """Initialize the Groq client."""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            logger.info("Groq provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq provider: {e}")
            raise
    
    async def generate_content(
        self, 
        prompt: str, 
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """Generate content using Groq.
        
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
            raise ValueError(f"Model {model} not supported by Groq provider")
        
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
            
            # Log the payload for debugging
            logger.debug(f"Groq API payload: {payload}")
            
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
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq HTTP error: Status {e.response.status_code}")
            logger.error(f"Groq error response: {e.response.text}")
            logger.error(f"Groq request payload: {payload}")
            raise
        except Exception as e:
            logger.error(f"Groq content generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Groq provider health."""
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
            logger.error(f"Groq health check failed: {e}")
            return False
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Groq client."""
        if self._client:
            await self._client.aclose()