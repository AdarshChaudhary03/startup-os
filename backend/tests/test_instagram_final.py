#!/usr/bin/env python3
"""
Final Instagram API Test Script

This script tests the Instagram API integration with proper image URLs
and verifies that actual posting works instead of simulation.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from social_media_publisher.main_agent import SocialMediaPublisherMainAgent
from ai_providers.factory import AIProviderFactory
from social_media_publisher.config import SocialPlatform, PostType

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_instagram_posting():
    """Test Instagram posting with proper image URLs."""
    try:
        logger.info("Starting Instagram API test...")
        
        # Initialize AI provider
        ai_provider = AIProviderFactory.create_provider("groq")
        
        # Initialize Social Media Publisher Agent
        publisher = SocialMediaPublisherMainAgent(ai_provider)
        
        # Test data with reliable image URL
        test_content = "🌟 Testing Instagram API integration! This is a test post from our Social Media Publisher Agent. #test #api #instagram"
        
        # Use reliable image URLs that Instagram can access
        test_images = [
            "https://picsum.photos/1080/1080?random=1",  # Reliable image service
            # Alternative reliable URLs:
            # "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1080&fit=crop",
            # "https://source.unsplash.com/1080x1080/?nature"
        ]
        
        publish_request = {
            "content": test_content,
            "platform": "instagram",
            "post_type": PostType.IMAGE_POST,
            "images": test_images,
            "videos": [],
            "target_audience": "general",
            "hashtags": ["#test", "#api", "#instagram", "#socialmedia"],
            "schedule_time": None  # Immediate posting
        }
        
        request_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Publishing test post with request ID: {request_id}")
        logger.info(f"Content: {test_content}")
        logger.info(f"Images: {test_images}")
        
        # Publish the content
        result = await publisher.publish_content(
            content=test_content,
            platform=SocialPlatform.INSTAGRAM,
            request_id=request_id,
            post_type=PostType.IMAGE_POST,
            images=test_images,
            target_audience="general"
        )
        
        logger.info("\n" + "="*50)
        logger.info("INSTAGRAM API TEST RESULTS")
        logger.info("="*50)
        
        if result.get("success"):
            logger.info("✅ SUCCESS: Instagram posting completed!")
            
            # Check if it was actually posted or simulated
            if result.get("simulation"):
                logger.warning("⚠️  WARNING: Post was SIMULATED, not actually posted to Instagram")
                logger.warning("This means the Instagram API integration is not working properly")
                logger.warning("Check your Instagram API credentials and configuration")
            else:
                logger.info("🎉 ACTUAL POST: Content was successfully posted to Instagram!")
                logger.info(f"Post ID: {result.get('post_id')}")
                logger.info(f"Instagram URL: {result.get('url')}")
                
            logger.info(f"Platform: {result.get('platform')}")
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Published at: {result.get('published_at')}")
            
        else:
            logger.error("❌ FAILED: Instagram posting failed")
            logger.error(f"Error: {result.get('error')}")
            
        logger.info("\nFull result:")
        logger.info(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

async def test_instagram_credentials():
    """Test Instagram API credentials."""
    try:
        logger.info("Testing Instagram API credentials...")
        
        # Check environment variables
        instagram_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        instagram_user_id = os.getenv("INSTAGRAM_USER_ID")
        
        logger.info(f"Instagram Access Token: {'✅ Set' if instagram_access_token else '❌ Missing'}")
        logger.info(f"Instagram User ID: {'✅ Set' if instagram_user_id else '❌ Missing'}")
        
        if not instagram_access_token:
            logger.error("INSTAGRAM_ACCESS_TOKEN environment variable is not set")
            logger.error("Please set your Instagram API credentials in .env file")
            
        if not instagram_user_id:
            logger.error("INSTAGRAM_USER_ID environment variable is not set")
            logger.error("Please set your Instagram User ID in .env file")
            
        return instagram_access_token and instagram_user_id
        
    except Exception as e:
        logger.error(f"Credentials test failed: {e}")
        return False

async def main():
    """Main test function."""
    logger.info("🚀 Starting Instagram API Final Test")
    logger.info("This test will verify actual Instagram posting functionality")
    
    # Test credentials first
    credentials_ok = await test_instagram_credentials()
    
    if not credentials_ok:
        logger.error("❌ Instagram credentials are not properly configured")
        logger.error("Please configure your Instagram API credentials before running this test")
        return
    
    # Test Instagram posting
    result = await test_instagram_posting()
    
    # Final assessment
    logger.info("\n" + "="*60)
    logger.info("FINAL TEST ASSESSMENT")
    logger.info("="*60)
    
    if result.get("success"):
        if result.get("simulation"):
            logger.warning("⚠️  TEST RESULT: SIMULATION MODE")
            logger.warning("The Instagram agent is working but falling back to simulation")
            logger.warning("This indicates an issue with Instagram API integration")
            logger.warning("Possible causes:")
            logger.warning("- Invalid Instagram access token")
            logger.warning("- Instagram app not properly configured")
            logger.warning("- Instagram API permissions issues")
            logger.warning("- Image URL not accessible by Instagram")
        else:
            logger.info("🎉 TEST RESULT: SUCCESS!")
            logger.info("Instagram API integration is working correctly")
            logger.info("Content was actually posted to Instagram")
    else:
        logger.error("❌ TEST RESULT: FAILURE")
        logger.error("Instagram API integration is not working")
        logger.error(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
