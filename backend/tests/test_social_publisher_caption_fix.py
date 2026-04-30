#!/usr/bin/env python3
"""
Test script for Social Media Publisher caption extraction fix.

This test verifies that the social_publisher endpoint correctly:
1. Accepts the AgentExecutionRequest with complex context
2. Extracts caption from context object
3. Passes the correct caption to Instagram API
4. Handles various payload formats
"""

import asyncio
import json
import httpx
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
SOCIAL_PUBLISHER_ENDPOINT = f"{BASE_URL}/api/agents/social_publisher"

# Test cases
test_cases = [
    {
        "name": "Test 1: Caption in context object",
        "payload": {
            "task": "Schedule and publish the caption on Instagram.",
            "context": {
                "content_writer_output": "🤖💻 Ready to unlock the future of learning? \nDiscover GenAI, a game-changer for students 📚",
                "caption": "🤖💻 Ready to unlock the future of learning? \nDiscover GenAI, a game-changer for students 📚",
                "metadata": {
                    "content_generated_at": "2026-04-30T08:47:21.028015+00:00",
                    "session_id": "test-session-001"
                }
            },
            "metadata": {
                "step_number": 2,
                "total_steps": 2,
                "session_id": "test-session-001"
            }
        },
        "expected_caption_contains": "Ready to unlock the future of learning"
    },
    {
        "name": "Test 2: Caption as direct field",
        "payload": {
            "task": "Schedule and publish the caption on Instagram.",
            "caption": "🚀 Upskill with GenAI 🤖 Learn the latest in AI and machine learning 💻",
            "context": "{\"session_id\": \"test-session-002\"}",
            "metadata": {
                "session_id": "test-session-002"
            }
        },
        "expected_caption_contains": "Upskill with GenAI"
    },
    {
        "name": "Test 3: Content field as caption",
        "payload": {
            "task": "Publish to Instagram",
            "content": "✨ Transform your learning with AI! #GenAI #Education #Innovation",
            "metadata": {
                "session_id": "test-session-003"
            }
        },
        "expected_caption_contains": "Transform your learning with AI"
    },
    {
        "name": "Test 4: Complex nested context",
        "payload": {
            "task": "Post on Instagram",
            "context": json.dumps({
                "content_writer_output": "🎯 Master GenAI skills today! Join our workshop #AI #Learning",
                "caption": "🎯 Master GenAI skills today! Join our workshop #AI #Learning",
                "nested_data": {
                    "platform": "instagram",
                    "schedule": "immediate"
                }
            }),
            "metadata": {
                "session_id": "test-session-004"
            }
        },
        "expected_caption_contains": "Master GenAI skills"
    }
]


async def test_social_publisher_endpoint():
    """Test the social publisher endpoint with various payload formats."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        results = []
        
        for test_case in test_cases:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running: {test_case['name']}")
            logger.info(f"{'='*60}")
            
            try:
                # Add session ID header
                headers = {
                    "Content-Type": "application/json",
                    "X-Session-ID": test_case["payload"].get("metadata", {}).get("session_id", "test-default")
                }
                
                # Log request details
                logger.info(f"Request URL: {SOCIAL_PUBLISHER_ENDPOINT}")
                logger.info(f"Request Headers: {headers}")
                logger.info(f"Request Payload: {json.dumps(test_case['payload'], indent=2)}")
                
                # Make request
                response = await client.post(
                    SOCIAL_PUBLISHER_ENDPOINT,
                    json=test_case["payload"],
                    headers=headers
                )
                
                # Log response
                logger.info(f"Response Status: {response.status_code}")
                logger.info(f"Response Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"Response Data: {json.dumps(response_data, indent=2)}")
                    
                    # Check if the expected caption was used
                    output = response_data.get("output", "")
                    success = test_case["expected_caption_contains"] in str(response_data)
                    
                    result = {
                        "test": test_case["name"],
                        "status": "PASSED" if success else "FAILED",
                        "response_status": response.status_code,
                        "output": output,
                        "caption_found": success
                    }
                    
                    if success:
                        logger.info(f"✅ TEST PASSED: Caption correctly extracted and used")
                    else:
                        logger.error(f"❌ TEST FAILED: Expected caption not found in response")
                        logger.error(f"Expected to find: '{test_case['expected_caption_contains']}'")
                    
                else:
                    # Handle error response
                    error_text = response.text
                    logger.error(f"Response Error: {error_text}")
                    
                    result = {
                        "test": test_case["name"],
                        "status": "FAILED",
                        "response_status": response.status_code,
                        "error": error_text
                    }
                    
                    # Check if it's the 422 error we're trying to fix
                    if response.status_code == 422:
                        logger.error("❌ Got 422 Unprocessable Content error - caption extraction may have failed")
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Exception during test: {str(e)}", exc_info=True)
                results.append({
                    "test": test_case["name"],
                    "status": "ERROR",
                    "error": str(e)
                })
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] in ["FAILED", "ERROR"])
        
        logger.info(f"Total Tests: {len(results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        
        for result in results:
            status_emoji = "✅" if result["status"] == "PASSED" else "❌"
            logger.info(f"{status_emoji} {result['test']}: {result['status']}")
            if result.get("error"):
                logger.info(f"   Error: {result['error']}")
        
        return results


if __name__ == "__main__":
    logger.info("Starting Social Media Publisher Caption Fix Tests")
    logger.info(f"Testing endpoint: {SOCIAL_PUBLISHER_ENDPOINT}")
    logger.info(f"Test started at: {datetime.now().isoformat()}")
    
    # Run tests
    results = asyncio.run(test_social_publisher_endpoint())
    
    # Exit with appropriate code
    if all(r["status"] == "PASSED" for r in results):
        logger.info("\n✅ All tests passed!")
        exit(0)
    else:
        logger.error("\n❌ Some tests failed!")
        exit(1)