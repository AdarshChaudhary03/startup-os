#!/usr/bin/env python3
"""
Test script for Instagram API with local image file upload.
This script tests the fixed Instagram agent that uses actual local files instead of URLs.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from social_media_publisher.main_agent import SocialMediaPublisherMainAgent
from ai_providers.factory import AIProviderFactory
from social_media_publisher.config import PostType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_instagram_local_image():
    """Test Instagram posting with local image file."""
    try:
        # Initialize AI provider
        ai_provider = AIProviderFactory.create_provider("groq")
        
        # Initialize Social Media Publisher Agent
        publisher = SocialMediaPublisherMainAgent(ai_provider)
        
        # Test content for Instagram
        test_content = "Beautiful sunny day in Delhi! ☀️ Perfect weather for exploring the city. #Delhi #SunnyDay #Beautiful"
        
        # Test with local image file
        test_data = {
            "content": test_content,
            "platforms": ["instagram"],
            "post_type": PostType.IMAGE_POST,
            "images": ["/startup-os/backend/assets/images.jpg"],  # Use local file path
            "videos": [],
            "target_audience": "travel enthusiasts",
            "hashtags": ["#Delhi", "#SunnyDay", "#Beautiful", "#Travel", "#India"]
        }
        
        logger.info("Testing Instagram posting with local image file...")
        logger.info(f"Content: {test_content}")
        logger.info(f"Image path: {test_data['images'][0]}")
        
        # Check if image file exists
        image_path = test_data['images'][0]
        if os.path.exists(image_path):
            logger.info(f"✅ Image file found: {image_path}")
            file_size = os.path.getsize(image_path)
            logger.info(f"📁 File size: {file_size} bytes")
        else:
            logger.warning(f"⚠️ Image file not found: {image_path}")
            logger.info("The Instagram agent will create a default image automatically")
        
        # Publish content
        result = await publisher.publish_content(
            content=test_data["content"],
            platforms=test_data["platforms"],
            post_type=test_data["post_type"],
            images=test_data["images"],
            videos=test_data["videos"],
            target_audience=test_data["target_audience"],
            hashtags=test_data["hashtags"],
            request_id="test_local_image_001"
        )
        
        # Display results
        logger.info("\n" + "="*50)
        logger.info("INSTAGRAM POSTING RESULTS")
        logger.info("="*50)
        
        if result.get("success"):
            logger.info("✅ Publishing successful!")
            
            for platform_result in result.get("results", []):
                platform = platform_result.get("platform", "unknown")
                success = platform_result.get("success", False)
                
                logger.info(f"\n📱 Platform: {platform.upper()}")
                logger.info(f"Status: {'✅ Success' if success else '❌ Failed'}")
                
                if success:
                    post_id = platform_result.get("post_id", "N/A")
                    url = platform_result.get("url", "N/A")
                    status = platform_result.get("status", "N/A")
                    simulation = platform_result.get("simulation", False)
                    
                    logger.info(f"Post ID: {post_id}")
                    logger.info(f"URL: {url}")
                    logger.info(f"Status: {status}")
                    logger.info(f"Mode: {'🔧 Simulation' if simulation else '🚀 Live API'}")
                    
                    if simulation:
                        note = platform_result.get("note", "")
                        if note:
                            logger.info(f"Note: {note}")
                    
                    # Show Instagram-specific data
                    instagram_data = platform_result.get("instagram_data", {})
                    if instagram_data:
                        logger.info(f"Caption: {instagram_data.get('caption', 'N/A')[:100]}...")
                        logger.info(f"Media Type: {instagram_data.get('media_type', 'N/A')}")
                else:
                    error = platform_result.get("error", "Unknown error")
                    logger.error(f"❌ Error: {error}")
        else:
            logger.error("❌ Publishing failed!")
            error = result.get("error", "Unknown error")
            logger.error(f"Error: {error}")
        
        logger.info("\n" + "="*50)
        logger.info("TEST COMPLETED")
        logger.info("="*50)
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test function."""
    logger.info("🧪 Starting Instagram Local Image Test")
    logger.info(f"📅 Test started at: {datetime.now()}")
    
    # Check environment
    instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    instagram_user_id = os.getenv("INSTAGRAM_USER_ID")
    
    if instagram_token and instagram_user_id:
        logger.info("🔑 Instagram API credentials found - will attempt live posting")
    else:
        logger.info("🔧 No Instagram API credentials - will use simulation mode")
        logger.info("To enable live posting, set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID")
    
    # Run test
    result = await test_instagram_local_image()
    
    if result:
        logger.info("\n✅ Test completed successfully!")
    else:
        logger.error("\n❌ Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
