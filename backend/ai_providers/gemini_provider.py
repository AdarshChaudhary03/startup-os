"""Gemini AI Provider

Implementation of the Gemini AI provider using google-genai library.
"""

import asyncio
import logging
from typing import List, Dict, Any
import google.genai as genai
from google.genai import types

from .base import BaseAIProvider, AIResponse

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Gemini AI provider implementation."""
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "gemini-2.5-pro",
            "gemini-1.5-pro", 
            "gemini-1.5-flash",
            "gemini-pro"
        ]
    
    async def initialize(self) -> None:
        """Initialize the Gemini client."""
        try:
            self._client = genai.Client(api_key=self.api_key)
            logger.info("Gemini provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini provider: {e}")
            raise
    
    async def generate_content(
        self, 
        prompt: str, 
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """Generate content using Gemini.
        
        Args:
            prompt: Input prompt
            model: Model to use (defaults to gemini-2.5-pro)
            **kwargs: Additional parameters like temperature, max_tokens, etc.
        """
        if not self._client:
            await self.initialize()
        
        if not model:
            model = self.get_default_model()
        
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not supported by Gemini provider")
        
        try:
            # Extract Gemini-specific parameters
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 1024)
            
            # Generate response using the new google.genai API
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=model,
                contents=types.Content(
                    parts=[types.Part(text=prompt)]
                ),
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            
            content = response.candidates[0].content.parts[0].text
            
            # Extract usage information if available
            usage_info = None
            if hasattr(response, 'usage_metadata'):
                usage_info = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
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
            logger.error(f"Gemini content generation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Gemini provider health."""
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
            logger.error(f"Gemini health check failed: {e}")
            return False