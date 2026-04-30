"""Simplified API Models for Agent APIs

These models define the simplified request/response structures for agent APIs.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime


# Social Publisher API Models
class SimpleSocialPublisherRequest(BaseModel):
    """Simplified request model for Social Publisher API."""
    caption: str = Field(..., description="Content/caption to publish")
    image_url: Optional[str] = Field(None, description="Optional image URL")
    platform: Literal["instagram", "linkedin", "facebook"] = Field(
        ..., description="Target social media platform"
    )


class SimpleSocialPublisherResponse(BaseModel):
    """Response model for Social Publisher API."""
    success: bool
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    platform: str
    published_at: Optional[str] = None
    error: Optional[str] = None
    message: str


# Content Writer API Models  
class SimpleContentWriterRequest(BaseModel):
    """Simplified request model for Content Writer API."""
    topic: str = Field(..., description="Topic to write about")
    mode: Literal[
        "reel_script",
        "blog", 
        "instagram_post",
        "linkedin_post",
        "facebook_post"
    ] = Field(..., description="Type of content to generate")


class SimpleContentWriterResponse(BaseModel):
    """Response model for Content Writer API."""
    success: bool
    content: Optional[str] = None
    word_count: Optional[int] = None
    hashtags: Optional[list[str]] = None
    mode: str
    error: Optional[str] = None
    message: str
    generated_at: Optional[str] = None


# API Matrix Entry Model
class APIMatrixEntry(BaseModel):
    """Model for API reference matrix entry."""
    api_name: str
    endpoint: str
    method: Literal["GET", "POST", "PUT", "DELETE"]
    description: str
    request_body: Dict[str, Any]
    response_format: Dict[str, Any]
    example_request: Dict[str, Any]
    example_response: Dict[str, Any]
    notes: Optional[str] = None