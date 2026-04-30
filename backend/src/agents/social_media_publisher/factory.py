"""Social Media Agent Factory

Factory pattern implementation for creating appropriate social media agents
based on platform and requirements.
"""

import logging
from typing import Dict, Type, Optional, Any, List
from .config import SocialPlatform, SocialMediaPublisherConfig, DEFAULT_CONFIG
from .sub_agents import (
    InstagramAgent,
    LinkedInAgent,
    FacebookAgent
)

logger = logging.getLogger(__name__)


class SocialMediaAgentFactory:
    """Factory for creating social media publishing agents."""
    
    # Registry of available agents
    _agent_registry: Dict[SocialPlatform, Type] = {
        SocialPlatform.INSTAGRAM: InstagramAgent,
        SocialPlatform.LINKEDIN: LinkedInAgent,
        SocialPlatform.FACEBOOK: FacebookAgent,
        # Future platforms can be added here
        # SocialPlatform.TWITTER: TwitterAgent,
        # SocialPlatform.TIKTOK: TikTokAgent,
    }
    
    # Cached agent instances
    _agent_cache: Dict[str, Any] = {}
    
    @classmethod
    async def create_agent(
        cls,
        platform: SocialPlatform,
        config: Optional[SocialMediaPublisherConfig] = None,
        force_new: bool = False
    ) -> Any:
        """Create or retrieve a social media agent for the specified platform.
        
        Args:
            platform: The social media platform to create an agent for
            config: Optional configuration. Uses default if not provided.
            force_new: Force creation of new instance instead of using cache
        
        Returns:
            Appropriate social media agent instance
        
        Raises:
            ValueError: If platform is not supported or not enabled
        """
        if platform not in cls._agent_registry:
            raise ValueError(f"Unsupported social media platform: {platform}")
        
        config = config or DEFAULT_CONFIG
        
        # Check if platform is enabled
        if not config.is_platform_enabled(platform):
            raise ValueError(f"Platform {platform.value} is not enabled in configuration")
        
        cache_key = f"{platform.value}_{id(config)}"
        
        # Return cached instance if available and not forcing new
        if not force_new and cache_key in cls._agent_cache:
            logger.debug(f"Returning cached agent for platform: {platform.value}")
            return cls._agent_cache[cache_key]
        
        # Create new agent instance
        agent_class = cls._agent_registry[platform]
        agent = agent_class(config)
        
        # Initialize the agent
        await agent.initialize()
        
        # Cache the instance
        cls._agent_cache[cache_key] = agent
        
        logger.info(f"Created new {agent_class.__name__} for platform: {platform.value}")
        return agent
    
    @classmethod
    async def create_main_agent(
        cls,
        config: Optional[SocialMediaPublisherConfig] = None
    ):
        """Create the main social media publisher agent that orchestrates sub-agents.
        
        Args:
            config: Optional configuration. Uses default if not provided.
        
        Returns:
            SocialMediaPublisherMainAgent instance
        """
        # Import locally to avoid circular import
        from .main_agent import SocialMediaPublisherMainAgent
        
        config = config or DEFAULT_CONFIG
        cache_key = f"main_agent_{id(config)}"
        
        if cache_key in cls._agent_cache:
            return cls._agent_cache[cache_key]
        
        main_agent = SocialMediaPublisherMainAgent(config)
        await main_agent.initialize()
        
        cls._agent_cache[cache_key] = main_agent
        
        logger.info("Created new SocialMediaPublisherMainAgent")
        return main_agent
    
    @classmethod
    def get_supported_platforms(cls) -> List[SocialPlatform]:
        """Get list of supported social media platforms.
        
        Returns:
            List of supported SocialPlatform values
        """
        return list(cls._agent_registry.keys())
    
    @classmethod
    def register_agent(cls, platform: SocialPlatform, agent_class: Type) -> None:
        """Register a new agent class for a social media platform.
        
        Args:
            platform: Social media platform
            agent_class: Agent class to register
        """
        cls._agent_registry[platform] = agent_class
        logger.info(f"Registered {agent_class.__name__} for platform: {platform.value}")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the agent cache."""
        cls._agent_cache.clear()
        logger.info("Social media agent cache cleared")
    
    @classmethod
    async def get_agent_for_task(cls, task: str, config: Optional[SocialMediaPublisherConfig] = None) -> Any:
        """Automatically determine and create the best agent for a given task.
        
        Args:
            task: Description of the social media task
            config: Optional configuration
        
        Returns:
            Appropriate agent for the task
        """
        platform = cls._classify_task(task)
        return await cls.create_agent(platform, config)
    
    @classmethod
    def _classify_task(cls, task: str) -> SocialPlatform:
        """Classify a task to determine the appropriate social media platform.
        
        Args:
            task: Task description
        
        Returns:
            Appropriate SocialPlatform
        """
        task_lower = task.lower()
        
        # Instagram keywords
        instagram_keywords = [
            'instagram', 'insta', 'ig', 'story', 'stories', 'reel', 'reels',
            'hashtag', 'hashtags', 'feed post', 'carousel', 'igtv'
        ]
        
        # LinkedIn keywords
        linkedin_keywords = [
            'linkedin', 'professional', 'business', 'career', 'networking',
            'article', 'professional post', 'company update', 'industry',
            'b2b', 'corporate', 'work', 'job', 'professional development'
        ]
        
        # Facebook keywords
        facebook_keywords = [
            'facebook', 'fb', 'event', 'community', 'group', 'page',
            'family', 'friends', 'local', 'neighborhood', 'poll'
        ]
        
        # Platform-specific posting keywords
        posting_keywords = [
            'post', 'publish', 'share', 'upload', 'schedule', 'distribute'
        ]
        
        # Check for specific platform mentions first
        if any(keyword in task_lower for keyword in instagram_keywords):
            return SocialPlatform.INSTAGRAM
        elif any(keyword in task_lower for keyword in linkedin_keywords):
            return SocialPlatform.LINKEDIN
        elif any(keyword in task_lower for keyword in facebook_keywords):
            return SocialPlatform.FACEBOOK
        
        # If no specific platform mentioned, check for content type indicators
        if any(keyword in task_lower for keyword in posting_keywords):
            # Default to Instagram for general social media posting
            return SocialPlatform.INSTAGRAM
        
        # Default platform
        return SocialPlatform.INSTAGRAM
    
    @classmethod
    def get_platform_capabilities(cls, platform: SocialPlatform) -> Dict[str, Any]:
        """Get capabilities and features supported by a platform.
        
        Args:
            platform: Social media platform
        
        Returns:
            Dictionary of platform capabilities
        """
        capabilities = {
            SocialPlatform.INSTAGRAM: {
                "post_types": ["text_post", "image_post", "story", "reel", "carousel"],
                "media_types": ["image", "video"],
                "max_images": 10,
                "max_video_duration": 60,
                "supports_hashtags": True,
                "max_hashtags": 30,
                "supports_scheduling": True,
                "supports_stories": True,
                "supports_reels": True,
                "character_limit": 2200
            },
            SocialPlatform.LINKEDIN: {
                "post_types": ["text_post", "image_post", "video_post", "article", "poll"],
                "media_types": ["image", "video", "document"],
                "max_images": 9,
                "max_video_duration": 600,
                "supports_hashtags": True,
                "max_hashtags": 5,
                "supports_scheduling": True,
                "supports_articles": True,
                "supports_polls": True,
                "character_limit": 3000
            },
            SocialPlatform.FACEBOOK: {
                "post_types": ["text_post", "image_post", "video_post", "event", "poll"],
                "media_types": ["image", "video"],
                "max_images": 10,
                "max_video_duration": 7200,
                "supports_hashtags": True,
                "max_hashtags": 30,
                "supports_scheduling": True,
                "supports_events": True,
                "supports_polls": True,
                "character_limit": 63206
            }
        }
        
        return capabilities.get(platform, {})
    
    @classmethod
    def validate_task_for_platform(cls, task: str, platform: SocialPlatform) -> Dict[str, Any]:
        """Validate if a task is suitable for a specific platform.
        
        Args:
            task: Task description
            platform: Target platform
        
        Returns:
            Validation result with recommendations
        """
        capabilities = cls.get_platform_capabilities(platform)
        task_lower = task.lower()
        
        validation = {
            "is_suitable": True,
            "warnings": [],
            "recommendations": [],
            "platform": platform.value,
            "capabilities": capabilities
        }
        
        # Check for platform-specific features
        if "story" in task_lower and not capabilities.get("supports_stories", False):
            validation["warnings"].append(f"{platform.value} does not support stories")
            validation["recommendations"].append("Consider using Instagram for story content")
        
        if "reel" in task_lower and not capabilities.get("supports_reels", False):
            validation["warnings"].append(f"{platform.value} does not support reels")
            validation["recommendations"].append("Consider using Instagram for reel content")
        
        if "article" in task_lower and not capabilities.get("supports_articles", False):
            validation["warnings"].append(f"{platform.value} does not support long-form articles")
            validation["recommendations"].append("Consider using LinkedIn for article publishing")
        
        if "event" in task_lower and not capabilities.get("supports_events", False):
            validation["warnings"].append(f"{platform.value} does not support event creation")
            validation["recommendations"].append("Consider using Facebook for event promotion")
        
        # Check content appropriateness
        if platform == SocialPlatform.LINKEDIN:
            casual_indicators = ["party", "drunk", "hangover", "lit", "savage"]
            if any(indicator in task_lower for indicator in casual_indicators):
                validation["warnings"].append("Content may not be suitable for LinkedIn's professional audience")
                validation["recommendations"].append("Consider using Instagram or Facebook for casual content")
        
        if validation["warnings"]:
            validation["is_suitable"] = False
        
        return validation