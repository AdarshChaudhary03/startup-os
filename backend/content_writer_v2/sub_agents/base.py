"""Base Content Agent

Abstract base class for all content generation sub-agents.
Defines the common interface and shared functionality.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone

from ..config import ContentWriterV2Config, DEFAULT_CONFIG
from ai_providers.factory import AIProviderFactory
from ai_providers.base import AIResponse
from ai_providers.exceptions import AIProviderError
from logging_config import log_orchestration_event

logger = logging.getLogger(__name__)


class BaseContentAgent(ABC):
    """Abstract base class for all content generation agents."""
    
    def __init__(self, config: Optional[ContentWriterV2Config] = None):
        """Initialize the base content agent.
        
        Args:
            config: Configuration for the agent
        """
        self.config = config or DEFAULT_CONFIG
        self._ai_provider = None
        self._initialized = False
        self.agent_type = self.__class__.__name__
    
    async def initialize(self) -> None:
        """Initialize the AI provider for content generation."""
        try:
            # Get AI provider from factory
            self._ai_provider = await AIProviderFactory.get_provider(
                provider_name=self.config.ai_provider.provider
            )
            
            if not self._ai_provider:
                raise AIProviderError(f"Failed to initialize {self.config.ai_provider.provider} provider")
            
            # Test the provider
            health_ok = await self._ai_provider.health_check()
            if not health_ok:
                raise AIProviderError(f"{self.config.ai_provider.provider} provider failed health check")
            
            self._initialized = True
            logger.info(f"{self.agent_type} initialized with {self.config.ai_provider.provider} provider")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_type}: {e}")
            raise
    
    @abstractmethod
    async def generate_content(
        self,
        task: str,
        request_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate content based on the task and parameters.
        
        Args:
            task: The content generation task/topic
            request_id: Unique request identifier for logging
            **kwargs: Additional parameters specific to the agent
        
        Returns:
            Dictionary containing generated content and metadata
        
        Raises:
            AIProviderError: If content generation fails
        """
        pass
    
    async def _generate_with_provider(
        self,
        prompt: str,
        request_id: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Generate content using the AI provider.
        
        Args:
            prompt: The prompt to send to the AI provider
            request_id: Request identifier for logging
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider parameters
        
        Returns:
            AIResponse from the provider
        
        Raises:
            AIProviderError: If generation fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=prompt,
                model=self.config.ai_provider.model,
                temperature=temperature or self.config.ai_provider.temperature,
                max_tokens=max_tokens or self.config.ai_provider.max_tokens,
                **kwargs
            )
            
            # Log successful generation
            log_orchestration_event(
                request_id=request_id,
                event_type="ai_generation_success",
                agent_id=self.agent_type.lower(),
                message=f"Content generated successfully by {self.agent_type}",
                additional_data={
                    "model_used": response.model,
                    "provider_used": response.provider,
                    "content_length": len(response.content),
                    "usage_info": response.usage
                }
            )
            
            return response
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="ai_generation_error",
                agent_id=self.agent_type.lower(),
                message=f"Content generation failed in {self.agent_type}: {str(e)}",
                additional_data={
                    "error_type": type(e).__name__,
                    "provider": self.config.ai_provider.provider
                }
            )
            logger.error(f"Content generation failed in {self.agent_type} for request {request_id}: {e}")
            raise AIProviderError(f"Content generation failed: {str(e)}")
    
    def _build_base_prompt(
        self,
        task: str,
        system_prompt: str,
        additional_instructions: Optional[str] = None,
        brand_context: Optional[str] = None,
        target_audience: Optional[str] = None
    ) -> str:
        """Build a base prompt with common elements.
        
        Args:
            task: The main task description
            system_prompt: System prompt for the agent
            additional_instructions: Additional specific instructions
            brand_context: Brand context and guidelines
            target_audience: Target audience description
        
        Returns:
            Complete prompt string
        """
        prompt_parts = [system_prompt]
        
        # Add brand context if available
        if brand_context or self.config.brand_voice:
            brand_info = brand_context or self.config.brand_voice
            prompt_parts.append(f"Brand Voice & Guidelines: {brand_info}")
        
        # Add target audience if available
        if target_audience or self.config.target_audience:
            audience_info = target_audience or self.config.target_audience
            prompt_parts.append(f"Target Audience: {audience_info}")
        
        # Add main task
        prompt_parts.append(f"Task: {task}")
        
        # Add additional instructions if provided
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        return "\n\n".join(prompt_parts)
    
    def _extract_content_metadata(self, content: str, **kwargs) -> Dict[str, Any]:
        """Extract metadata from generated content.
        
        Args:
            content: Generated content
            **kwargs: Additional metadata
        
        Returns:
            Metadata dictionary
        """
        word_count = len(content.split())
        char_count = len(content)
        line_count = len(content.split('\n'))
        
        metadata = {
            "word_count": word_count,
            "character_count": char_count,
            "line_count": line_count,
            "estimated_reading_time_minutes": max(1, round(word_count / 200)),
            "agent_type": self.agent_type,
            "provider_used": self.config.ai_provider.provider,
            "model_used": self.config.ai_provider.model,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
        
        return metadata
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready to generate content.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            if not self._ai_provider:
                return False
            
            return await self._ai_provider.health_check()
            
        except Exception as e:
            logger.error(f"{self.agent_type} health check failed: {e}")
            return False
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the agent.
        
        Returns:
            Agent information dictionary
        """
        return {
            "agent_type": self.agent_type,
            "provider": self.config.ai_provider.provider,
            "model": self.config.ai_provider.model,
            "initialized": self._initialized,
            "config": {
                "temperature": self.config.ai_provider.temperature,
                "max_tokens": self.config.ai_provider.max_tokens,
                "brand_name": self.config.brand_name,
                "target_audience": self.config.target_audience
            }
        }
    
    async def validate_content(
        self,
        content: str,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate generated content against rules.
        
        Args:
            content: Content to validate
            validation_rules: Optional validation rules
        
        Returns:
            Validation results
        """
        if not self.config.enable_content_validation:
            return {"valid": True, "warnings": [], "errors": []}
        
        warnings = []
        errors = []
        
        # Basic validation
        if not content or not content.strip():
            errors.append("Content is empty")
        
        # Length validation (if rules provided)
        if validation_rules:
            min_length = validation_rules.get("min_length")
            max_length = validation_rules.get("max_length")
            
            if min_length and len(content) < min_length:
                errors.append(f"Content too short (minimum {min_length} characters)")
            
            if max_length and len(content) > max_length:
                errors.append(f"Content too long (maximum {max_length} characters)")
        
        # Check for placeholder text
        placeholders = ["[INSERT", "TODO", "PLACEHOLDER", "XXX"]
        for placeholder in placeholders:
            if placeholder in content.upper():
                warnings.append(f"Content contains placeholder: {placeholder}")
        
        return {
            "valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "content_length": len(content),
            "word_count": len(content.split())
        }