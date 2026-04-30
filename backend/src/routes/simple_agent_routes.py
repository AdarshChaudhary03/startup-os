"""Simplified agent routes for Content Writer and Social Publisher"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import uuid

from ..core.simple_agent_models import (
    SimpleContentWriterRequest,
    SimpleContentWriterResponse,
    SimpleSocialPublisherRequest,
    SimpleSocialPublisherResponse
)
from ..core.logging_config import log_orchestration_event
from ..core.agent_state_manager import state_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/simple", tags=["simple_agents"])


@router.post("/content_writer", response_model=SimpleContentWriterResponse)
async def simple_content_writer(
    req: SimpleContentWriterRequest,
    x_session_id: Optional[str] = Header(None)
):
    """Simplified Content Writer endpoint - just topic and mode"""
    request_id = str(uuid.uuid4())
    session_id = x_session_id or f"session-{int(datetime.now().timestamp() * 1000)}-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"[SIMPLE_API] Content Writer request: topic='{req.topic}', mode='{req.mode}'")
    
    try:
        # Import and use Content Writer v2
        from ..agents.content_writer_v2.main_agent import ContentWriterMainAgent
        from ..agents.content_writer_v2.config import DEFAULT_CONFIG
        
        # Create and initialize the agent
        main_agent = ContentWriterMainAgent(DEFAULT_CONFIG)
        await main_agent.initialize()
        
        # Map mode to category
        mode_to_category = {
            "instagram_post": "social_media",
            "linkedin_post": "social_media",
            "facebook_post": "social_media",
            "twitter_post": "social_media",
            "blog": "blog",
            "article": "blog",
            "reel_script": "script",
            "youtube_script": "script",
            "email": "marketing",
            "newsletter": "marketing"
        }
        
        category = mode_to_category.get(req.mode, "social_media")
        
        # Generate content
        result = await main_agent.generate_content(
            task=f"Write a {req.mode.replace('_', ' ')} about {req.topic}",
            request_id=request_id,
            category=category
        )
        
        content = result.get("content", "")
        
        # Extract hashtags if present
        import re
        hashtags = re.findall(r'#\w+', content)
        hashtags = [tag.strip('#') for tag in hashtags] if hashtags else None
        
        # Save to state manager for use by other agents
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=content,
            metadata={
                "mode": req.mode,
                "topic": req.topic,
                "request_id": request_id,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        logger.info(f"[SIMPLE_API] Content generated successfully for {req.mode} about {req.topic}")
        
        return SimpleContentWriterResponse(
            success=True,
            content=content,
            mode=req.mode,
            topic=req.topic,
            word_count=len(content.split()),
            hashtags=hashtags,
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"[SIMPLE_API] Content Writer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social_publisher", response_model=SimpleSocialPublisherResponse)
async def simple_social_publisher(
    req: SimpleSocialPublisherRequest,
    x_session_id: Optional[str] = Header(None)
):
    """Simplified Social Publisher endpoint - just caption, platform, and optional image"""
    request_id = str(uuid.uuid4())
    session_id = x_session_id or f"session-{int(datetime.now().timestamp() * 1000)}-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"[SIMPLE_API] Social Publisher request: platform='{req.platform}', caption_length={len(req.caption)}")
    
    try:
        # Import and use Social Media Publisher
        from ..agents.social_media_publisher.main_agent import SocialMediaPublisherMainAgent
        from ..agents.social_media_publisher.config import DEFAULT_CONFIG, SocialPlatform
        
        # Create and initialize the agent
        main_agent = SocialMediaPublisherMainAgent(DEFAULT_CONFIG)
        await main_agent.initialize()
        
        # Map platform string to enum
        platform_map = {
            "instagram": SocialPlatform.INSTAGRAM,
            "linkedin": SocialPlatform.LINKEDIN,
            "facebook": SocialPlatform.FACEBOOK,
            "twitter": SocialPlatform.TWITTER
        }
        
        platform_enum = platform_map.get(req.platform)
        if not platform_enum:
            raise ValueError(f"Unsupported platform: {req.platform}")
        
        # Prepare images list if image_url provided
        images = [req.image_url] if req.image_url else None
        
        # Publish content
        result = await main_agent.publish_content(
            content=req.caption,
            caption=req.caption,  # Explicitly pass caption
            request_id=request_id,
            platform=platform_enum,
            images=images,
            session_id=session_id
        )
        
        if result.get("success"):
            platform_result = result.get("results", {}).get(req.platform, {})
            
            # Save to state manager
            state_manager.save_agent_output(
                session_id=session_id,
                agent_id="social_publisher",
                output={
                    "platform": req.platform,
                    "post_id": platform_result.get("post_id", "unknown"),
                    "post_url": platform_result.get("url", ""),
                    "published_at": result.get("published_at")
                },
                metadata={
                    "request_id": request_id,
                    "caption_length": len(req.caption),
                    "has_image": bool(req.image_url)
                }
            )
            
            logger.info(f"[SIMPLE_API] Successfully published to {req.platform}")
            
            return SimpleSocialPublisherResponse(
                success=True,
                platform=req.platform,
                post_id=platform_result.get("post_id", "unknown"),
                post_url=platform_result.get("url", ""),
                published_at=result.get("published_at"),
                request_id=request_id
            )
        else:
            error_msg = result.get("errors", {}).get(req.platform, "Unknown error")
            logger.error(f"[SIMPLE_API] Publishing failed: {error_msg}")
            
            return SimpleSocialPublisherResponse(
                success=False,
                platform=req.platform,
                post_id="",
                post_url="",
                published_at=datetime.now(timezone.utc).isoformat(),
                request_id=request_id,
                error=error_msg
            )
            
    except Exception as e:
        logger.error(f"[SIMPLE_API] Social Publisher error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def simple_api_health():
    """Health check for simplified API endpoints"""
    return {
        "status": "healthy",
        "endpoints": [
            "/api/simple/content_writer",
            "/api/simple/social_publisher"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }