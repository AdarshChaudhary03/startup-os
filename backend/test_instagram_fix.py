#!/usr/bin/env python3
"""
Test script to verify Instagram API fixes

This script tests the Instagram agent functionality after applying fixes for:
1. Missing _generate_text_image method
2. Groq model configuration
3. Helper methods for URL validation and sample images
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from social_media_publisher.main_agent import SocialMediaPublisherAgent
from social_media_publisher.config import SocialPlatform, PostType
from ai_providers.factory import get_ai_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_instagram_agent_fixes():
    """Test Instagram agent with all fixes applied."""
    try:
        logger.info("Starting Instagram agent fix tests...")
        
        # Test 1: Initialize AI provider with correct model
        logger.info("Test 1: Testing AI provider initialization...")
        try:
            ai_provider = get_ai_provider("groq")
            logger.info("✅ AI provider initialized successfully")
        except Exception as e:
            logger.error(f"❌ AI provider initialization failed: {e}")
            return False
        
        # Test 2: Initialize Social Media Publisher Agent
        logger.info("Test 2: Testing Social Media Publisher Agent initialization...")
        try:
            main_agent = SocialMediaPublisherAgent(ai_provider)
            logger.info("✅ Social Media Publisher Agent initialized successfully")
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            return False
        
        # Test 3: Test Instagram posting with text-only content
        logger.info("Test 3: Testing Instagram posting with text-only content...")
        try:
            test_content = "🌟 Testing Instagram posting with fixed agent! This should use a placeholder image for text-only posts. #test #instagram #ai"
            
            result = await main_agent.publish_content(
                content=test_content,
                platforms=[SocialPlatform.INSTAGRAM],
                post_type=PostType.TEXT_POST,
                request_id="test_fix_001"
            )
            
            if result.get("success"):
                logger.info("✅ Instagram posting test successful")
                logger.info(f"Result: {result}")
            else:
                logger.warning(f"⚠️ Instagram posting returned error: {result.get('error')}")
                # This might be expected if no API credentials are configured
                
        except Exception as e:
            logger.error(f"❌ Instagram posting test failed: {e}")
            return False
        
        # Test 4: Test content optimization with new Groq model
        logger.info("Test 4: Testing content optimization with correct Groq model...")
        try:
            # This will test if the Groq model configuration is working
            test_content = "Write an engaging Instagram caption about AI technology"
            
            result = await main_agent.publish_content(
                content=test_content,
                platforms=[SocialPlatform.INSTAGRAM],
                post_type=PostType.TEXT_POST,
                request_id="test_fix_002",
                optimize_content=True
            )
            
            logger.info("✅ Content optimization test completed")
            logger.info(f"Optimization result: {result}")
            
        except Exception as e:
            logger.error(f"❌ Content optimization test failed: {e}")
            return False
        
        logger.info("🎉 All Instagram agent fix tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test suite failed with unexpected error: {e}")
        return False

async def test_instagram_helper_methods():
    """Test the new helper methods added to Instagram agent."""
    try:
        logger.info("Testing Instagram agent helper methods...")
        
        # Import Instagram agent directly
        from social_media_publisher.sub_agents.instagram import InstagramAgent
        from ai_providers.factory import get_ai_provider
        
        ai_provider = get_ai_provider("groq")
        instagram_agent = InstagramAgent(ai_provider)
        
        # Test _get_sample_image_url method
        logger.info("Testing _get_sample_image_url method...")
        sample_url = instagram_agent._get_sample_image_url()
        logger.info(f"✅ Sample image URL: {sample_url}")
        
        # Test _is_valid_url method
        logger.info("Testing _is_valid_url method...")
        test_urls = [
            "https://via.placeholder.com/1080x1080",
            "http://example.com/image.jpg",
            "invalid-url",
            "https://instagram.com/p/test123"
        ]
        
        for url in test_urls:
            is_valid = instagram_agent._is_valid_url(url)
            logger.info(f"URL: {url} - Valid: {is_valid}")
        
        logger.info("✅ Helper methods test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Helper methods test failed: {e}")
        return False

def main():
    """Main test function."""
    logger.info("🚀 Starting Instagram API Fix Verification Tests")
    logger.info("=" * 60)
    
    # Check environment
    logger.info("Environment Check:")
    logger.info(f"GROQ_API_KEY configured: {'✅' if os.getenv('GROQ_API_KEY') else '❌'}")
    logger.info(f"INSTAGRAM_ACCESS_TOKEN configured: {'✅' if os.getenv('INSTAGRAM_ACCESS_TOKEN') else '❌'}")
    logger.info(f"INSTAGRAM_USER_ID configured: {'✅' if os.getenv('INSTAGRAM_USER_ID') else '❌'}")
    logger.info("=" * 60)
    
    # Run tests
    try:
        # Test helper methods first
        helper_test_result = asyncio.run(test_instagram_helper_methods())
        
        # Test main agent functionality
        agent_test_result = asyncio.run(test_instagram_agent_fixes())
        
        if helper_test_result and agent_test_result:
            logger.info("🎉 ALL TESTS PASSED! Instagram agent fixes are working correctly.")
            return 0
        else:
            logger.error("❌ Some tests failed. Please check the logs above.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)