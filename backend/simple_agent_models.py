"""Simplified models for agent APIs"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class SimpleContentWriterRequest(BaseModel):
    """Simplified Content Writer API request model"""
    topic: str = Field(..., description="Topic to write about")
    mode: Literal[
        "instagram_post",
        "linkedin_post", 
        "facebook_post",
        "twitter_post",
        "blog",
        "article",
        "reel_script",
        "youtube_script",
        "email",
        "newsletter"
    ] = Field(..., description="Type of content to generate")
    
    class Config:
        schema_extra = {
            "example": {
                "topic": "GenAI for students",
                "mode": "instagram_post"
            }
        }


class SimpleContentWriterResponse(BaseModel):
    """Simplified Content Writer API response model"""
    success: bool
    content: str
    mode: str
    topic: str
    word_count: int
    hashtags: Optional[list[str]] = None
    request_id: str
    timestamp: str
    


class SimpleSocialPublisherRequest(BaseModel):
    """Simplified Social Publisher API request model"""
    caption: str = Field(..., description="Caption/content to publish")
    platform: Literal[
        "instagram",
        "linkedin",
        "facebook",
        "twitter"
    ] = Field(..., description="Social media platform")
    image_url: Optional[str] = Field(None, description="Optional image URL")
    
    class Config:
        schema_extra = {
            "example": {
                "caption": "🚀 Discover the power of AI with GenAI for students! #AI #GenAI #Students",
                "platform": "instagram",
                "image_url": "https://example.com/image.jpg"
            }
        }


class SimpleSocialPublisherResponse(BaseModel):
    """Simplified Social Publisher API response model"""
    success: bool
    platform: str
    post_id: str
    post_url: str
    published_at: str
    request_id: str
    error: Optional[str] = None