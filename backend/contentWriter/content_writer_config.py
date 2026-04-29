"""Content Writer Agent Configuration

Configuration settings for the Content Writer Agent including
LLM settings, content types, and output formatting options.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ContentType(Enum):
    """Supported content types for the Content Writer Agent."""
    BLOG_POST = "blog_post"
    ARTICLE = "article"
    NEWSLETTER = "newsletter"
    STORY = "story"
    LONG_FORM = "long_form"
    SOCIAL_COPY = "social_copy"
    MARKETING_COPY = "marketing_copy"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    PRODUCT_DESCRIPTION = "product_description"
    EMAIL_SEQUENCE = "email_sequence"


class ToneOfVoice(Enum):
    """Available tone of voice options."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    PERSUASIVE = "persuasive"
    INFORMATIVE = "informative"
    ENGAGING = "engaging"


@dataclass
class ContentWriterConfig:
    """Configuration class for Content Writer Agent."""
    
    # LLM Provider Settings
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 2048
    
    # Content Settings
    default_content_type: ContentType = ContentType.BLOG_POST
    default_tone: ToneOfVoice = ToneOfVoice.PROFESSIONAL
    default_word_count: int = 600
    
    # Output Settings
    include_seo_metadata: bool = True
    include_outline: bool = True
    include_call_to_action: bool = True
    
    # Quality Settings
    enable_fact_checking: bool = True
    enable_plagiarism_check: bool = False
    enable_readability_score: bool = True
    
    # Brand Guidelines
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    key_messages: List[str] = None
    
    # Content Structure
    min_word_count: int = 200
    max_word_count: int = 3000
    preferred_paragraph_length: int = 3  # sentences per paragraph
    
    # SEO Settings
    target_keywords: List[str] = None
    meta_description_length: int = 160
    title_length_limit: int = 60
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.key_messages is None:
            self.key_messages = []
        if self.target_keywords is None:
            self.target_keywords = []
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for serialization."""
        return {
            'provider': self.provider,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'default_content_type': self.default_content_type.value,
            'default_tone': self.default_tone.value,
            'default_word_count': self.default_word_count,
            'include_seo_metadata': self.include_seo_metadata,
            'include_outline': self.include_outline,
            'include_call_to_action': self.include_call_to_action,
            'enable_fact_checking': self.enable_fact_checking,
            'enable_plagiarism_check': self.enable_plagiarism_check,
            'enable_readability_score': self.enable_readability_score,
            'brand_voice': self.brand_voice,
            'target_audience': self.target_audience,
            'key_messages': self.key_messages,
            'min_word_count': self.min_word_count,
            'max_word_count': self.max_word_count,
            'preferred_paragraph_length': self.preferred_paragraph_length,
            'target_keywords': self.target_keywords,
            'meta_description_length': self.meta_description_length,
            'title_length_limit': self.title_length_limit
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContentWriterConfig':
        """Create config from dictionary."""
        config = cls()
        
        # Update fields from dictionary
        for key, value in data.items():
            if hasattr(config, key):
                if key == 'default_content_type':
                    setattr(config, key, ContentType(value))
                elif key == 'default_tone':
                    setattr(config, key, ToneOfVoice(value))
                else:
                    setattr(config, key, value)
        
        return config


# Default configuration instance
DEFAULT_CONFIG = ContentWriterConfig(
    provider="groq",
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=2048,
    default_content_type=ContentType.BLOG_POST,
    default_tone=ToneOfVoice.PROFESSIONAL,
    default_word_count=600,
    include_seo_metadata=True,
    include_outline=True,
    include_call_to_action=True,
    enable_fact_checking=True,
    enable_readability_score=True,
    min_word_count=200,
    max_word_count=3000,
    preferred_paragraph_length=3,
    meta_description_length=160,
    title_length_limit=60
)
