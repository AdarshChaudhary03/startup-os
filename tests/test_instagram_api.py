#!/usr/bin/env python3
"""
Test script for Instagram API integration

This script tests the Instagram Graph API functionality of the Social Media Publisher Agent.
It can be used to verify that the Instagram integration is working correctly.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from social_media_publisher.main_agent import SocialMediaPublisherAgent
from social_media_publisher.config import SocialPlatform, PostType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_instagram_credentials() -> bool:
    """Check if Instagram API credentials are configured."""
    required_vars = [
        'INSTAGRAM_ACCESS_TOKEN',
        'INSTAGRAM_USER_ID',
        'INSTAGRAM_APP_ID',
        'INSTAGRAM_APP_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing Instagram credentials: {', '.join(missing_vars)}")
        logger.info("Instagram will run in simulation mode")
        return False
    
    logger.info("Instagram API credentials found")
    return True


async def test_instagram_text_post():
    """Test Instagram text post (will include placeholder image)."""
    logger.info("Testing Instagram text post...")
    
    agent = SocialMediaPublisherAgent()
    
    result = await agent.publish_content(
        content="Testing Instagram API integration! 🚀 This is a test post from our Social Media Publisher Agent.",
        platform=SocialPlatform.INSTAGRAM,
        post_type=PostType.TEXT_POST,
        target_audience="tech enthusiasts",
        request_id="test_text_post_001"
    )
    
    logger.info(f"Text post result: {result}")
    return result


async def test_instagram_image_post():
    """Test Instagram image post."""
    logger.info("Testing Instagram image post...")
    
    agent = SocialMediaPublisherAgent()
    
    # Using a placeholder image for testing
    test_image_url = "https://via.placeholder.com/1080x1080/4267B2/FFFFFF?text=Test+Post"
    
    result = await agent.publish_content(
        content="Beautiful sunset today! 🌅 Testing our Instagram image posting capabilities.",
        platform=SocialPlatform.INSTAGRAM,
        post_type=PostType.IMAGE_POST,
        images=[test_image_url],
        target_audience="photography lovers",
        request_id="test_image_post_001"
    )
    
    logger.info(f"Image post result: {result}")
    return result


async def test_instagram_with_hashtags():
    """Test Instagram post with custom hashtags."""
    logger.info("Testing Instagram post with hashtags...")
    
    agent = SocialMediaPublisherAgent()
    
    result = await agent.publish_content(
        content="Excited to share our latest project! Working on AI-powered social media automation. 🤖✨",
        platform=SocialPlatform.INSTAGRAM,
        post_type=PostType.TEXT_POST,
        hashtags=["AI", "automation", "socialmedia", "tech", "innovation", "startup"],
        target_audience="entrepreneurs and developers",
        request_id="test_hashtags_001"
    )
    
    logger.info(f"Hashtags post result: {result}")
    return result


async def test_instagram_scheduling():
    """Test Instagram post scheduling."""
    logger.info("Testing Instagram post scheduling...")
    
    agent = SocialMediaPublisherAgent()
    
    # Schedule for 1 hour from now
    schedule_time = datetime.now().replace(microsecond=0)
    schedule_time = schedule_time.replace(hour=schedule_time.hour + 1)
    
    result = await agent.schedule_content(
        content="This is a scheduled post! 📅 Testing our scheduling capabilities.",
        platform=SocialPlatform.INSTAGRAM,
        post_type=PostType.TEXT_POST,
        schedule_time=schedule_time,
        target_audience="general audience",
        request_id="test_schedule_001"
    )
    
    logger.info(f"Scheduling result: {result}")
    return result


async def test_instagram_analytics():
    """Test Instagram analytics retrieval."""
    logger.info("Testing Instagram analytics...")
    
    from social_media_publisher.sub_agents.instagram import InstagramAgent
    from social_media_publisher.config import DEFAULT_CONFIG
    
    agent = InstagramAgent(DEFAULT_CONFIG)
    await agent.initialize()
    
    # Test with a dummy post ID
    analytics = await agent.get_post_analytics("ig_test_post_123")
    
    logger.info(f"Analytics result: {analytics}")
    return analytics


async def run_all_tests():
    """Run all Instagram API tests."""
    logger.info("Starting Instagram API tests...")
    logger.info("=" * 50)
    
    # Check credentials
    has_credentials = check_instagram_credentials()
    
    if not has_credentials:
        logger.info("Running tests in simulation mode")
    else:
        logger.info("Running tests with actual Instagram API")
    
    logger.info("=" * 50)
    
    tests = [
        ("Text Post", test_instagram_text_post),
        ("Image Post", test_instagram_image_post),
        ("Hashtags Post", test_instagram_with_hashtags),
        ("Scheduling", test_instagram_scheduling),
        ("Analytics", test_instagram_analytics)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n🧪 Running {test_name} test...")
            result = await test_func()
            results[test_name] = {
                "status": "success",
                "result": result
            }
            logger.info(f"✅ {test_name} test completed successfully")
        except Exception as e:
            logger.error(f"❌ {test_name} test failed: {e}")
            results[test_name] = {
                "status": "failed",
                "error": str(e)
            }
    
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    for test_name, result in results.items():
        status_emoji = "✅" if result["status"] == "success" else "❌"
        logger.info(f"{status_emoji} {test_name}: {result['status']}")
        if result["status"] == "failed":
            logger.info(f"   Error: {result['error']}")
    
    return results


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    asyncio.run(run_all_tests())
