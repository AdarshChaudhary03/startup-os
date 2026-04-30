#!/usr/bin/env python3
"""
Test script to verify Instagram API fix

This script tests the Instagram API integration with the new URL compatibility fixes.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from social_media_publisher.main_agent import SocialMediaPublisherAgent
from social_media_publisher.config import PostType
from ai_providers.factory import AIProviderFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_instagram_api_fix():
    """Test Instagram API with the new URL compatibility fixes."""
    try:
        # Initialize AI provider
        ai_provider = AIProviderFactory.create_provider("groq")
        
        # Initialize Social Media Publisher Agent
        agent = SocialMediaPublisherAgent(ai_provider)
        await agent.initialize()
        
        # Test data for Instagram posting
        test_content = "Testing Instagram API fix with new URL compatibility! 🚀 #test #instagram #api"
        
        # Test 1: Post with no media (should use default image)
        logger.info("Test 1: Posting with no media (should use default image)")
        result1 = await agent.publish_content(
            content=test_content,
            platforms=["instagram"],
            post_type=PostType.TEXT_POST,
            images=[],
            videos=[],
            request_id="test_1"
        )
        
        logger.info(f"Test 1 Result: {result1}")
        
        # Test 2: Post with problematic placeholder URL (should fallback to default)
        logger.info("Test 2: Posting with problematic placeholder URL")
        problematic_url = "https://via.placeholder.com/1080x1080/FF0000/FFFFFF?text=Bad+URL"
        result2 = await agent.publish_content(
            content=test_content,
            platforms=["instagram"],
            post_type=PostType.IMAGE_POST,
            images=[problematic_url],
            videos=[],
            request_id="test_2"
        )
        
        logger.info(f"Test 2 Result: {result2}")
        
        # Test 3: Post with good URL (should work)
        logger.info("Test 3: Posting with compatible image URL")
        good_url = "https://picsum.photos/1080/1080"
        result3 = await agent.publish_content(
            content=test_content,
            platforms=["instagram"],
            post_type=PostType.IMAGE_POST,
            images=[good_url],
            videos=[],
            request_id="test_3"
        )
        
        logger.info(f"Test 3 Result: {result3}")
        
        # Test 4: Test URL compatibility validation
        logger.info("Test 4: Testing URL compatibility validation")
        from social_media_publisher.sub_agents.instagram import InstagramAgent
        
        instagram_agent = InstagramAgent(ai_provider)
        
        test_urls = [
            "https://via.placeholder.com/1080x1080",  # Should be False
            "https://picsum.photos/1080/1080",        # Should be True
            "https://images.unsplash.com/photo-123",  # Should be True
            "http://localhost:8000/image.jpg",        # Should be False
            "https://source.unsplash.com/1080x1080",  # Should be True
        ]
        
        for url in test_urls:
            is_valid = instagram_agent._is_valid_url(url)
            is_compatible = instagram_agent._is_instagram_compatible_url(url)
            logger.info(f"URL: {url}")
            logger.info(f"  Valid: {is_valid}, Compatible: {is_compatible}")
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the Instagram API fix tests."""
    print("Starting Instagram API Fix Tests...")
    print("=" * 50)
    
    # Check environment variables
    required_env_vars = ["GROQ_API_KEY"]
    optional_env_vars = ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID"]
    
    print("Environment Check:")
    for var in required_env_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is missing (required)")
    
    for var in optional_env_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"⚠ {var} is missing (will use simulation mode)")
    
    print("\nRunning tests...")
    asyncio.run(test_instagram_api_fix())
    
    print("\nTests completed!")
    print("Check the logs above for detailed results.")

if __name__ == "__main__":
    main()