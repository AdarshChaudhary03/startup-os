"""Content Writer Main Agent

Main orchestrator agent that manages and coordinates sub-agents
for different content types and use cases.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone

from .config import (
    ContentWriterV2Config, 
    ContentCategory, 
    SocialPlatform, 
    ContentFormat,
    ToneStyle,
    DEFAULT_CONFIG
)
from .factory import ContentAgentFactory
from .sub_agents.base import BaseContentAgent
from ai_providers.factory import AIProviderFactory
from ai_providers.base import AIResponse
from ai_providers.exceptions import AIProviderError
from logging_config import log_orchestration_event

logger = logging.getLogger(__name__)


class ContentWriterMainAgent:
    """Main Content Writer Agent that orchestrates specialized sub-agents."""
    
    def __init__(self, config: Optional[ContentWriterV2Config] = None):
        """Initialize the main content writer agent.
        
        Args:
            config: Configuration for the agent system
        """
        self.config = config or DEFAULT_CONFIG
        self._ai_provider = None
        self._sub_agents: Dict[ContentCategory, BaseContentAgent] = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the main agent and AI provider."""
        try:
            # Initialize AI provider
            self._ai_provider = await AIProviderFactory.get_provider(
                provider_name=self.config.ai_provider.provider
            )
            
            if not self._ai_provider:
                raise AIProviderError(f"Failed to initialize {self.config.ai_provider.provider} provider")
            
            # Test provider health
            health_ok = await self._ai_provider.health_check()
            if not health_ok:
                raise AIProviderError(f"{self.config.ai_provider.provider} provider failed health check")
            
            self._initialized = True
            logger.info(f"Content Writer Main Agent initialized with {self.config.ai_provider.provider} provider")
            
        except Exception as e:
            logger.error(f"Failed to initialize Content Writer Main Agent: {e}")
            raise
    
    async def generate_content(
        self,
        task: str,
        request_id: str,
        category: Optional[ContentCategory] = None,
        platform: Optional[SocialPlatform] = None,
        content_format: Optional[ContentFormat] = None,
        tone: Optional[ToneStyle] = None,
        word_count: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        target_audience: Optional[str] = None,
        brand_context: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate content using the appropriate sub-agent.
        
        Args:
            task: Content generation task description
            request_id: Unique request identifier
            category: Content category (auto-detected if not provided)
            platform: Target platform (for social media content)
            content_format: Specific content format
            tone: Tone and style
            word_count: Target word count
            duration_seconds: Target duration for scripts
            target_audience: Target audience description
            brand_context: Brand context and guidelines
            additional_instructions: Additional specific instructions
            **kwargs: Additional parameters for specific agents
        
        Returns:
            Dictionary containing generated content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Log content generation start
        log_orchestration_event(
            request_id=request_id,
            event_type="content_generation_start",
            agent_id="content_writer_main",
            message="Starting content generation with Main Agent",
            additional_data={
                "task_preview": task[:100] + "..." if len(task) > 100 else task,
                "category": category.value if category else "auto-detect",
                "platform": platform.value if platform else None,
                "format": content_format.value if content_format else None
            }
        )
        
        try:
            # Auto-detect category if not provided
            if not category:
                category = await self._classify_content_task(task, request_id)
            
            # Get or create appropriate sub-agent
            sub_agent = await self._get_sub_agent(category)
            
            # Prepare parameters for sub-agent
            agent_params = {
                "task": task,
                "request_id": request_id,
                "platform": platform,
                "content_format": content_format,
                "tone": tone,
                "word_count": word_count,
                "duration_seconds": duration_seconds,
                "target_audience": target_audience or self.config.target_audience,
                "brand_context": brand_context or self.config.brand_voice,
                "additional_instructions": additional_instructions,
                **kwargs
            }
            
            # Remove None values
            agent_params = {k: v for k, v in agent_params.items() if v is not None}
            
            # Generate content using sub-agent
            result = await sub_agent.generate_content(**agent_params)
            
            # Add metadata
            result.update({
                "main_agent_version": "2.0.0",
                "category_used": category.value,
                "sub_agent_used": sub_agent.__class__.__name__,
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id
            })
            
            # Log successful generation
            log_orchestration_event(
                request_id=request_id,
                event_type="content_generation_complete",
                agent_id="content_writer_main",
                message="Content generation completed successfully",
                additional_data={
                    "category_used": category.value,
                    "sub_agent_used": sub_agent.__class__.__name__,
                    "content_length": len(result.get("content", "")),
                    "has_metadata": "metadata" in result
                }
            )
            
            return result
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="content_generation_error",
                agent_id="content_writer_main",
                message=f"Content generation failed: {str(e)}",
                additional_data={
                    "error_type": type(e).__name__,
                    "category": category.value if category else None
                }
            )
            logger.error(f"Content generation failed for request {request_id}: {e}")
            raise AIProviderError(f"Content generation failed: {str(e)}")
    
    async def _classify_content_task(self, task: str, request_id: str) -> ContentCategory:
        """Classify the content task to determine appropriate category.
        
        Args:
            task: Task description
            request_id: Request identifier for logging
        
        Returns:
            Appropriate ContentCategory
        """
        # Use factory's classification logic
        category = ContentAgentFactory._classify_task(task)
        
        log_orchestration_event(
            request_id=request_id,
            event_type="task_classification",
            agent_id="content_writer_main",
            message=f"Task classified as: {category.value}",
            additional_data={
                "task_preview": task[:100] + "..." if len(task) > 100 else task,
                "classified_category": category.value
            }
        )
        
        return category
    
    async def _get_sub_agent(self, category: ContentCategory) -> BaseContentAgent:
        """Get or create a sub-agent for the specified category.
        
        Args:
            category: Content category
        
        Returns:
            Appropriate sub-agent instance
        """
        if category not in self._sub_agents:
            self._sub_agents[category] = await ContentAgentFactory.create_agent(
                category=category,
                config=self.config
            )
        
        return self._sub_agents[category]
    
    async def get_content_suggestions(
        self,
        topic: str,
        category: Optional[ContentCategory] = None,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Get content suggestions for a given topic.
        
        Args:
            topic: Topic to generate suggestions for
            category: Content category (auto-detected if not provided)
            count: Number of suggestions to generate
        
        Returns:
            List of content suggestions
        """
        if not self._initialized:
            await self.initialize()
        
        if not category:
            category = ContentAgentFactory._classify_task(topic)
        
        sub_agent = await self._get_sub_agent(category)
        
        if hasattr(sub_agent, 'get_content_suggestions'):
            return await sub_agent.get_content_suggestions(topic, count)
        
        # Fallback to basic suggestions
        return await self._generate_basic_suggestions(topic, category, count)
    
    async def _generate_basic_suggestions(self, topic: str, category: ContentCategory, count: int) -> List[Dict[str, Any]]:
        """Generate basic content suggestions using the main AI provider.
        
        Args:
            topic: Topic for suggestions
            category: Content category
            count: Number of suggestions
        
        Returns:
            List of suggestions
        """
        prompt = f"""
Generate {count} creative content ideas for the topic: {topic}

Content category: {category.value.replace('_', ' ')}

For each idea, provide:
1. A compelling title/headline
2. A brief description (1-2 sentences)
3. Target audience
4. Key angle or hook

Format as JSON array with objects containing: title, description, audience, angle
"""
        
        try:
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=prompt,
                model=self.config.ai_provider.model,
                temperature=0.8,
                max_tokens=1024
            )
            
            # Try to parse JSON response
            import json
            suggestions = json.loads(response.content)
            
            if isinstance(suggestions, list):
                return suggestions[:count]
            
        except Exception as e:
            logger.warning(f"Failed to generate structured suggestions: {e}")
        
        # Fallback to simple suggestions
        return [
            {
                "title": f"Content Idea {i+1} for {topic}",
                "description": f"Create engaging {category.value.replace('_', ' ')} content about {topic}",
                "audience": "General audience",
                "angle": "Informative and engaging"
            }
            for i in range(count)
        ]
    
    async def analyze_content_performance(
        self,
        content: str,
        category: ContentCategory,
        platform: Optional[SocialPlatform] = None
    ) -> Dict[str, Any]:
        """Analyze content for potential performance metrics.
        
        Args:
            content: Content to analyze
            category: Content category
            platform: Platform (for social media content)
        
        Returns:
            Analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        sub_agent = await self._get_sub_agent(category)
        
        if hasattr(sub_agent, 'analyze_content'):
            return await sub_agent.analyze_content(content, platform)
        
        # Basic analysis
        word_count = len(content.split())
        char_count = len(content)
        
        return {
            "word_count": word_count,
            "character_count": char_count,
            "estimated_reading_time_minutes": max(1, round(word_count / 200)),
            "category": category.value,
            "platform": platform.value if platform else None
        }
    
    async def health_check(self) -> bool:
        """Check if the main agent and its components are healthy.
        
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
            logger.error(f"Content Writer Main Agent health check failed: {e}")
            return False
    
    def get_supported_categories(self) -> List[ContentCategory]:
        """Get list of supported content categories.
        
        Returns:
            List of supported categories
        """
        return ContentAgentFactory.get_supported_categories()
    
    async def clear_cache(self) -> None:
        """Clear cached sub-agents."""
        self._sub_agents.clear()
        ContentAgentFactory.clear_cache()
        logger.info("Content Writer Main Agent cache cleared")