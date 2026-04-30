#!/usr/bin/env python3
"""
Test CEO Agent Orchestration Integration

This test verifies that the CEO agent properly calls the orchestrate endpoint
after gathering requirements from the user through the chat interface.
"""

import asyncio
import json
import httpx
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


async def test_ceo_chat_to_orchestration():
    """Test the complete flow from CEO chat to orchestration"""
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Step 1: Start CEO chat session
        logger.info("Step 1: Starting CEO chat session...")
        start_response = await client.post(
            f"{BASE_URL}/api/ceo/chat/start",
            json={
                "initial_message": "I need to create a landing page for my startup",
                "user_context": {"test": True}
            }
        )
        
        if start_response.status_code != 200:
            logger.error(f"Failed to start chat: {start_response.status_code} - {start_response.text}")
            return False
            
        chat_data = start_response.json()
        conversation_id = chat_data["conversation_id"]
        logger.info(f"Chat started with conversation_id: {conversation_id}")
        logger.info(f"Initial message: {chat_data['message']}")
        
        # Step 2: Send responses to CEO questions
        logger.info("\nStep 2: Answering CEO questions...")
        
        # Simulate user responses
        responses = [
            "The purpose is to attract potential customers and showcase our AI-powered analytics platform",
            "Our target audience is small to medium-sized businesses looking for data insights",
            "We need a modern, professional design with sections for features, pricing, and testimonials",
            "We'd like to launch within 2 weeks",
            "It should be mobile-responsive and SEO-optimized"
        ]
        
        for i, response_text in enumerate(responses):
            # Send message
            message_response = await client.post(
                f"{BASE_URL}/api/ceo/chat/message",
                json={
                    "conversation_id": conversation_id,
                    "message": response_text
                }
            )
            
            if message_response.status_code != 200:
                logger.error(f"Failed to send message: {message_response.status_code}")
                return False
                
            message_data = message_response.json()
            logger.info(f"Response {i+1}: {response_text[:50]}...")
            logger.info(f"CEO reply: {message_data.get('message', '')[:100]}...")
            
            # Check if requirements are complete
            if message_data.get("state") == "requirements_complete":
                logger.info("Requirements gathering complete!")
                break
                
            # Small delay between messages
            await asyncio.sleep(0.5)
        
        # Step 3: Finalize requirements and trigger orchestration
        logger.info("\nStep 3: Finalizing requirements...")
        finalize_response = await client.post(
            f"{BASE_URL}/api/ceo/chat/{conversation_id}/finalize"
        )
        
        if finalize_response.status_code != 200:
            logger.error(f"Failed to finalize: {finalize_response.status_code} - {finalize_response.text}")
            return False
            
        finalize_data = finalize_response.json()
        logger.info("Finalization response received")
        logger.info(f"Success: {finalize_data.get('success', False)}")
        
        # Check if orchestration was called
        orchestration_result = finalize_data.get("orchestration_result")
        if orchestration_result:
            if orchestration_result.get("error"):
                logger.error(f"Orchestration error: {orchestration_result['error']}")
                logger.error(f"Details: {orchestration_result.get('details', 'No details')}")
                return False
            else:
                logger.info("✅ Orchestration successful!")
                logger.info(f"Orchestration result: {json.dumps(orchestration_result, indent=2)}")
                return True
        else:
            logger.warning("No orchestration result found in response")
            return False


async def test_direct_orchestration():
    """Test calling orchestration endpoint directly"""
    
    logger.info("\nTesting direct orchestration endpoint...")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{BASE_URL}/api/orchestrate",
            json={
                "task": "Create a simple landing page",
                "agent_id": None
            }
        )
        
        if response.status_code == 200:
            logger.info("✅ Direct orchestration successful")
            logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            logger.error(f"❌ Direct orchestration failed: {response.status_code}")
            logger.error(f"Error: {response.text}")
            return False


async def check_server_health():
    """Check if the server is running"""
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                logger.info("✅ Server is healthy")
                return True
            else:
                logger.error(f"❌ Server health check failed: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to server: {e}")
        return False


async def main():
    """Run all tests"""
    
    logger.info("=" * 60)
    logger.info("CEO Agent Orchestration Integration Test")
    logger.info("=" * 60)
    
    # Check server health first
    if not await check_server_health():
        logger.error("Server is not running. Please start the backend first.")
        return
    
    # Run tests
    test_results = []
    
    # Test 1: Direct orchestration
    logger.info("\n" + "=" * 40)
    logger.info("Test 1: Direct Orchestration")
    logger.info("=" * 40)
    test_results.append(("Direct Orchestration", await test_direct_orchestration()))
    
    # Test 2: CEO chat to orchestration flow
    logger.info("\n" + "=" * 40)
    logger.info("Test 2: CEO Chat to Orchestration Flow")
    logger.info("=" * 40)
    test_results.append(("CEO Chat to Orchestration", await test_ceo_chat_to_orchestration()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    if all_passed:
        logger.info("\n🎉 All tests passed!")
    else:
        logger.info("\n❌ Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
