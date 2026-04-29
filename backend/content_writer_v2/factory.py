"""Content Agent Factory

Factory pattern implementation for creating appropriate content agents
based on content category and requirements.
"""

import logging
from typing import Dict, Type, Optional, Any
from .config import ContentCategory, ContentWriterV2Config, DEFAULT_CONFIG
# Removed circular import - ContentWriterMainAgent will be imported locally where needed
from .sub_agents import (
    SocialMediaAgent,
    BlogAgent,
    ScriptAgent,
    MarketingCopyAgent,
    TechnicalWritingAgent
)

logger = logging.getLogger(__name__)


class ContentAgentFactory:
    """Factory for creating content generation agents."""
    
    # Registry of available agents
    _agent_registry: Dict[ContentCategory, Type] = {
        ContentCategory.SOCIAL_MEDIA: SocialMediaAgent,
        ContentCategory.BLOG: BlogAgent,
        ContentCategory.SCRIPT: ScriptAgent,
        ContentCategory.MARKETING: MarketingCopyAgent,
        ContentCategory.TECHNICAL: TechnicalWritingAgent,
    }
    
    # Cached agent instances
    _agent_cache: Dict[str, Any] = {}
    
    @classmethod
    async def create_agent(
        cls,
        category: ContentCategory,
        config: Optional[ContentWriterV2Config] = None,
        force_new: bool = False
    ) -> Any:
        """Create or retrieve a content agent for the specified category.
        
        Args:
            category: The content category to create an agent for
            config: Optional configuration. Uses default if not provided.
            force_new: Force creation of new instance instead of using cache
        
        Returns:
            Appropriate content agent instance
        
        Raises:
            ValueError: If category is not supported
        """
        if category not in cls._agent_registry:
            raise ValueError(f"Unsupported content category: {category}")
        
        config = config or DEFAULT_CONFIG
        cache_key = f"{category.value}_{id(config)}"
        
        # Return cached instance if available and not forcing new
        if not force_new and cache_key in cls._agent_cache:
            logger.debug(f"Returning cached agent for category: {category.value}")
            return cls._agent_cache[cache_key]
        
        # Create new agent instance
        agent_class = cls._agent_registry[category]
        agent = agent_class(config)
        
        # Initialize the agent
        await agent.initialize()
        
        # Cache the instance
        cls._agent_cache[cache_key] = agent
        
        logger.info(f"Created new {agent_class.__name__} for category: {category.value}")
        return agent
    
    @classmethod
    async def create_main_agent(
        cls,
        config: Optional[ContentWriterV2Config] = None
    ):
        """Create the main content writer agent that orchestrates sub-agents.
        
        Args:
            config: Optional configuration. Uses default if not provided.
        
        Returns:
            ContentWriterMainAgent instance
        """
        # Import locally to avoid circular import
        from .main_agent import ContentWriterMainAgent
        
        config = config or DEFAULT_CONFIG
        cache_key = f"main_agent_{id(config)}"
        
        if cache_key in cls._agent_cache:
            return cls._agent_cache[cache_key]
        
        main_agent = ContentWriterMainAgent(config)
        await main_agent.initialize()
        
        cls._agent_cache[cache_key] = main_agent
        
        logger.info("Created new ContentWriterMainAgent")
        return main_agent
    
    @classmethod
    def get_supported_categories(cls) -> list[ContentCategory]:
        """Get list of supported content categories.
        
        Returns:
            List of supported ContentCategory values
        """
        return list(cls._agent_registry.keys())
    
    @classmethod
    def register_agent(cls, category: ContentCategory, agent_class: Type) -> None:
        """Register a new agent class for a content category.
        
        Args:
            category: Content category
            agent_class: Agent class to register
        """
        cls._agent_registry[category] = agent_class
        logger.info(f"Registered {agent_class.__name__} for category: {category.value}")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the agent cache."""
        cls._agent_cache.clear()
        logger.info("Agent cache cleared")
    
    @classmethod
    async def get_agent_for_task(cls, task: str, config: Optional[ContentWriterV2Config] = None) -> Any:
        """Automatically determine and create the best agent for a given task.
        
        Args:
            task: Description of the content task
            config: Optional configuration
        
        Returns:
            Appropriate agent for the task
        """
        category = cls._classify_task(task)
        return await cls.create_agent(category, config)
    
    @classmethod
    def _classify_task(cls, task: str) -> ContentCategory:
        """Classify a task to determine the appropriate content category.
        
        Args:
            task: Task description
        
        Returns:
            Appropriate ContentCategory
        """
        task_lower = task.lower()
        
        # Social media keywords
        social_keywords = [
            'instagram', 'twitter', 'linkedin', 'facebook', 'tiktok', 'youtube',
            'caption', 'post', 'story', 'reel', 'hashtag', 'social media'
        ]
        
        # Blog keywords
        blog_keywords = [
            'blog', 'article', 'post', 'write about', 'essay', 'content piece'
        ]
        
        # Script keywords
        script_keywords = [
            'script', 'video', 'reel script', 'youtube script', 'podcast',
            'narration', 'voiceover'
        ]
        
        # Marketing keywords
        marketing_keywords = [
            'marketing', 'ad copy', 'advertisement', 'sales copy', 'promotional',
            'campaign', 'product description', 'landing page'
        ]
        
        # Technical keywords
        technical_keywords = [
            'technical', 'documentation', 'api', 'guide', 'tutorial',
            'how-to', 'manual', 'specification'
        ]
        
        # Check for matches
        if any(keyword in task_lower for keyword in social_keywords):
            return ContentCategory.SOCIAL_MEDIA
        elif any(keyword in task_lower for keyword in script_keywords):
            return ContentCategory.SCRIPT
        elif any(keyword in task_lower for keyword in marketing_keywords):
            return ContentCategory.MARKETING
        elif any(keyword in task_lower for keyword in technical_keywords):
            return ContentCategory.TECHNICAL
        elif any(keyword in task_lower for keyword in blog_keywords):
            return ContentCategory.BLOG
        
        # Default to blog for general content creation
        return ContentCategory.BLOG