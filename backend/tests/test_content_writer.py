#!/usr/bin/env python3
"""
Test script to debug Content Writer Agent issues
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_content_writer_agent():
    """Test the Content Writer Agent directly to debug issues."""
    
    print("=== Content Writer Agent Debug Test ===")
    
    try:
        # Test 1: Import the service
        print("\n1. Testing import of Content Writer Service...")
        from contentWriter.content_writer_service import get_content_writer_service
        print("[SUCCESS] Successfully imported Content Writer Service")
        
        # Test 2: Get the service instance
        print("\n2. Getting Content Writer Service instance...")
        content_service = await get_content_writer_service()
        print("[SUCCESS] Successfully got Content Writer Service instance")
        
        # Test 3: Test health check
        print("\n3. Testing service health check...")
        is_healthy = await content_service.health_check()
        print(f"Health check result: {is_healthy}")
        
        if not is_healthy:
            print("[ERROR] Content Writer Service is not healthy")
            return
        
        # Test 4: Execute a simple content task
        print("\n4. Testing content generation...")
        test_task = "Write a short blog post about AI in startups"
        test_request_id = "debug-test-001"
        
        print(f"Task: {test_task}")
        print(f"Request ID: {test_request_id}")
        
        content = await content_service.execute_content_task(
            task=test_task,
            request_id=test_request_id
        )
        
        print("\n=== Generated Content ===")
        print(content)
        print("\n=== End Generated Content ===")
        
        # Check if it's dummy data
        if "Task completed successfully" in content or len(content) < 50:
            print("[ERROR] Received dummy data instead of real content")
        else:
            print("[SUCCESS] Received real LLM-generated content")
            
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("This suggests the Content Writer module is not properly set up")
    except Exception as e:
        print(f"[ERROR] Error during testing: {e}")
        logger.exception("Full error details:")

async def test_ai_provider_factory():
    """Test the AI Provider Factory directly."""
    
    print("\n=== AI Provider Factory Test ===")
    
    try:
        # Test 1: Import the factory
        print("\n1. Testing import of AI Provider Factory...")
        from ai_providers.factory import AIProviderFactory
        print("[SUCCESS] Successfully imported AI Provider Factory")
        
        # Test 2: Get Groq provider
        print("\n2. Testing Groq provider creation...")
        groq_provider = await AIProviderFactory.get_provider("groq")
        
        if groq_provider:
            print("[SUCCESS] Successfully created Groq provider")
            
            # Test 3: Test provider health
            print("\n3. Testing Groq provider health...")
            is_healthy = await groq_provider.health_check()
            print(f"Groq provider health: {is_healthy}")
            
            if is_healthy:
                # Test 4: Generate simple content
                print("\n4. Testing content generation with Groq...")
                from ai_providers.base import AIResponse
                
                response = await groq_provider.generate_content(
                    prompt="Write a one sentence summary about AI in startups.",
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    max_tokens=100
                )
                
                print(f"Generated content: {response.content}")
                print("[SUCCESS] AI Provider is working correctly")
            else:
                print("[ERROR] Groq provider is not healthy")
        else:
            print("[ERROR] Failed to create Groq provider")
            
    except Exception as e:
        print(f"[ERROR] Error during AI provider testing: {e}")
        logger.exception("Full error details:")

async def test_environment_config():
    """Test environment configuration."""
    
    print("\n=== Environment Configuration Test ===")
    
    try:
        from config import GROQ_API_KEY, DEFAULT_AI_PROVIDER
        
        print(f"Default AI Provider: {DEFAULT_AI_PROVIDER}")
        print(f"Groq API Key configured: {'Yes' if GROQ_API_KEY else 'No'}")
        
        if GROQ_API_KEY:
            print(f"Groq API Key (first 10 chars): {GROQ_API_KEY[:10]}...")
        else:
            print("[ERROR] Groq API Key is not configured")
            
    except Exception as e:
        print(f"[ERROR] Error checking environment config: {e}")

async def main():
    """Main test function."""
    
    # Test environment configuration
    await test_environment_config()
    
    # Test AI Provider Factory
    await test_ai_provider_factory()
    
    # Test Content Writer Agent
    await test_content_writer_agent()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
