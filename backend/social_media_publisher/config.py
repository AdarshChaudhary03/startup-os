"""Social Media Publisher Configuration

Configuration classes, enums, and settings for the Social Media Publisher Agent.
"""

import os
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, time


class SocialPlatform(Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    TWITTER = "twitter"  # Future enhancement
    TIKTOK = "tiktok"    # Future enhancement


class PostType(Enum):
    """Types of social media posts."""
    TEXT_POST = "text_post"
    IMAGE_POST = "image_post"
    VIDEO_POST = "video_post"
    CAROUSEL_POST = "carousel_post"
    STORY = "story"
    REEL = "reel"
    ARTICLE = "article"
    EVENT = "event"
    POLL = "poll"


class PostStatus(Enum):
    """Status of social media posts."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class PostScheduling(Enum):
    """Post scheduling options."""
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    OPTIMAL_TIME = "optimal_time"
    CUSTOM_TIME = "custom_time"


class ContentModerationLevel(Enum):
    """Content moderation levels."""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    CUSTOM = "custom"


@dataclass
class PlatformConfig:
    """Configuration for a specific social media platform."""
    platform: SocialPlatform
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    enabled: bool = True
    
    # Platform-specific limits
    max_text_length: int = 2200
    max_hashtags: int = 30
    max_images: int = 10
    max_video_duration: int = 60
    
    # Image requirements
    image_width: int = 1080
    image_height: int = 1080
    supported_image_formats: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png"])
    
    # Video requirements
    supported_video_formats: List[str] = field(default_factory=lambda: ["mp4", "mov"])
    
    # Platform-specific features
    supports_hashtags: bool = True
    supports_mentions: bool = True
    supports_stories: bool = True
    supports_reels: bool = True
    supports_polls: bool = True
    supports_scheduling: bool = True


@dataclass
class HashtagConfig:
    """Configuration for hashtag generation and optimization."""
    auto_generate: bool = True
    max_hashtags: int = 30
    min_hashtags: int = 5
    trending_weight: float = 0.3
    relevance_weight: float = 0.7
    avoid_banned: bool = True
    include_branded: bool = True
    branded_hashtags: List[str] = field(default_factory=list)


@dataclass
class SchedulingConfig:
    """Configuration for post scheduling."""
    auto_schedule: bool = True
    use_optimal_timing: bool = True
    timezone: str = "UTC"
    
    # Optimal posting times by platform
    optimal_times: Dict[SocialPlatform, List[time]] = field(default_factory=lambda: {
        SocialPlatform.INSTAGRAM: [
            time(9, 0),   # 9 AM
            time(12, 0),  # 12 PM
            time(17, 0),  # 5 PM
            time(19, 0)   # 7 PM
        ],
        SocialPlatform.LINKEDIN: [
            time(8, 0),   # 8 AM
            time(12, 0),  # 12 PM
            time(14, 0),  # 2 PM
            time(17, 0)   # 5 PM
        ],
        SocialPlatform.FACEBOOK: [
            time(9, 0),   # 9 AM
            time(13, 0),  # 1 PM
            time(15, 0),  # 3 PM
            time(20, 0)   # 8 PM
        ]
    })


@dataclass
class ContentModerationConfig:
    """Configuration for content moderation."""
    enabled: bool = True
    level: ContentModerationLevel = ContentModerationLevel.BASIC
    check_profanity: bool = True
    check_spam: bool = True
    check_copyright: bool = True
    custom_filters: List[str] = field(default_factory=list)
    whitelist_domains: List[str] = field(default_factory=list)
    blacklist_words: List[str] = field(default_factory=list)


@dataclass
class AnalyticsConfig:
    """Configuration for analytics and monitoring."""
    enabled: bool = True
    track_engagement: bool = True
    track_reach: bool = True
    track_clicks: bool = True
    track_conversions: bool = True
    retention_days: int = 90
    export_format: str = "json"


@dataclass
class AIProviderConfig:
    """Configuration for AI provider integration."""
    provider: str = "groq"
    model: str = "llama-3.1-70b-versatile"  # Fixed: Use supported Groq model
    temperature: float = 0.7
    max_tokens: int = 1024
    timeout_seconds: int = 30


@dataclass
class SocialMediaPublisherConfig:
    """Main configuration class for Social Media Publisher Agent."""
    
    # Platform configurations
    platforms: Dict[SocialPlatform, PlatformConfig] = field(default_factory=dict)
    
    # Feature configurations
    hashtag_config: HashtagConfig = field(default_factory=HashtagConfig)
    scheduling_config: SchedulingConfig = field(default_factory=SchedulingConfig)
    moderation_config: ContentModerationConfig = field(default_factory=ContentModerationConfig)
    analytics_config: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    
    # AI provider configuration
    ai_provider: AIProviderConfig = field(default_factory=AIProviderConfig)
    
    # General settings
    default_platform: SocialPlatform = SocialPlatform.INSTAGRAM
    max_concurrent_posts: int = 5
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    
    # Logging and monitoring
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_endpoint: Optional[str] = None
    
    # Content settings
    auto_optimize_content: bool = True
    auto_add_hashtags: bool = True
    auto_mention_detection: bool = True
    
    def __post_init__(self):
        """Initialize platform configurations if not provided."""
        if not self.platforms:
            self.platforms = self._create_default_platform_configs()
    
    def _create_default_platform_configs(self) -> Dict[SocialPlatform, PlatformConfig]:
        """Create default platform configurations."""
        configs = {}
        
        # Instagram configuration
        configs[SocialPlatform.INSTAGRAM] = PlatformConfig(
            platform=SocialPlatform.INSTAGRAM,
            access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN"),
            app_id=os.getenv("INSTAGRAM_APP_ID"),
            app_secret=os.getenv("INSTAGRAM_APP_SECRET"),
            max_text_length=2200,
            max_hashtags=30,
            max_images=10,
            max_video_duration=60,
            image_width=1080,
            image_height=1080,
            supported_image_formats=["jpg", "jpeg", "png"],
            supported_video_formats=["mp4"],
            supports_hashtags=True,
            supports_mentions=True,
            supports_stories=True,
            supports_reels=True,
            supports_polls=True,
            supports_scheduling=True
        )
        
        # LinkedIn configuration
        configs[SocialPlatform.LINKEDIN] = PlatformConfig(
            platform=SocialPlatform.LINKEDIN,
            access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
            max_text_length=3000,
            max_hashtags=5,  # LinkedIn recommends fewer hashtags
            max_images=9,
            max_video_duration=600,  # 10 minutes
            image_width=1200,
            image_height=627,
            supported_image_formats=["jpg", "jpeg", "png", "gif"],
            supported_video_formats=["mp4", "mov", "wmv", "flv"],
            supports_hashtags=True,
            supports_mentions=True,
            supports_stories=False,  # LinkedIn Stories deprecated
            supports_reels=False,
            supports_polls=True,
            supports_scheduling=True
        )
        
        # Facebook configuration
        configs[SocialPlatform.FACEBOOK] = PlatformConfig(
            platform=SocialPlatform.FACEBOOK,
            access_token=os.getenv("FACEBOOK_ACCESS_TOKEN"),
            app_id=os.getenv("FACEBOOK_APP_ID"),
            app_secret=os.getenv("FACEBOOK_APP_SECRET"),
            max_text_length=63206,
            max_hashtags=30,
            max_images=10,
            max_video_duration=7200,  # 2 hours
            image_width=1200,
            image_height=630,
            supported_image_formats=["jpg", "jpeg", "png", "gif", "bmp", "tiff"],
            supported_video_formats=["mp4", "mov", "avi", "wmv", "flv", "3gp"],
            supports_hashtags=True,
            supports_mentions=True,
            supports_stories=True,
            supports_reels=True,
            supports_polls=True,
            supports_scheduling=True
        )
        
        return configs
    
    def get_platform_config(self, platform: SocialPlatform) -> Optional[PlatformConfig]:
        """Get configuration for a specific platform."""
        return self.platforms.get(platform)
    
    def is_platform_enabled(self, platform: SocialPlatform) -> bool:
        """Check if a platform is enabled."""
        config = self.get_platform_config(platform)
        return config is not None and config.enabled
    
    def get_enabled_platforms(self) -> List[SocialPlatform]:
        """Get list of enabled platforms."""
        return [
            platform for platform, config in self.platforms.items()
            if config.enabled
        ]


# Default configuration instance
DEFAULT_CONFIG = SocialMediaPublisherConfig(
    ai_provider=AIProviderConfig(
        provider=os.getenv("SOCIAL_MEDIA_AI_PROVIDER", "groq"),
        model=os.getenv("SOCIAL_MEDIA_AI_MODEL", "llama-3.1-70b-versatile"),  # Fixed: Use supported model
        temperature=float(os.getenv("SOCIAL_MEDIA_AI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("SOCIAL_MEDIA_AI_MAX_TOKENS", "1024"))
    ),
    default_platform=SocialPlatform(os.getenv("SOCIAL_MEDIA_DEFAULT_PLATFORM", "instagram")),
    auto_optimize_content=os.getenv("SOCIAL_MEDIA_AUTO_OPTIMIZE", "true").lower() == "true",
    auto_add_hashtags=os.getenv("SOCIAL_MEDIA_AUTO_HASHTAGS", "true").lower() == "true",
    log_level=os.getenv("SOCIAL_MEDIA_LOG_LEVEL", "INFO")
)