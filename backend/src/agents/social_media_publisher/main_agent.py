"""Social Media Publisher Main Agent

Main orchestrator agent that manages and coordinates sub-agents
for different social media platforms and publishing tasks.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List, Union
from datetime import datetime, timezone

from .config import (
    SocialMediaPublisherConfig,
    SocialPlatform,
    PostType,
    PostStatus,
    PostScheduling,
    DEFAULT_CONFIG
)
from .factory import SocialMediaAgentFactory
from .sub_agents.base import BaseSocialMediaAgent
from ...core.ai_providers.factory import AIProviderFactory
from ...core.ai_providers.base import AIResponse
from ...core.ai_providers.exceptions import AIProviderError
from ...core.logging_config import log_orchestration_event
from ...core.agent_state_manager import state_manager

logger = logging.getLogger(__name__)


class SocialMediaPublisherMainAgent:
    """Main Social Media Publisher Agent that orchestrates platform-specific sub-agents."""
    
    def __init__(self, config: Optional[SocialMediaPublisherConfig] = None):
        """Initialize the main social media publisher agent.
        
        Args:
            config: Configuration for the agent system
        """
        self.config = config or DEFAULT_CONFIG
        self._ai_provider = None
        self._sub_agents: Dict[SocialPlatform, BaseSocialMediaAgent] = {}
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
            logger.info(f"Social Media Publisher Main Agent initialized with {self.config.ai_provider.provider} provider")
            
        except Exception as e:
            logger.error(f"Failed to initialize Social Media Publisher Main Agent: {e}")
            raise
    
    async def publish_content(
        self,
        content: str,
        request_id: str,
        platform: Optional[SocialPlatform] = None,
        platforms: Optional[List[SocialPlatform]] = None,
        post_type: Optional[PostType] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None,
        target_audience: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        task: Optional[str] = None,  # Add task parameter
        caption: Optional[str] = None,  # Add caption parameter
        **kwargs
    ) -> Dict[str, Any]:
        """Publish content to social media platform(s).
        
        Args:
            content: Content text to publish
            request_id: Unique request identifier
            platform: Single platform to publish to
            platforms: Multiple platforms to publish to
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
        
        # Enhanced content retrieval logic
        logger.debug(f"[SOCIAL_DEBUG] Initial content: {content[:200] if content else 'None'}...")
        logger.debug(f"[SOCIAL_DEBUG] Task parameter: {task[:200] if task else 'None'}...")
        logger.debug(f"[SOCIAL_DEBUG] Caption parameter: {caption[:200] if caption else 'None'}...")
        logger.debug(f"[SOCIAL_DEBUG] Session ID: {session_id}")
        
        # Priority 1: Use caption parameter if provided (from CEO agent)
        if caption and caption != content:
            logger.info(f"[SOCIAL_DEBUG] Using caption parameter as content")
            content = caption
        # Priority 2: Check state manager for Content Writer output
        elif session_id:
            # Try to get content from Content Writer agent output
            logger.debug(f"[SOCIAL_DEBUG] Attempting to retrieve Content Writer output from state manager")
            content_writer_output = state_manager.get_agent_output(session_id, "content_writer")
            if content_writer_output:
                logger.info(f"[SOCIAL_DEBUG] Retrieved content from Content Writer via state manager for session {session_id}")
                # Use the actual generated content instead of the instruction
                content = content_writer_output
                logger.info(f"[SOCIAL_DEBUG] Using generated content: {content[:200]}...")
                
                # Also try to extract hashtags if they were generated separately
                try:
                    # Check if the content includes hashtags already
                    if not hashtags and '#' in content:
                        # Extract hashtags from the content
                        import re
                        extracted_hashtags = re.findall(r'#\w+', content)
                        if extracted_hashtags:
                            hashtags = [tag.strip('#') for tag in extracted_hashtags]
                            logger.info(f"[SOCIAL_DEBUG] Extracted {len(hashtags)} hashtags from content")
                except Exception as e:
                    logger.warning(f"[SOCIAL_DEBUG] Failed to extract hashtags: {e}")
            else:
                logger.warning(f"[SOCIAL_DEBUG] No Content Writer output found in state manager for session {session_id}")
                # Priority 3: Check if content parameter contains actual content (not instruction)
                if content and len(content) > 50 and not content.startswith("Schedule") and not content.startswith("Publish"):
                    logger.info(f"[SOCIAL_DEBUG] Using content parameter as it appears to be actual content")
                # Priority 4: Check if task contains content
                elif task and len(task) > 50 and not task.startswith("Schedule") and not task.startswith("Publish"):
                    logger.info(f"[SOCIAL_DEBUG] Using task as content since it appears to be actual content")
                    content = task
        
        logger.info(f"[SOCIAL_DEBUG] Final content to publish: {content[:200]}...")
        
        # Determine target platforms
        target_platforms = self._determine_target_platforms(platform, platforms, content)
        
        # Log publishing start
        log_orchestration_event(
            request_id=request_id,
            event_type="social_media_publish_start",
            agent_id="social_media_publisher_main",
            message="Starting content publishing to social media platforms",
            additional_data={
                "target_platforms": [p.value for p in target_platforms],
                "content_length": len(content),
                "has_images": bool(images),
                "has_videos": bool(videos),
                "scheduled": bool(schedule_time),
                "multi_platform": len(target_platforms) > 1
            }
        )
        
        try:
            # Validate platforms are enabled
            enabled_platforms = [p for p in target_platforms if self.config.is_platform_enabled(p)]
            
            if not enabled_platforms:
                raise ValueError("No enabled platforms found for publishing")
            
            if len(enabled_platforms) != len(target_platforms):
                disabled = [p.value for p in target_platforms if p not in enabled_platforms]
                logger.warning(f"Skipping disabled platforms: {disabled}")
            
            # Publish to each platform
            results = {}
            errors = {}
            
            if len(enabled_platforms) == 1:
                # Single platform publishing
                platform_result = await self._publish_to_platform(
                    enabled_platforms[0],
                    content,
                    request_id,
                    post_type,
                    images,
                    videos,
                    hashtags,
                    mentions,
                    schedule_time,
                    target_audience,
                    additional_params,
                    **kwargs
                )
                results[enabled_platforms[0].value] = platform_result
            else:
                # Multi-platform publishing
                platform_tasks = []
                for platform in enabled_platforms:
                    task = self._publish_to_platform(
                        platform,
                        content,
                        request_id,
                        post_type,
                        images,
                        videos,
                        hashtags,
                        mentions,
                        schedule_time,
                        target_audience,
                        additional_params,
                        **kwargs
                    )
                    platform_tasks.append((platform, task))
                
                # Execute all publishing tasks concurrently
                platform_results = await asyncio.gather(
                    *[task for _, task in platform_tasks],
                    return_exceptions=True
                )
                
                # Process results
                for (platform, _), result in zip(platform_tasks, platform_results):
                    if isinstance(result, Exception):
                        errors[platform.value] = str(result)
                        logger.error(f"Publishing failed for {platform.value}: {result}")
                    else:
                        results[platform.value] = result
            
            # Compile final result
            final_result = {
                "success": len(results) > 0,
                "platforms_published": list(results.keys()),
                "platforms_failed": list(errors.keys()),
                "total_platforms": len(enabled_platforms),
                "successful_platforms": len(results),
                "failed_platforms": len(errors),
                "results": results,
                "errors": errors,
                "main_agent_version": "1.0.0",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "original_content": content
            }
            
            # Add aggregated metrics
            if results:
                final_result["aggregated_metrics"] = self._aggregate_metrics(results)
            
            # Log successful publishing
            log_orchestration_event(
                request_id=request_id,
                event_type="social_media_publish_complete",
                agent_id="social_media_publisher_main",
                message="Content publishing completed",
                additional_data={
                    "successful_platforms": len(results),
                    "failed_platforms": len(errors),
                    "platforms_published": list(results.keys()),
                    "total_reach": final_result.get("aggregated_metrics", {}).get("total_estimated_reach", 0)
                }
            )
            
            return final_result
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="social_media_publish_error",
                agent_id="social_media_publisher_main",
                message=f"Content publishing failed: {str(e)}",
                additional_data={
                    "error_type": type(e).__name__,
                    "target_platforms": [p.value for p in target_platforms]
                }
            )
            logger.error(f"Content publishing failed for request {request_id}: {e}")
            raise AIProviderError(f"Content publishing failed: {str(e)}")
    
    def _determine_target_platforms(
        self,
        platform: Optional[SocialPlatform],
        platforms: Optional[List[SocialPlatform]],
        content: str
    ) -> List[SocialPlatform]:
        """Determine target platforms for publishing.
        
        Args:
            platform: Single platform
            platforms: Multiple platforms
            content: Content for auto-detection
        
        Returns:
            List of target platforms
        """
        if platforms:
            return platforms
        elif platform:
            return [platform]
        else:
            # Auto-detect platform from content
            detected_platform = SocialMediaAgentFactory._classify_task(content)
            return [detected_platform]
    
    async def _publish_to_platform(
        self,
        platform: SocialPlatform,
        content: str,
        request_id: str,
        post_type: Optional[PostType],
        images: Optional[List[str]],
        videos: Optional[List[str]],
        hashtags: Optional[List[str]],
        mentions: Optional[List[str]],
        schedule_time: Optional[datetime],
        target_audience: Optional[str],
        additional_params: Optional[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Publish content to a specific platform.
        
        Args:
            platform: Target platform
            content: Content to publish
            request_id: Request ID
            post_type: Post type
            images: Image list
            videos: Video list
            hashtags: Hashtag list
            mentions: Mention list
            schedule_time: Schedule time
            target_audience: Target audience
            additional_params: Additional parameters
            **kwargs: Extra parameters
        
        Returns:
            Publishing result
        """
        # Get or create platform agent
        agent = await self._get_platform_agent(platform)
        
        # Publish content using platform agent
        result = await agent.publish_content(
            content=content,
            request_id=request_id,
            post_type=post_type,
            images=images,
            videos=videos,
            hashtags=hashtags,
            mentions=mentions,
            schedule_time=schedule_time,
            target_audience=target_audience,
            additional_params=additional_params,
            **kwargs
        )
        
        return result
    
    async def _get_platform_agent(self, platform: SocialPlatform) -> BaseSocialMediaAgent:
        """Get or create a platform-specific agent.
        
        Args:
            platform: Social media platform
        
        Returns:
            Platform-specific agent instance
        """
        if platform not in self._sub_agents:
            self._sub_agents[platform] = await SocialMediaAgentFactory.create_agent(
                platform=platform,
                config=self.config
            )
        
        return self._sub_agents[platform]
    
    def _aggregate_metrics(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metrics from multiple platform results.
        
        Args:
            results: Results from different platforms
        
        Returns:
            Aggregated metrics
        """
        aggregated = {
            "total_posts": len(results),
            "total_estimated_reach": 0,
            "total_estimated_impressions": 0,
            "platforms_breakdown": {}
        }
        
        for platform, result in results.items():
            metrics = result.get("metrics", {})
            
            # Estimate reach based on platform (these would be real metrics in production)
            platform_reach = {
                "instagram": 1000,
                "linkedin": 500,
                "facebook": 800
            }.get(platform, 500)
            
            platform_impressions = {
                "instagram": 1500,
                "linkedin": 750,
                "facebook": 1200
            }.get(platform, 750)
            
            aggregated["total_estimated_reach"] += platform_reach
            aggregated["total_estimated_impressions"] += platform_impressions
            
            aggregated["platforms_breakdown"][platform] = {
                "estimated_reach": platform_reach,
                "estimated_impressions": platform_impressions,
                "post_id": result.get("post_id"),
                "status": result.get("status"),
                "url": result.get("url")
            }
        
        return aggregated
    
    async def schedule_content(
        self,
        content: str,
        schedule_time: datetime,
        request_id: str,
        platform: Optional[SocialPlatform] = None,
        platforms: Optional[List[SocialPlatform]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Schedule content for future publishing.
        
        Args:
            content: Content to schedule
            schedule_time: When to publish
            request_id: Request ID
            platform: Single platform
            platforms: Multiple platforms
            **kwargs: Additional parameters
        
        Returns:
            Scheduling result
        """
        return await self.publish_content(
            content=content,
            request_id=request_id,
            platform=platform,
            platforms=platforms,
            schedule_time=schedule_time,
            **kwargs
        )
    
    async def get_analytics(
        self,
        post_id: str,
        platform: SocialPlatform,
        request_id: str
    ) -> Dict[str, Any]:
        """Get analytics for a published post.
        
        Args:
            post_id: Post identifier
            platform: Platform where post was published
            request_id: Request ID
        
        Returns:
            Analytics data
        """
        try:
            agent = await self._get_platform_agent(platform)
            analytics = await agent.get_post_analytics(post_id)
            
            # Add main agent metadata
            analytics.update({
                "main_agent_version": "1.0.0",
                "retrieved_by": "social_media_publisher_main",
                "request_id": request_id
            })
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics for {platform.value} post {post_id}: {e}")
            return {
                "post_id": post_id,
                "platform": platform.value,
                "analytics_available": False,
                "error": str(e),
                "request_id": request_id
            }
    
    async def get_platform_suggestions(
        self,
        content: str,
        target_audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get platform suggestions for content.
        
        Args:
            content: Content to analyze
            target_audience: Target audience
        
        Returns:
            Platform suggestions
        """
        suggestions = {
            "recommended_platforms": [],
            "platform_analysis": {},
            "content_analysis": {
                "content_type": "general",
                "tone": "neutral",
                "target_audience": target_audience or "general"
            }
        }
        
        # Analyze content for each platform
        for platform in self.config.get_enabled_platforms():
            validation = SocialMediaAgentFactory.validate_task_for_platform(content, platform)
            
            platform_score = 100
            if not validation["is_suitable"]:
                platform_score -= 30
            
            platform_score -= len(validation["warnings"]) * 10
            
            suggestions["platform_analysis"][platform.value] = {
                "suitability_score": max(0, platform_score),
                "is_suitable": validation["is_suitable"],
                "warnings": validation["warnings"],
                "recommendations": validation["recommendations"],
                "capabilities": validation["capabilities"]
            }
            
            if platform_score >= 70:
                suggestions["recommended_platforms"].append({
                    "platform": platform.value,
                    "score": platform_score,
                    "reason": "Good fit for content and audience"
                })
        
        # Sort recommendations by score
        suggestions["recommended_platforms"].sort(key=lambda x: x["score"], reverse=True)
        
        return suggestions
    
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
            
            # Check AI provider health
            ai_healthy = await self._ai_provider.health_check()
            
            # Check platform agents health
            platform_health = True
            for agent in self._sub_agents.values():
                agent_healthy = await agent.health_check()
                if not agent_healthy:
                    platform_health = False
                    break
            
            return ai_healthy and platform_health
            
        except Exception as e:
            logger.error(f"Social Media Publisher Main Agent health check failed: {e}")
            return False
    
    def get_supported_platforms(self) -> List[SocialPlatform]:
        """Get list of supported platforms.
        
        Returns:
            List of supported platforms
        """
        return SocialMediaAgentFactory.get_supported_platforms()
    
    async def clear_cache(self) -> None:
        """Clear cached sub-agents."""
        self._sub_agents.clear()
        SocialMediaAgentFactory.clear_cache()
        logger.info("Social Media Publisher Main Agent cache cleared")