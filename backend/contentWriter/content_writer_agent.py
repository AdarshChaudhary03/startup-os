"""Content Writer Agent Implementation

Main implementation of the Content Writer Agent that integrates with LLM providers
to generate high-quality content instead of using dummy data.
"""

import asyncio
import logging
import json
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone

from contentWriter.content_writer_config import ContentWriterConfig, ContentType, ToneOfVoice, DEFAULT_CONFIG
from contentWriter.content_prompts import ContentPrompts
from ai_providers.factory import AIProviderFactory
from ai_providers.base import AIResponse
from ai_providers.exceptions import AIProviderError
from logging_config import log_orchestration_event

logger = logging.getLogger(__name__)


class ContentWriterAgent:
    """Content Writer Agent that generates content using LLM providers."""
    
    def __init__(self, config: Optional[ContentWriterConfig] = None):
        """Initialize the Content Writer Agent.
        
        Args:
            config: Configuration for the agent. Uses default if not provided.
        """
        self.config = config or DEFAULT_CONFIG
        self._ai_provider = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the AI provider for content generation."""
        try:
            # Get AI provider from factory
            self._ai_provider = await AIProviderFactory.get_provider(
                provider_name=self.config.provider
            )
            
            if not self._ai_provider:
                raise AIProviderError(f"Failed to initialize {self.config.provider} provider")
            
            # Test the provider
            health_ok = await self._ai_provider.health_check()
            if not health_ok:
                raise AIProviderError(f"{self.config.provider} provider failed health check")
            
            self._initialized = True
            logger.info(f"Content Writer Agent initialized with {self.config.provider} provider")
            
        except Exception as e:
            logger.error(f"Failed to initialize Content Writer Agent: {e}")
            raise
    
    async def generate_content(
        self,
        task: str,
        request_id: str,
        content_type: Optional[ContentType] = None,
        tone: Optional[ToneOfVoice] = None,
        word_count: Optional[int] = None,
        target_audience: Optional[str] = None,
        key_points: Optional[List[str]] = None,
        seo_keywords: Optional[List[str]] = None,
        brand_voice: Optional[str] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate content based on the task and parameters.
        
        Args:
            task: The content generation task/topic
            request_id: Unique request identifier for logging
            content_type: Type of content to generate
            tone: Tone of voice to use
            word_count: Target word count
            target_audience: Description of target audience
            key_points: Key points to cover
            seo_keywords: SEO keywords to incorporate
            brand_voice: Brand voice guidelines
            additional_instructions: Additional specific instructions
        
        Returns:
            Generated content as string
        
        Raises:
            AIProviderError: If content generation fails
        """
        if not self._initialized:
            await self.initialize()
        
        # Log content generation start
        log_orchestration_event(
            request_id=request_id,
            event_type="content_generation_start",
            agent_id="content_writer",
            message="Starting content generation with LLM",
            additional_data={
                "task_preview": task[:100] + "..." if len(task) > 100 else task,
                "content_type": (content_type or self.config.default_content_type).value,
                "provider": self.config.provider,
                "model": self.config.model
            }
        )
        
        try:
            # Use provided parameters or defaults
            content_type = content_type or self.config.default_content_type
            tone = tone or self.config.default_tone
            word_count = word_count or self.config.default_word_count
            
            # Build the content generation prompt
            prompt = ContentPrompts.build_content_prompt(
                content_type=content_type,
                tone=tone,
                topic=task,
                word_count=word_count,
                target_audience=target_audience,
                key_points=key_points,
                brand_voice=brand_voice or self.config.brand_voice,
                seo_keywords=seo_keywords or self.config.target_keywords,
                additional_instructions=additional_instructions
            )
            
            # Generate content using AI provider
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            content = response.content
            
            # Post-process content if needed
            if self.config.include_seo_metadata:
                content = await self._add_seo_metadata(content, seo_keywords, request_id)
            
            # Log successful generation
            log_orchestration_event(
                request_id=request_id,
                event_type="content_generation_complete",
                agent_id="content_writer",
                message="Content generation completed successfully",
                additional_data={
                    "content_length": len(content),
                    "word_count_estimate": len(content.split()),
                    "model_used": response.model,
                    "provider_used": response.provider,
                    "usage_info": response.usage
                }
            )
            
            return content
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="content_generation_error",
                agent_id="content_writer",
                message=f"Content generation failed: {str(e)}",
                additional_data={
                    "error_type": type(e).__name__,
                    "provider": self.config.provider
                }
            )
            logger.error(f"Content generation failed for request {request_id}: {e}")
            raise AIProviderError(f"Content generation failed: {str(e)}")
    
    async def generate_outline(
        self,
        topic: str,
        content_type: Optional[ContentType] = None,
        request_id: Optional[str] = None
    ) -> str:
        """Generate a content outline.
        
        Args:
            topic: Topic for the outline
            content_type: Type of content
            request_id: Request identifier for logging
        
        Returns:
            Generated outline as string
        """
        if not self._initialized:
            await self.initialize()
        
        content_type = content_type or self.config.default_content_type
        request_id = request_id or f"outline_{datetime.now(timezone.utc).isoformat()}"
        
        try:
            prompt = ContentPrompts.get_outline_prompt(topic, content_type)
            
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=1024  # Outlines are typically shorter
            )
            
            logger.info(f"Generated outline for topic: {topic}")
            return response.content
            
        except Exception as e:
            logger.error(f"Outline generation failed: {e}")
            raise AIProviderError(f"Outline generation failed: {str(e)}")
    
    async def optimize_for_seo(
        self,
        content: str,
        keywords: List[str],
        request_id: Optional[str] = None
    ) -> str:
        """Optimize existing content for SEO.
        
        Args:
            content: Original content to optimize
            keywords: Target keywords
            request_id: Request identifier for logging
        
        Returns:
            SEO-optimized content
        """
        if not self._initialized:
            await self.initialize()
        
        request_id = request_id or f"seo_{datetime.now(timezone.utc).isoformat()}"
        
        try:
            prompt = ContentPrompts.get_seo_optimization_prompt(content, keywords)
            
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=prompt,
                model=self.config.model,
                temperature=0.3,  # Lower temperature for optimization tasks
                max_tokens=self.config.max_tokens
            )
            
            logger.info(f"Optimized content for SEO with keywords: {keywords}")
            return response.content
            
        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            raise AIProviderError(f"SEO optimization failed: {str(e)}")
    
    async def revise_content(
        self,
        content: str,
        feedback: str,
        request_id: Optional[str] = None
    ) -> str:
        """Revise content based on feedback.
        
        Args:
            content: Original content
            feedback: Feedback for improvement
            request_id: Request identifier for logging
        
        Returns:
            Revised content
        """
        if not self._initialized:
            await self.initialize()
        
        request_id = request_id or f"revision_{datetime.now(timezone.utc).isoformat()}"
        
        try:
            prompt = ContentPrompts.get_revision_prompt(content, feedback)
            
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            logger.info(f"Revised content based on feedback")
            return response.content
            
        except Exception as e:
            logger.error(f"Content revision failed: {e}")
            raise AIProviderError(f"Content revision failed: {str(e)}")
    
    async def _add_seo_metadata(
        self,
        content: str,
        keywords: Optional[List[str]],
        request_id: str
    ) -> str:
        """Add SEO metadata to content if enabled.
        
        Args:
            content: Original content
            keywords: SEO keywords
            request_id: Request identifier
        
        Returns:
            Content with SEO metadata
        """
        if not keywords:
            return content
        
        try:
            # Generate meta description and title suggestions
            seo_prompt = f"""
Based on the following content, generate SEO metadata:

Content:
{content[:500]}...

Target keywords: {', '.join(keywords)}

Please provide:
1. SEO-optimized title (under {self.config.title_length_limit} characters)
2. Meta description (under {self.config.meta_description_length} characters)
3. Suggested H1 tag

Format as JSON with keys: title, meta_description, h1_tag
"""
            
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=seo_prompt,
                model=self.config.model,
                temperature=0.3,
                max_tokens=512
            )
            
            # Try to parse SEO metadata
            try:
                seo_data = json.loads(response.content)
                seo_metadata = f"""
<!-- SEO Metadata -->
<!-- Title: {seo_data.get('title', 'N/A')} -->
<!-- Meta Description: {seo_data.get('meta_description', 'N/A')} -->
<!-- H1 Tag: {seo_data.get('h1_tag', 'N/A')} -->
<!-- Target Keywords: {', '.join(keywords)} -->

"""
                return seo_metadata + content
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse SEO metadata JSON for request {request_id}")
                return content
            
        except Exception as e:
            logger.warning(f"Failed to add SEO metadata for request {request_id}: {e}")
            return content
    
    async def get_content_analytics(self, content: str) -> Dict[str, Any]:
        """Analyze content and return metrics.
        
        Args:
            content: Content to analyze
        
        Returns:
            Dictionary with content analytics
        """
        word_count = len(content.split())
        char_count = len(content)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        # Estimate reading time (average 200 words per minute)
        reading_time_minutes = max(1, round(word_count / 200))
        
        analytics = {
            'word_count': word_count,
            'character_count': char_count,
            'paragraph_count': paragraph_count,
            'estimated_reading_time_minutes': reading_time_minutes,
            'meets_min_word_count': word_count >= self.config.min_word_count,
            'within_max_word_count': word_count <= self.config.max_word_count,
            'provider_used': self.config.provider,
            'model_used': self.config.model
        }
        
        return analytics
    
    def update_config(self, new_config: ContentWriterConfig) -> None:
        """Update the agent configuration.
        
        Args:
            new_config: New configuration to use
        """
        self.config = new_config
        # Reset initialization to force provider reload with new config
        self._initialized = False
        self._ai_provider = None
        logger.info("Content Writer Agent configuration updated")
    
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
            logger.error(f"Content Writer Agent health check failed: {e}")
            return False


# Global instance for easy access
_content_writer_agent = None


async def get_content_writer_agent(config: Optional[ContentWriterConfig] = None) -> ContentWriterAgent:
    """Get or create a Content Writer Agent instance.
    
    Args:
        config: Optional configuration. Uses default if not provided.
    
    Returns:
        ContentWriterAgent instance
    """
    global _content_writer_agent
    
    if _content_writer_agent is None or config is not None:
        _content_writer_agent = ContentWriterAgent(config)
        await _content_writer_agent.initialize()
    
    return _content_writer_agent
