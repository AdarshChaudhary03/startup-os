"""Configuration for Content Writer v2 System

Centralized configuration management for all content writer sub-agents.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class ContentCategory(Enum):
    """Categories of content that can be generated."""
    SOCIAL_MEDIA = "social_media"
    BLOG = "blog"
    SCRIPT = "script"
    MARKETING = "marketing"
    TECHNICAL = "technical"
    EMAIL = "email"
    PRODUCT = "product"


class SocialPlatform(Enum):
    """Social media platforms."""
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class ContentFormat(Enum):
    """Content formats."""
    CAPTION = "caption"
    POST = "post"
    STORY = "story"
    REEL_SCRIPT = "reel_script"
    VIDEO_SCRIPT = "video_script"
    BLOG_POST = "blog_post"
    ARTICLE = "article"
    EMAIL_COPY = "email_copy"
    AD_COPY = "ad_copy"
    PRODUCT_DESCRIPTION = "product_description"
    TECHNICAL_DOC = "technical_doc"


class ToneStyle(Enum):
    """Tone and style options."""
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    HUMOROUS = "humorous"
    INSPIRATIONAL = "inspirational"
    EDUCATIONAL = "educational"
    PERSUASIVE = "persuasive"
    TRENDY = "trendy"


@dataclass
class AIProviderConfig:
    """Configuration for AI provider."""
    provider: str = "groq"
    model: str = "llama-3.1-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


@dataclass
class SocialMediaConfig:
    """Configuration for social media content generation."""
    default_platform: SocialPlatform = SocialPlatform.INSTAGRAM
    include_hashtags: bool = True
    max_hashtags: int = 30
    include_emojis: bool = False  # Changed to False for text-only content
    include_call_to_action: bool = True
    character_limits: Dict[SocialPlatform, int] = field(default_factory=lambda: {
        SocialPlatform.INSTAGRAM: 2200,
        SocialPlatform.TWITTER: 280,
        SocialPlatform.LINKEDIN: 3000,
        SocialPlatform.FACEBOOK: 63206,
        SocialPlatform.TIKTOK: 150,
        SocialPlatform.YOUTUBE: 5000
    })
    hashtag_categories: List[str] = field(default_factory=lambda: [
        "trending", "niche", "location", "brand", "community"
    ])


@dataclass
class BlogConfig:
    """Configuration for blog content generation."""
    default_word_count: int = 800
    min_word_count: int = 300
    max_word_count: int = 3000
    include_seo_optimization: bool = True
    include_meta_description: bool = True
    include_outline: bool = True
    default_structure: List[str] = field(default_factory=lambda: [
        "introduction", "main_content", "conclusion", "call_to_action"
    ])
    seo_keyword_density: float = 1.5  # Percentage


@dataclass
class ScriptConfig:
    """Configuration for script generation."""
    default_duration_seconds: int = 60
    include_visual_cues: bool = True
    include_timing: bool = True
    script_formats: List[str] = field(default_factory=lambda: [
        "reel", "youtube_short", "tiktok", "youtube_video", "podcast"
    ])
    words_per_minute: int = 150  # Average speaking rate


@dataclass
class MarketingConfig:
    """Configuration for marketing copy generation."""
    include_urgency: bool = True
    include_social_proof: bool = True
    include_benefits: bool = True
    include_features: bool = True
    call_to_action_styles: List[str] = field(default_factory=lambda: [
        "direct", "soft", "urgent", "curiosity", "benefit_driven"
    ])


@dataclass
class TechnicalConfig:
    """Configuration for technical writing."""
    include_code_examples: bool = True
    include_diagrams: bool = False
    documentation_style: str = "markdown"
    target_audience_level: str = "intermediate"  # beginner, intermediate, advanced


@dataclass
class ContentWriterV2Config:
    """Main configuration for Content Writer v2 system."""
    
    # AI Provider settings
    ai_provider: AIProviderConfig = field(default_factory=AIProviderConfig)
    
    # Sub-agent configurations
    social_media: SocialMediaConfig = field(default_factory=SocialMediaConfig)
    blog: BlogConfig = field(default_factory=BlogConfig)
    script: ScriptConfig = field(default_factory=ScriptConfig)
    marketing: MarketingConfig = field(default_factory=MarketingConfig)
    technical: TechnicalConfig = field(default_factory=TechnicalConfig)
    
    # General settings
    enable_logging: bool = True
    log_level: str = "INFO"
    cache_responses: bool = True
    cache_ttl_seconds: int = 3600
    
    # Quality control
    enable_content_validation: bool = True
    enable_plagiarism_check: bool = False
    enable_sentiment_analysis: bool = True
    
    # Brand settings
    brand_name: Optional[str] = None
    brand_voice: Optional[str] = None
    brand_guidelines: Optional[str] = None
    target_audience: Optional[str] = None
    
    # Environment-based overrides
    def __post_init__(self):
        """Override settings from environment variables."""
        # AI Provider overrides
        if os.getenv("CONTENT_WRITER_PROVIDER"):
            self.ai_provider.provider = os.getenv("CONTENT_WRITER_PROVIDER")
        if os.getenv("CONTENT_WRITER_MODEL"):
            self.ai_provider.model = os.getenv("CONTENT_WRITER_MODEL")
        if os.getenv("CONTENT_WRITER_TEMPERATURE"):
            self.ai_provider.temperature = float(os.getenv("CONTENT_WRITER_TEMPERATURE"))
        
        # Brand overrides
        if os.getenv("BRAND_NAME"):
            self.brand_name = os.getenv("BRAND_NAME")
        if os.getenv("BRAND_VOICE"):
            self.brand_voice = os.getenv("BRAND_VOICE")
        if os.getenv("TARGET_AUDIENCE"):
            self.target_audience = os.getenv("TARGET_AUDIENCE")


# Default configuration instance
DEFAULT_CONFIG = ContentWriterV2Config()


# Platform-specific configurations
INSTAGRAM_CONFIG = ContentWriterV2Config(
    social_media=SocialMediaConfig(
        default_platform=SocialPlatform.INSTAGRAM,
        include_hashtags=True,
        max_hashtags=30,
        include_emojis=False  # Changed to False for text-only content
    )
)

TWITTER_CONFIG = ContentWriterV2Config(
    social_media=SocialMediaConfig(
        default_platform=SocialPlatform.TWITTER,
        include_hashtags=True,
        max_hashtags=5,
        include_emojis=False
    )
)

LINKEDIN_CONFIG = ContentWriterV2Config(
    social_media=SocialMediaConfig(
        default_platform=SocialPlatform.LINKEDIN,
        include_hashtags=True,
        max_hashtags=10,
        include_emojis=False
    )
)