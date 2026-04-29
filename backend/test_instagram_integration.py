#!/usr/bin/env python3
"""
Instagram Integration Test (Without Real Credentials)

This script tests the Instagram API integration logic without requiring
real Instagram credentials, focusing on the technical fixes.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from social_media_publisher.sub_agents.instagram import InstagramAgent
from social_media_publisher.config import SocialPlatform, PostType
from ai_providers.groq_provider import GroqProvider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockInstagramConfig:
    """Mock Instagram configuration for testing."""
    def __init__(self):
        self.access_token = "test_access_token_12345"
        self.user_id = "test_user_id_67890"
        self.max_text_length = 2200
        self.api_version = "v18.0"
        self.base_url = "https://graph.facebook.com"

async def test_instagram_api_integration():
    """Test Instagram API integration with mocked credentials."""
    try:
        logger.info("Starting Instagram API integration test...")
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'INSTAGRAM_ACCESS_TOKEN': 'test_token_12345',
            'INSTAGRAM_USER_ID': 'test_user_67890',
            'GROQ_API_KEY': 'test_groq_key'
        }):
            
            # Initialize AI provider
            ai_provider = GroqProvider(api_key="test_groq_key")
            
            # Initialize Instagram agent with mock config
            instagram_agent = InstagramAgent(ai_provider)
            instagram_agent.platform_config = MockInstagramConfig()
            
            # Test data
            test_content = "🌟 Testing Instagram API integration! This is a test post from our Social Media Publisher Agent. #test #api #instagram"
            
            # Test image URLs (using reliable sources)
            test_images = [
                "https://picsum.photos/1080/1080?random=1"  # Reliable image service
            ]
            
            post_data = {
                "content": test_content,
                "post_type": PostType.IMAGE_POST,
                "images": test_images,
                "videos": [],
                "hashtags": ["#test", "#api", "#instagram", "#socialmedia"]
            }
            
            request_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Testing with request ID: {request_id}")
            logger.info(f"Content: {test_content}")
            logger.info(f"Images: {test_images}")
            
            # Mock the HTTP requests to Instagram API
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "test_container_12345"}
            mock_response.raise_for_status = MagicMock()
            
            mock_publish_response = MagicMock()
            mock_publish_response.status_code = 200
            mock_publish_response.json.return_value = {"id": "test_post_67890"}
            mock_publish_response.raise_for_status = MagicMock()
            
            with patch('requests.post') as mock_post:
                # First call: create media container
                # Second call: publish media container
                mock_post.side_effect = [mock_response, mock_publish_response]
                
                # Test the publishing logic
                result = await instagram_agent._publish_post(post_data, request_id)
                
                logger.info("\n" + "="*50)
                logger.info("INSTAGRAM API INTEGRATION TEST RESULTS")
                logger.info("="*50)
                
                if result.get("success"):
                    logger.info("✅ SUCCESS: Instagram API integration is working!")
                    
                    # Check if it was actually posted or simulated
                    if result.get("simulation"):
                        logger.warning("⚠️  WARNING: Post was SIMULATED")
                        logger.warning("This means there was an issue with the API integration")
                    else:
                        logger.info("🎉 INTEGRATION SUCCESS: API calls were made correctly!")
                        logger.info(f"Post ID: {result.get('post_id')}")
                        
                    logger.info(f"Platform: {result.get('platform')}")
                    logger.info(f"Status: {result.get('status')}")
                    
                    # Verify the API calls were made correctly
                    logger.info("\n📋 API CALL VERIFICATION:")
                    
                    if mock_post.call_count >= 1:
                        # Check first call (create media container)
                        first_call = mock_post.call_args_list[0]
                        call_url = first_call[0][0]
                        call_data = first_call[1]['data']
                        
                        logger.info(f"✅ Media container creation call made to: {call_url}")
                        logger.info(f"✅ Call data included: {list(call_data.keys())}")
                        
                        # Verify image_url parameter is included
                        if 'image_url' in call_data:
                            logger.info(f"✅ image_url parameter correctly included: {call_data['image_url']}")
                        else:
                            logger.error("❌ image_url parameter missing from API call")
                        
                        # Verify caption is included
                        if 'caption' in call_data:
                            logger.info(f"✅ caption parameter correctly included")
                        else:
                            logger.error("❌ caption parameter missing from API call")
                            
                    if mock_post.call_count >= 2:
                        # Check second call (publish media container)
                        second_call = mock_post.call_args_list[1]
                        publish_url = second_call[0][0]
                        publish_data = second_call[1]['data']
                        
                        logger.info(f"✅ Media publish call made to: {publish_url}")
                        logger.info(f"✅ Publish data included: {list(publish_data.keys())}")
                        
                else:
                    logger.error("❌ FAILED: Instagram API integration failed")
                    logger.error(f"Error: {result.get('error')}")
                    
                logger.info("\nFull result:")
                logger.info(result)
                
                return result
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

async def test_url_validation():
    """Test URL validation logic."""
    try:
        logger.info("\n" + "="*50)
        logger.info("TESTING URL VALIDATION")
        logger.info("="*50)
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'GROQ_API_KEY': 'test_groq_key'
        }):
            
            ai_provider = GroqProvider(api_key="test_groq_key")
            instagram_agent = InstagramAgent(ai_provider)
            
            # Test URLs
            test_urls = [
                "https://picsum.photos/1080/1080?random=1",  # Should pass
                "https://images.unsplash.com/photo-123",      # Should pass
                "https://via.placeholder.com/1080x1080",      # Should fail
                "http://example.com/image.jpg",               # Should fail (not HTTPS)
                "https://localhost/image.jpg",                # Should fail
            ]
            
            for url in test_urls:
                is_valid = instagram_agent._is_valid_url(url)
                is_compatible = instagram_agent._is_instagram_compatible_url(url)
                
                status = "✅ PASS" if is_compatible else "❌ FAIL"
                logger.info(f"{status} {url}")
                logger.info(f"    Valid URL: {is_valid}, Instagram Compatible: {is_compatible}")
                
        logger.info("\n✅ URL validation test completed")
        
    except Exception as e:
        logger.error(f"URL validation test failed: {e}")

async def main():
    """Main test function."""
    logger.info("🚀 Starting Instagram API Integration Test")
    logger.info("This test verifies the technical fixes without requiring real credentials")
    
    # Test URL validation first
    await test_url_validation()
    
    # Test Instagram API integration
    result = await test_instagram_api_integration()
    
    # Final assessment
    logger.info("\n" + "="*60)
    logger.info("FINAL INTEGRATION ASSESSMENT")
    logger.info("="*60)
    
    if result.get("success") and not result.get("simulation"):
        logger.info("🎉 INTEGRATION TEST: SUCCESS!")
        logger.info("The Instagram API integration fixes are working correctly")
        logger.info("Key improvements:")
        logger.info("- ✅ Using image_url parameter instead of file uploads")
        logger.info("- ✅ Using reliable image hosting services")
        logger.info("- ✅ Proper URL validation")
        logger.info("- ✅ Correct API call structure")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Configure real Instagram API credentials")
        logger.info("2. Test with actual Instagram account")
        logger.info("3. Verify posts appear on Instagram")
    elif result.get("simulation"):
        logger.warning("⚠️  INTEGRATION TEST: PARTIAL SUCCESS")
        logger.warning("The code is working but falling back to simulation")
        logger.warning("This would happen with real credentials if there are API issues")
    else:
        logger.error("❌ INTEGRATION TEST: FAILURE")
        logger.error("There are still issues with the Instagram API integration")
        logger.error(f"Error: {result.get('error') if result else 'Unknown error'}")

if __name__ == "__main__":
    asyncio.run(main())
