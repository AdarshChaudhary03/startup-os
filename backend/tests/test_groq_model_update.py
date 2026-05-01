"""Test script to verify Groq API works with the updated model"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.ai_service import ai_service
from src.agents.ceo.ceo_ai_task_analyzer import ceo_ai_task_analyzer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_groq_api_direct():
    """Test Groq API directly with the new model"""
    logger.info("Testing Groq API with updated model...")
    
    try:
        # Test with a simple prompt
        prompt = "Hello, this is a test. Please respond with a simple greeting."
        response = await ai_service.generate_content(
            prompt=prompt,
            provider_name="groq",
            model="llama-3.3-70b-versatile"
        )
        
        logger.info(f"Groq API Response: {response[:100]}...")
        return True, "Groq API test successful"
    except Exception as e:
        logger.error(f"Groq API test failed: {e}")
        return False, str(e)


async def test_ceo_task_analyzer():
    """Test CEO AI task analyzer with the updated model"""
    logger.info("Testing CEO AI task analyzer...")
    
    try:
        # Test with a sample task
        test_task = "Create an Instagram post about GenAI and post it"
        session_id = "test-session-123"
        
        result = await ceo_ai_task_analyzer.analyze_task(
            task=test_task,
            session_id=session_id
        )
        
        logger.info(f"Task analyzer result: {result}")
        
        if result.get("state") == "awaiting_answers":
            logger.info("Task analyzer successfully generated questions")
            logger.info(f"Completeness score: {result.get('completeness_score')}/10")
            logger.info(f"Number of questions: {len(result.get('questions', []))}")
            return True, "CEO task analyzer test successful"
        elif result.get("state") == "complete":
            logger.info("Task was already complete enough")
            return True, "CEO task analyzer test successful - task already complete"
        else:
            return False, f"Unexpected state: {result.get('state')}"
            
    except Exception as e:
        logger.error(f"CEO task analyzer test failed: {e}")
        return False, str(e)


async def main():
    """Run all tests"""
    logger.info("Starting Groq model update tests...")
    
    # Test 1: Direct Groq API
    success1, message1 = await test_groq_api_direct()
    print(f"\n{'✓' if success1 else '✗'} Groq API Test: {message1}")
    
    # Test 2: CEO Task Analyzer
    success2, message2 = await test_ceo_task_analyzer()
    print(f"{'✓' if success2 else '✗'} CEO Task Analyzer Test: {message2}")
    
    # Overall result
    all_success = success1 and success2
    print(f"\n{'='*50}")
    print(f"Overall Result: {'ALL TESTS PASSED ✓' if all_success else 'SOME TESTS FAILED ✗'}")
    print(f"{'='*50}")
    
    return all_success


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
