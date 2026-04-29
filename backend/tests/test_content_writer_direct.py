#!/usr/bin/env python3
"""Direct test of Content Writer Service to debug the dummy data issue."""

import asyncio
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_content_writer():
    """Test Content Writer Service directly."""
    try:
        print("=== Testing Content Writer Service ===")
        
        # Test imports
        print("1. Testing imports...")
        from contentWriter.content_writer_service import get_content_writer_service
        print("   OK Content Writer Service import successful")
        
        # Get service instance
        print("2. Getting service instance...")
        service = await get_content_writer_service()
        print("   OK Service instance created")
        
        # Test task execution
        print("3. Testing task execution...")
        task = "create a blog on GenAI in 100 words"
        request_id = "test-direct-123"
        
        print(f"   Task: {task}")
        print(f"   Request ID: {request_id}")
        
        result = await service.execute_content_task(task, request_id)
        
        print("4. Results:")
        print(f"   Content Length: {len(result)}")
        print(f"   Word Count: {len(result.split())}")
        print(f"   Content Preview: {result[:200]}...")
        
        # Check if it's dummy data
        dummy_indicators = [
            "Long-form article outline complete",
            "SEO-targeted intro",
            "citation placeholders",
            "Task completed successfully",
            "Content generation temporarily unavailable"
        ]
        
        is_dummy = any(indicator in result for indicator in dummy_indicators)
        print(f"   Is Dummy Data: {is_dummy}")
        
        if is_dummy:
            print("   X ISSUE: Still returning dummy data!")
        else:
            print("   OK SUCCESS: Real content generated!")
            
        return result
        
    except Exception as e:
        print(f"X ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_content_writer())
    if result:
        print("\n=== FULL RESULT ===")
        print(result)
    else:
        print("\n=== TEST FAILED ===")
