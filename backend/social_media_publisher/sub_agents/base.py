"""Base Social Media Agent

Abstract base class for all social media platform agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone

from ..config import (
    SocialMediaPublisherConfig,
    SocialPlatform,
    PostType,
    PostStatus,
    PostScheduling,
    PlatformConfig
)
from ai_providers.factory import AIProviderFactory
from ai_providers.base import AIResponse
from ai_providers.exceptions import AIProviderError
from logging_config import log_orchestration_event

logger = logging.getLogger(__name__)


class BaseSocialMediaAgent(ABC):
    """Abstract base class for social media platform agents."""
    
    def __init__(self, config: SocialMediaPublisherConfig):
        """Initialize the base social media agent.
        
        Args:
            config: Social media publisher configuration
        """
        self.config = config
        self.platform = self._get_platform()
        self.platform_config = config.get_platform_config(self.platform)
        self._ai_provider = None
        self._initialized = False
        
        if not self.platform_config:
            raise ValueError(f"No configuration found for platform: {self.platform}")
        
        if not self.platform_config.enabled:
            raise ValueError(f"Platform {self.platform} is not enabled")
    
    @abstractmethod
    def _get_platform(self) -> SocialPlatform:
        """Get the platform this agent handles.
        
        Returns:
            SocialPlatform enum value
        """
        pass
    
    async def initialize(self) -> None:
        """Initialize the agent and AI provider."""
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
            
            # Platform-specific initialization
            await self._platform_initialize()
            
            self._initialized = True
            logger.info(f"{self.__class__.__name__} initialized for {self.platform.value}")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            raise
    
    async def _platform_initialize(self) -> None:
        """Platform-specific initialization. Override in subclasses."""
        pass
    
    async def publish_content(
        self,
        content: str,
        request_id: str,
        post_type: Optional[PostType] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        target_audience: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Publish content to the social media platform.
        
        Args:
            content: Content text to publish
            request_id: Unique request identifier
            post_type: Type of post to create
            images: List of image URLs or paths
            videos: List of video URLs or paths
            hashtags: List of hashtags to include
            mentions: List of usernames to mention
            schedule_time: When to publish (None for immediate)
            target_audience: Target audience description
            additional_params: Platform-specific parameters
            **kwargs: Additional parameters
        
        Returns:
            Dictionary containing publishing results and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Log publishing start
        log_orchestration_event(
            request_id=request_id,
            event_type="social_media_publish_start",
            agent_id=f"social_media_{self.platform.value}",
            message=f"Starting content publishing to {self.platform.value}",
            additional_data={
                "platform": self.platform.value,
                "post_type": post_type.value if post_type else "auto",
                "content_length": len(content),
                "has_images": bool(images),
                "has_videos": bool(videos),
                "scheduled": bool(schedule_time)
            }
        )
        
        try:
            # Validate content
            await self._validate_content(content, post_type, images, videos)
            
            # Optimize content for platform
            optimized_content = await self._optimize_content(
                content, post_type, target_audience, request_id
            )
            
            # Generate hashtags if needed
            if self.config.auto_add_hashtags and not hashtags:
                hashtags = await self._generate_hashtags(
                    optimized_content, post_type, request_id
                )
            
            # Detect mentions if enabled
            if self.config.auto_mention_detection and not mentions:
                mentions = await self._detect_mentions(optimized_content)
            
            # Prepare post data
            post_data = {
                "content": optimized_content,
                "post_type": post_type or self._determine_post_type(content, images, videos),
                "images": images or [],
                "videos": videos or [],
                "hashtags": hashtags or [],
                "mentions": mentions or [],
                "schedule_time": schedule_time,
                "additional_params": additional_params or {}
            }
            
            # Publish or schedule
            if schedule_time:
                result = await self._schedule_post(post_data, request_id)
            else:
                result = await self._publish_post(post_data, request_id)
            
            # Add metadata
            result.update({
                "platform": self.platform.value,
                "agent_version": "1.0.0",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "original_content": content,
                "optimized_content": optimized_content
            })
            
            # Log successful publishing
            log_orchestration_event(
                request_id=request_id,
                event_type="social_media_publish_complete",
                agent_id=f"social_media_{self.platform.value}",
                message=f"Content published successfully to {self.platform.value}",
                additional_data={
                    "platform": self.platform.value,
                    "post_id": result.get("post_id"),
                    "status": result.get("status"),
                    "engagement_metrics": result.get("metrics", {})
                }
            )
            
            return result
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="social_media_publish_error",
                agent_id=f"social_media_{self.platform.value}",
                message=f"Publishing failed for {self.platform.value}: {str(e)}",
                additional_data={
                    "platform": self.platform.value,
                    "error_type": type(e).__name__
                }
            )
            logger.error(f"Publishing failed for {self.platform.value}: {e}")
            raise AIProviderError(f"Publishing failed: {str(e)}")
    
    async def _validate_content(
        self,
        content: str,
        post_type: Optional[PostType],
        images: Optional[List[str]],
        videos: Optional[List[str]]
    ) -> None:
        """Validate content against platform requirements.
        
        Args:
            content: Content text
            post_type: Post type
            images: Image list
            videos: Video list
        
        Raises:
            ValueError: If content doesn't meet platform requirements
        """
        # Check content length
        if len(content) > self.platform_config.max_text_length:
            raise ValueError(
                f"Content too long: {len(content)} chars, max: {self.platform_config.max_text_length}"
            )
        
        # Check image limits
        if images and len(images) > self.platform_config.max_images:
            raise ValueError(
                f"Too many images: {len(images)}, max: {self.platform_config.max_images}"
            )
        
        # Platform-specific validation
        await self._platform_validate_content(content, post_type, images, videos)
    
    async def _platform_validate_content(
        self,
        content: str,
        post_type: Optional[PostType],
        images: Optional[List[str]],
        videos: Optional[List[str]]
    ) -> None:
        """Platform-specific content validation. Override in subclasses."""
        pass
    
    async def _optimize_content(
        self,
        content: str,
        post_type: Optional[PostType],
        target_audience: Optional[str],
        request_id: str
    ) -> str:
        """Optimize content for the platform.
        
        Args:
            content: Original content
            post_type: Post type
            target_audience: Target audience
            request_id: Request ID for logging
        
        Returns:
            Optimized content
        """
        if not self.config.auto_optimize_content:
            return content
        
        optimization_prompt = await self._get_optimization_prompt(
            content, post_type, target_audience
        )
        
        try:
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=optimization_prompt,
                model=self.config.ai_provider.model,
                temperature=self.config.ai_provider.temperature,
                max_tokens=self.config.ai_provider.max_tokens
            )
            
            optimized = response.content.strip()
            
            # Ensure optimized content meets length requirements
            if len(optimized) > self.platform_config.max_text_length:
                optimized = optimized[:self.platform_config.max_text_length - 3] + "..."
            
            return optimized
            
        except Exception as e:
            logger.warning(f"Content optimization failed: {e}. Using original content.")
            return content
    
    @abstractmethod
    async def _get_optimization_prompt(
        self,
        content: str,
        post_type: Optional[PostType],
        target_audience: Optional[str]
    ) -> str:
        """Get platform-specific content optimization prompt.
        
        Args:
            content: Original content
            post_type: Post type
            target_audience: Target audience
        
        Returns:
            Optimization prompt
        """
        pass
    
    async def _generate_hashtags(
        self,
        content: str,
        post_type: Optional[PostType],
        request_id: str
    ) -> List[str]:
        """Generate relevant hashtags for the content.
        
        Args:
            content: Content text
            post_type: Post type
            request_id: Request ID
        
        Returns:
            List of hashtags
        """
        if not self.platform_config.supports_hashtags:
            return []
        
        hashtag_prompt = await self._get_hashtag_prompt(content, post_type)
        
        try:
            response: AIResponse = await self._ai_provider.generate_content(
                prompt=hashtag_prompt,
                model=self.config.ai_provider.model,
                temperature=0.8,
                max_tokens=200
            )
            
            # Extract hashtags from response
            hashtags = self._extract_hashtags(response.content)
            
            # Limit to platform maximum
            max_hashtags = min(
                self.platform_config.max_hashtags,
                self.config.hashtag_config.max_hashtags
            )
            
            return hashtags[:max_hashtags]
            
        except Exception as e:
            logger.warning(f"Hashtag generation failed: {e}")
            return []
    
    @abstractmethod
    async def _get_hashtag_prompt(self, content: str, post_type: Optional[PostType]) -> str:
        """Get platform-specific hashtag generation prompt.
        
        Args:
            content: Content text
            post_type: Post type
        
        Returns:
            Hashtag generation prompt
        """
        pass
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text.
        
        Args:
            text: Text containing hashtags
        
        Returns:
            List of hashtags without # symbol
        """
        import re
        hashtags = re.findall(r'#(\w+)', text)
        return list(set(hashtags))  # Remove duplicates
    
    async def _detect_mentions(self, content: str) -> List[str]:
        """Detect mentions in content.
        
        Args:
            content: Content text
        
        Returns:
            List of mentioned usernames
        """
        if not self.platform_config.supports_mentions:
            return []
        
        import re
        mentions = re.findall(r'@(\w+)', content)
        return list(set(mentions))  # Remove duplicates
    
    def _determine_post_type(
        self,
        content: str,
        images: Optional[List[str]],
        videos: Optional[List[str]]
    ) -> PostType:
        """Determine post type based on content.
        
        Args:
            content: Content text
            images: Image list
            videos: Video list
        
        Returns:
            Determined post type
        """
        if videos:
            return PostType.VIDEO_POST
        elif images:
            if len(images) > 1:
                return PostType.CAROUSEL_POST
            else:
                return PostType.IMAGE_POST
        else:
            return PostType.TEXT_POST
    
    @abstractmethod
    async def _publish_post(self, post_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Publish post immediately to the platform.
        
        Args:
            post_data: Post data dictionary
            request_id: Request ID
        
        Returns:
            Publishing result
        """
        pass
    
    @abstractmethod
    async def _schedule_post(self, post_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Schedule post for later publishing.
        
        Args:
            post_data: Post data dictionary
            request_id: Request ID
        
        Returns:
            Scheduling result
        """
        pass
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a published post.
        
        Args:
            post_id: Post identifier
        
        Returns:
            Analytics data
        """
        # Default implementation - override in subclasses
        return {
            "post_id": post_id,
            "platform": self.platform.value,
            "analytics_available": False,
            "message": "Analytics not implemented for this platform"
        }
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy.
        
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
            logger.error(f"{self.__class__.__name__} health check failed: {e}")
            return False