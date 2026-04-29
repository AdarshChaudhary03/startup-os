"""Content Writer Service

Service layer for integrating the Content Writer Agent with the main orchestration system.
This service replaces dummy data generation with real LLM-powered content creation.
"""

import asyncio
import logging
from typing import Dict, Optional, Any

from contentWriter.content_writer_agent import get_content_writer_agent, ContentWriterAgent
from contentWriter.content_writer_config import ContentWriterConfig, ContentType, ToneOfVoice
from logging_config import log_orchestration_event

logger = logging.getLogger(__name__)


class ContentWriterService:
    """Service for Content Writer Agent integration with orchestration system."""
    
    def __init__(self):
        self._agent: Optional[ContentWriterAgent] = None
    
    async def initialize(self, config: Optional[ContentWriterConfig] = None) -> None:
        """Initialize the Content Writer Service.
        
        Args:
            config: Optional configuration for the Content Writer Agent
        """
        try:
            self._agent = await get_content_writer_agent(config)
            logger.info("Content Writer Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Content Writer Service: {e}")
            raise
    
    async def execute_content_task(
        self,
        task: str,
        request_id: str,
        agent_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute a content writing task using the LLM-powered agent.
        
        This method replaces the dummy data generation in utils.py execute_task_dummy
        for the content_writer agent.
        
        Args:
            task: The content writing task description
            request_id: Unique request identifier for logging
            agent_config: Optional configuration overrides
        
        Returns:
            Generated content as string
        """
        if not self._agent:
            await self.initialize()
        
        # Log task execution start
        log_orchestration_event(
            request_id=request_id,
            event_type="content_writer_execution_start",
            agent_id="content_writer",
            message="Starting Content Writer Agent execution with LLM",
            additional_data={
                "task_preview": task[:100] + "..." if len(task) > 100 else task,
                "has_config_overrides": bool(agent_config)
            }
        )
        
        try:
            # Parse task to extract content parameters
            content_params = self._parse_task_parameters(task, agent_config)
            
            # Generate content using the agent
            content = await self._agent.generate_content(
                task=task,
                request_id=request_id,
                **content_params
            )
            
            # Log successful execution
            log_orchestration_event(
                request_id=request_id,
                event_type="content_writer_execution_complete",
                agent_id="content_writer",
                message="Content Writer Agent execution completed successfully",
                additional_data={
                    "content_length": len(content),
                    "word_count": len(content.split()),
                    "content_type": content_params.get('content_type', 'blog_post')
                }
            )
            
            return content
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="content_writer_execution_error",
                agent_id="content_writer",
                message=f"Content Writer Agent execution failed: {str(e)}",
                additional_data={
                    "error_type": type(e).__name__
                }
            )
            logger.error(f"Content Writer task execution failed for request {request_id}: {e}")
            
            # Return a fallback message instead of raising to maintain orchestration flow
            return f"Content generation temporarily unavailable. Task: {task[:100]}..."
    
    def _parse_task_parameters(
        self,
        task: str,
        agent_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Parse task description to extract content generation parameters.
        
        Args:
            task: Task description
            agent_config: Optional configuration overrides
        
        Returns:
            Dictionary of parameters for content generation
        """
        params = {}
        task_lower = task.lower()
        
        # Detect content type from task description
        if any(keyword in task_lower for keyword in ['blog', 'post', 'article']):
            params['content_type'] = ContentType.BLOG_POST
        elif any(keyword in task_lower for keyword in ['newsletter', 'email']):
            params['content_type'] = ContentType.NEWSLETTER
        elif any(keyword in task_lower for keyword in ['story', 'narrative']):
            params['content_type'] = ContentType.STORY
        elif any(keyword in task_lower for keyword in ['social', 'tweet', 'post']):
            params['content_type'] = ContentType.SOCIAL_COPY
        elif any(keyword in task_lower for keyword in ['marketing', 'ad', 'copy']):
            params['content_type'] = ContentType.MARKETING_COPY
        elif any(keyword in task_lower for keyword in ['long-form', 'comprehensive']):
            params['content_type'] = ContentType.LONG_FORM
        elif any(keyword in task_lower for keyword in ['technical', 'documentation']):
            params['content_type'] = ContentType.TECHNICAL_DOCUMENTATION
        elif any(keyword in task_lower for keyword in ['product', 'description']):
            params['content_type'] = ContentType.PRODUCT_DESCRIPTION
        else:
            params['content_type'] = ContentType.BLOG_POST  # Default
        
        # Detect tone from task description
        if any(keyword in task_lower for keyword in ['professional', 'formal']):
            params['tone'] = ToneOfVoice.PROFESSIONAL
        elif any(keyword in task_lower for keyword in ['casual', 'informal']):
            params['tone'] = ToneOfVoice.CASUAL
        elif any(keyword in task_lower for keyword in ['friendly', 'warm']):
            params['tone'] = ToneOfVoice.FRIENDLY
        elif any(keyword in task_lower for keyword in ['authoritative', 'expert']):
            params['tone'] = ToneOfVoice.AUTHORITATIVE
        elif any(keyword in task_lower for keyword in ['conversational', 'chat']):
            params['tone'] = ToneOfVoice.CONVERSATIONAL
        elif any(keyword in task_lower for keyword in ['technical', 'precise']):
            params['tone'] = ToneOfVoice.TECHNICAL
        elif any(keyword in task_lower for keyword in ['creative', 'imaginative']):
            params['tone'] = ToneOfVoice.CREATIVE
        elif any(keyword in task_lower for keyword in ['persuasive', 'convincing']):
            params['tone'] = ToneOfVoice.PERSUASIVE
        elif any(keyword in task_lower for keyword in ['engaging', 'dynamic']):
            params['tone'] = ToneOfVoice.ENGAGING
        else:
            params['tone'] = ToneOfVoice.PROFESSIONAL  # Default
        
        # Extract word count if mentioned
        import re
        word_count_match = re.search(r'(\d+)[\s-]*word', task_lower)
        if word_count_match:
            params['word_count'] = int(word_count_match.group(1))
        
        # Extract target audience if mentioned
        audience_keywords = {
            'startup': 'startup founders and entrepreneurs',
            'developer': 'software developers and engineers',
            'business': 'business professionals and decision makers',
            'consumer': 'general consumers and end users',
            'technical': 'technical professionals and experts',
            'marketing': 'marketing professionals and teams'
        }
        
        for keyword, audience in audience_keywords.items():
            if keyword in task_lower:
                params['target_audience'] = audience
                break
        
        # Apply configuration overrides
        if agent_config:
            params.update(agent_config)
        
        return params
    
    async def generate_outline(self, topic: str, request_id: str) -> str:
        """Generate a content outline.
        
        Args:
            topic: Topic for the outline
            request_id: Request identifier
        
        Returns:
            Generated outline
        """
        if not self._agent:
            await self.initialize()
        
        try:
            return await self._agent.generate_outline(topic, request_id=request_id)
        except Exception as e:
            logger.error(f"Outline generation failed: {e}")
            return f"Outline generation temporarily unavailable for topic: {topic}"
    
    async def optimize_content_for_seo(
        self,
        content: str,
        keywords: list,
        request_id: str
    ) -> str:
        """Optimize content for SEO.
        
        Args:
            content: Original content
            keywords: Target keywords
            request_id: Request identifier
        
        Returns:
            SEO-optimized content
        """
        if not self._agent:
            await self.initialize()
        
        try:
            return await self._agent.optimize_for_seo(content, keywords, request_id)
        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            return content  # Return original content if optimization fails
    
    async def health_check(self) -> bool:
        """Check service health.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._agent:
                await self.initialize()
            
            return await self._agent.health_check()
        except Exception as e:
            logger.error(f"Content Writer Service health check failed: {e}")
            return False


# Global service instance
_content_writer_service = None


async def get_content_writer_service() -> ContentWriterService:
    """Get or create the Content Writer Service instance.
    
    Returns:
        ContentWriterService instance
    """
    global _content_writer_service
    
    if _content_writer_service is None:
        _content_writer_service = ContentWriterService()
        await _content_writer_service.initialize()
    
    return _content_writer_service
