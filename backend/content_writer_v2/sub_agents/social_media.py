"""Social Media Content Agent

Specialized agent for generating social media content across different platforms
with platform-specific optimizations, hashtags, and engagement features.
"""

import re
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone

from .base import BaseContentAgent
from ..config import (
    ContentWriterV2Config, 
    SocialPlatform, 
    ContentFormat, 
    ToneStyle,
    DEFAULT_CONFIG
)
from ai_providers.exceptions import AIProviderError
from logging_config import log_orchestration_event

logger = logging.getLogger(__name__)


class SocialMediaAgent(BaseContentAgent):
    """Specialized agent for social media content generation."""
    
    def __init__(self, config: Optional[ContentWriterV2Config] = None):
        """Initialize the Social Media Agent.
        
        Args:
            config: Configuration for the agent
        """
        super().__init__(config)
        self.platform_limits = self.config.social_media.character_limits
    
    async def generate_content(
        self,
        task: str,
        request_id: str,
        platform: Optional[SocialPlatform] = None,
        content_format: Optional[ContentFormat] = None,
        tone: Optional[ToneStyle] = None,
        include_hashtags: Optional[bool] = None,
        include_emojis: Optional[bool] = None,
        include_call_to_action: Optional[bool] = None,
        target_audience: Optional[str] = None,
        brand_context: Optional[str] = None,
        hashtag_count: Optional[int] = None,
        additional_instructions: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate social media content.
        
        Args:
            task: Content topic or description
            request_id: Unique request identifier
            platform: Target social media platform
            content_format: Specific content format
            tone: Tone and style
            include_hashtags: Whether to include hashtags
            include_emojis: Whether to include emojis
            include_call_to_action: Whether to include CTA
            target_audience: Target audience description
            brand_context: Brand context and guidelines
            hashtag_count: Number of hashtags to include
            additional_instructions: Additional instructions
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with generated content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Use defaults from config
        platform = platform or self.config.social_media.default_platform
        include_hashtags = include_hashtags if include_hashtags is not None else self.config.social_media.include_hashtags
        include_emojis = include_emojis if include_emojis is not None else self.config.social_media.include_emojis
        include_call_to_action = include_call_to_action if include_call_to_action is not None else self.config.social_media.include_call_to_action
        hashtag_count = hashtag_count or self.config.social_media.max_hashtags
        
        # Log generation start
        log_orchestration_event(
            request_id=request_id,
            event_type="social_media_generation_start",
            agent_id="social_media_agent",
            message="Starting social media content generation",
            additional_data={
                "platform": platform.value,
                "format": content_format.value if content_format else "auto",
                "include_hashtags": include_hashtags,
                "include_emojis": include_emojis
            }
        )
        
        try:
            # Build platform-specific prompt
            prompt = self._build_social_media_prompt(
                task=task,
                platform=platform,
                content_format=content_format,
                tone=tone,
                include_hashtags=include_hashtags,
                include_emojis=include_emojis,
                include_call_to_action=include_call_to_action,
                target_audience=target_audience,
                brand_context=brand_context,
                hashtag_count=hashtag_count,
                additional_instructions=additional_instructions
            )
            
            # Generate content
            response = await self._generate_with_provider(
                prompt=prompt,
                request_id=request_id,
                temperature=0.8  # Higher creativity for social media
            )
            
            content = response.content.strip()
            
            # Post-process content
            processed_content = await self._post_process_social_content(
                content=content,
                platform=platform,
                include_hashtags=include_hashtags,
                hashtag_count=hashtag_count,
                request_id=request_id
            )
            
            # Extract hashtags and mentions
            hashtags = self._extract_hashtags(processed_content)
            mentions = self._extract_mentions(processed_content)
            
            # Validate content length
            validation = await self._validate_platform_content(
                content=processed_content,
                platform=platform
            )
            
            # Build metadata
            metadata = self._extract_content_metadata(
                content=processed_content,
                platform=platform.value,
                content_format=content_format.value if content_format else "auto",
                hashtag_count=len(hashtags),
                mention_count=len(mentions),
                character_count=len(processed_content),
                within_limit=validation["within_limit"],
                engagement_score=self._calculate_engagement_score(processed_content, hashtags),
                tone_used=tone.value if tone else "auto"
            )
            
            result = {
                "content": processed_content,
                "hashtags": hashtags,
                "mentions": mentions,
                "metadata": metadata,
                "validation": validation,
                "platform_optimized": True,
                "suggestions": await self._get_content_suggestions(task, platform)
            }
            
            # Log successful generation
            log_orchestration_event(
                request_id=request_id,
                event_type="social_media_generation_complete",
                agent_id="social_media_agent",
                message="Social media content generated successfully",
                additional_data={
                    "platform": platform.value,
                    "content_length": len(processed_content),
                    "hashtag_count": len(hashtags),
                    "within_limit": validation["within_limit"]
                }
            )
            
            return result
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="social_media_generation_error",
                agent_id="social_media_agent",
                message=f"Social media content generation failed: {str(e)}",
                additional_data={
                    "platform": platform.value,
                    "error_type": type(e).__name__
                }
            )
            logger.error(f"Social media content generation failed for request {request_id}: {e}")
            raise AIProviderError(f"Social media content generation failed: {str(e)}")
    
    def _build_social_media_prompt(
        self,
        task: str,
        platform: SocialPlatform,
        content_format: Optional[ContentFormat] = None,
        tone: Optional[ToneStyle] = None,
        include_hashtags: bool = True,
        include_emojis: bool = True,
        include_call_to_action: bool = True,
        target_audience: Optional[str] = None,
        brand_context: Optional[str] = None,
        hashtag_count: int = 10,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Build a platform-specific prompt for social media content.
        
        Args:
            task: Content topic
            platform: Target platform
            content_format: Content format
            tone: Tone and style
            include_hashtags: Include hashtags
            include_emojis: Include emojis
            include_call_to_action: Include CTA
            target_audience: Target audience
            brand_context: Brand context
            hashtag_count: Number of hashtags
            additional_instructions: Additional instructions
        
        Returns:
            Complete prompt string
        """
        # Platform-specific system prompts
        platform_prompts = {
            SocialPlatform.INSTAGRAM: f"""
You are an expert Instagram content creator specializing in engaging, visually-appealing posts.

Create Instagram content that:
- Captures attention in the first few words
- Uses line breaks for visual appeal and readability
- Includes relevant emojis naturally (if requested)
- Has a conversational, authentic tone
- Encourages engagement (likes, comments, shares)
- Stays within {self.platform_limits[platform]} characters
- Uses strategic hashtags for discovery (if requested)
- Includes a clear call-to-action when appropriate
""",
            
            SocialPlatform.TWITTER: f"""
You are an expert Twitter content creator specializing in concise, impactful tweets.

Create Twitter content that:
- Gets straight to the point immediately
- Uses threading if more context is needed
- Includes relevant hashtags naturally (if requested)
- Encourages retweets and replies
- Stays within {self.platform_limits[platform]} characters
- Uses Twitter-specific language and conventions
- Includes mentions when relevant
""",
            
            SocialPlatform.LINKEDIN: f"""
You are an expert LinkedIn content creator specializing in professional, value-driven posts.

Create LinkedIn content that:
- Provides professional value and insights
- Uses a professional yet approachable tone
- Includes industry-relevant hashtags (if requested)
- Encourages meaningful professional discussion
- Stays within {self.platform_limits[platform]} characters
- Uses proper business etiquette
- Includes a professional call-to-action
""",
            
            SocialPlatform.FACEBOOK: f"""
You are an expert Facebook content creator specializing in community-building posts.

Create Facebook content that:
- Builds community and encourages discussion
- Uses a friendly, conversational tone
- Includes relevant hashtags naturally (if requested)
- Encourages shares and comments
- Can be longer and more detailed
- Uses Facebook-specific features and language
- Includes engaging questions or prompts
""",
            
            SocialPlatform.TIKTOK: f"""
You are an expert TikTok content creator specializing in trendy, engaging captions.

Create TikTok content that:
- Uses current trends and viral language
- Is short, punchy, and attention-grabbing
- Includes trending hashtags (if requested)
- Encourages views and engagement
- Stays within {self.platform_limits[platform]} characters
- Uses TikTok-specific slang and conventions
- Includes hooks that make people want to watch
""",
            
            SocialPlatform.YOUTUBE: f"""
You are an expert YouTube content creator specializing in compelling video descriptions.

Create YouTube content that:
- Clearly describes the video content
- Uses SEO-friendly language and keywords
- Includes relevant hashtags (if requested)
- Encourages likes, comments, and subscriptions
- Can be detailed and informative
- Includes timestamps and chapter markers when relevant
- Has a clear call-to-action
"""
        }
        
        system_prompt = platform_prompts.get(platform, platform_prompts[SocialPlatform.INSTAGRAM])
        
        # Content format specific instructions
        format_instructions = ""
        if content_format:
            format_map = {
                ContentFormat.CAPTION: "Create a compelling caption that complements visual content.",
                ContentFormat.POST: "Create a standalone post that delivers complete value.",
                ContentFormat.STORY: "Create story content that's casual and behind-the-scenes.",
                ContentFormat.REEL_SCRIPT: "Create a script for a short-form video with visual cues."
            }
            format_instructions = format_map.get(content_format, "")
        
        # Tone instructions
        tone_instructions = ""
        if tone:
            tone_map = {
                ToneStyle.CASUAL: "Use a relaxed, informal tone like talking to a friend.",
                ToneStyle.PROFESSIONAL: "Maintain a professional, authoritative tone.",
                ToneStyle.FRIENDLY: "Be warm, welcoming, and approachable.",
                ToneStyle.HUMOROUS: "Include appropriate humor and wit.",
                ToneStyle.INSPIRATIONAL: "Be motivating and uplifting.",
                ToneStyle.TRENDY: "Use current slang and trending language.",
                ToneStyle.EDUCATIONAL: "Focus on teaching and providing value.",
                ToneStyle.CONVERSATIONAL: "Write as if having a conversation."
            }
            tone_instructions = tone_map.get(tone, "")
        
        # Build requirements
        requirements = []
        requirements.append(f"Topic/Task: {task}")
        
        if format_instructions:
            requirements.append(f"Format: {format_instructions}")
        
        if tone_instructions:
            requirements.append(f"Tone: {tone_instructions}")
        
        if include_hashtags:
            requirements.append(f"Include {hashtag_count} relevant hashtags naturally integrated into the content")
        
        if include_emojis and platform in [SocialPlatform.INSTAGRAM, SocialPlatform.FACEBOOK]:
            requirements.append("Include relevant emojis to enhance engagement")
        
        if include_call_to_action:
            requirements.append("Include a clear, compelling call-to-action")
        
        if target_audience:
            requirements.append(f"Target audience: {target_audience}")
        
        if brand_context:
            requirements.append(f"Brand context: {brand_context}")
        
        if additional_instructions:
            requirements.append(f"Additional instructions: {additional_instructions}")
        
        # Character limit reminder
        char_limit = self.platform_limits[platform]
        requirements.append(f"IMPORTANT: Keep content under {char_limit} characters for {platform.value}")
        
        # Combine all parts
        prompt_parts = [system_prompt]
        prompt_parts.append("\nSpecific requirements:")
        prompt_parts.extend([f"- {req}" for req in requirements])
        
        prompt_parts.append(
            "\nGenerate engaging, platform-optimized content that meets all requirements. "
            "Focus on creating content that will perform well on the platform and engage the target audience."
        )
        
        return "\n".join(prompt_parts)
    
    async def _post_process_social_content(
        self,
        content: str,
        platform: SocialPlatform,
        include_hashtags: bool,
        hashtag_count: int,
        request_id: str
    ) -> str:
        """Post-process social media content for platform optimization.
        
        Args:
            content: Generated content
            platform: Target platform
            include_hashtags: Whether hashtags should be included
            hashtag_count: Target number of hashtags
            request_id: Request identifier
        
        Returns:
            Post-processed content
        """
        processed_content = content
        
        # Ensure content fits platform limits
        char_limit = self.platform_limits[platform]
        if len(processed_content) > char_limit:
            # Truncate content while preserving hashtags
            hashtags = self._extract_hashtags(processed_content)
            hashtag_text = " ".join(hashtags) if hashtags else ""
            
            # Calculate available space for main content
            available_space = char_limit - len(hashtag_text) - 10  # Buffer for spacing
            
            if available_space > 50:  # Minimum viable content length
                main_content = processed_content.replace(hashtag_text, "").strip()
                truncated_main = main_content[:available_space].rsplit(' ', 1)[0]  # Avoid cutting words
                processed_content = f"{truncated_main}... {hashtag_text}".strip()
            else:
                # If hashtags take too much space, reduce them
                processed_content = processed_content[:char_limit-3] + "..."
        
        # Platform-specific formatting
        if platform == SocialPlatform.INSTAGRAM:
            # Add line breaks for better readability
            processed_content = self._format_instagram_content(processed_content)
        
        elif platform == SocialPlatform.TWITTER:
            # Ensure Twitter conventions
            processed_content = self._format_twitter_content(processed_content)
        
        elif platform == SocialPlatform.LINKEDIN:
            # Professional formatting
            processed_content = self._format_linkedin_content(processed_content)
        
        return processed_content.strip()
    
    def _format_instagram_content(self, content: str) -> str:
        """Format content specifically for Instagram.
        
        Args:
            content: Content to format
        
        Returns:
            Instagram-formatted content
        """
        # Add strategic line breaks for readability
        # This is a simple implementation - could be enhanced with more sophisticated logic
        sentences = content.split('. ')
        if len(sentences) > 2:
            # Add line breaks after every 2-3 sentences
            formatted_sentences = []
            for i, sentence in enumerate(sentences):
                formatted_sentences.append(sentence)
                if i > 0 and (i + 1) % 2 == 0 and i < len(sentences) - 1:
                    formatted_sentences.append("\n")
            content = '. '.join(formatted_sentences)
        
        return content
    
    def _format_twitter_content(self, content: str) -> str:
        """Format content specifically for Twitter.
        
        Args:
            content: Content to format
        
        Returns:
            Twitter-formatted content
        """
        # Ensure proper Twitter formatting
        # Remove excessive line breaks
        content = re.sub(r'\n+', ' ', content)
        return content
    
    def _format_linkedin_content(self, content: str) -> str:
        """Format content specifically for LinkedIn.
        
        Args:
            content: Content to format
        
        Returns:
            LinkedIn-formatted content
        """
        # LinkedIn prefers paragraph breaks for professional content
        return content
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content.
        
        Args:
            content: Content to extract hashtags from
        
        Returns:
            List of hashtags
        """
        hashtag_pattern = r'#\w+'
        return re.findall(hashtag_pattern, content)
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract mentions from content.
        
        Args:
            content: Content to extract mentions from
        
        Returns:
            List of mentions
        """
        mention_pattern = r'@\w+'
        return re.findall(mention_pattern, content)
    
    async def _validate_platform_content(
        self,
        content: str,
        platform: SocialPlatform
    ) -> Dict[str, Any]:
        """Validate content against platform requirements.
        
        Args:
            content: Content to validate
            platform: Target platform
        
        Returns:
            Validation results
        """
        char_limit = self.platform_limits[platform]
        char_count = len(content)
        
        validation = {
            "platform": platform.value,
            "character_count": char_count,
            "character_limit": char_limit,
            "within_limit": char_count <= char_limit,
            "utilization_percentage": round((char_count / char_limit) * 100, 1),
            "warnings": [],
            "suggestions": []
        }
        
        # Platform-specific validation
        if char_count > char_limit:
            validation["warnings"].append(f"Content exceeds {platform.value} character limit by {char_count - char_limit} characters")
            validation["suggestions"].append("Consider shortening the content or removing some hashtags")
        
        elif char_count < char_limit * 0.3:  # Less than 30% utilization
            validation["suggestions"].append(f"Content is quite short for {platform.value}. Consider adding more value or context")
        
        # Check for platform-specific best practices
        if platform == SocialPlatform.INSTAGRAM:
            hashtags = self._extract_hashtags(content)
            if len(hashtags) > 30:
                validation["warnings"].append("Instagram recommends using no more than 30 hashtags")
        
        elif platform == SocialPlatform.TWITTER:
            hashtags = self._extract_hashtags(content)
            if len(hashtags) > 5:
                validation["warnings"].append("Twitter posts with more than 5 hashtags may have reduced engagement")
        
        return validation
    
    def _calculate_engagement_score(self, content: str, hashtags: List[str]) -> float:
        """Calculate a predicted engagement score for the content.
        
        Args:
            content: Content to analyze
            hashtags: List of hashtags
        
        Returns:
            Engagement score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Factors that increase engagement
        if len(hashtags) > 0:
            score += 0.1
        
        if '?' in content:  # Questions increase engagement
            score += 0.1
        
        if any(word in content.lower() for word in ['you', 'your', 'comment', 'share', 'like']):
            score += 0.1  # Direct engagement prompts
        
        # Emoji presence (simple check)
        if any(ord(char) > 127 for char in content):  # Non-ASCII characters (likely emojis)
            score += 0.05
        
        # Length optimization
        if 50 <= len(content) <= 200:  # Optimal length range
            score += 0.1
        
        return min(1.0, score)  # Cap at 1.0
    
    async def _get_content_suggestions(self, task: str, platform: SocialPlatform) -> List[str]:
        """Get content improvement suggestions.
        
        Args:
            task: Original task
            platform: Target platform
        
        Returns:
            List of suggestions
        """
        suggestions = [
            f"Consider creating a series of posts about {task} for better engagement",
            f"Try different posting times to optimize reach on {platform.value}",
            "Use platform analytics to track performance and optimize future content"
        ]
        
        # Platform-specific suggestions
        if platform == SocialPlatform.INSTAGRAM:
            suggestions.extend([
                "Consider creating a matching Instagram Story",
                "Use relevant location tags if applicable",
                "Engage with comments quickly to boost visibility"
            ])
        
        elif platform == SocialPlatform.TWITTER:
            suggestions.extend([
                "Consider creating a Twitter thread for more detailed discussion",
                "Engage with replies to increase conversation",
                "Retweet relevant content from your industry"
            ])
        
        return suggestions