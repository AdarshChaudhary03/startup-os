"""Test script to analyze Groq model response format"""

import asyncio
import json
import logging
from src.services.ai_service import ai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_groq_response():
    """Test Groq API response to understand the format"""
    
    # Simple test prompt that should return JSON
    test_prompt = """
Return a simple JSON object with the following structure:
{
    "status": "success",
    "message": "Test response",
    "number": 42
}

IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting.
"""
    
    try:
        logger.info("Testing Groq API response format...")
        
        # Call Groq API
        response = await ai_service.generate_content(
            prompt=test_prompt,
            provider_name="groq",
            model="llama-3.3-70b-versatile"
        )
        
        logger.info(f"Raw response type: {type(response)}")
        logger.info(f"Raw response length: {len(response) if response else 0}")
        logger.info(f"Raw response (first 200 chars): {response[:200] if response else 'None'}")
        logger.info(f"Raw response (last 200 chars): {response[-200:] if response else 'None'}")
        
        # Check for common issues
        if response:
            # Check for markdown code blocks
            if response.startswith('```'):
                logger.warning("Response starts with markdown code block")
                # Extract JSON from markdown
                lines = response.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('```json'):
                        in_json = True
                        continue
                    elif line.strip() == '```':
                        in_json = False
                        continue
                    elif in_json:
                        json_lines.append(line)
                response = '\n'.join(json_lines)
                logger.info(f"Extracted from markdown: {response}")
            
            # Check for leading/trailing whitespace
            if response != response.strip():
                logger.warning("Response has leading/trailing whitespace")
                response = response.strip()
            
            # Check for BOM or other invisible characters
            if response.startswith('\ufeff'):
                logger.warning("Response has BOM character")
                response = response.lstrip('\ufeff')
            
            # Try to parse JSON
            try:
                parsed = json.loads(response)
                logger.info(f"Successfully parsed JSON: {parsed}")
                return True
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                logger.error(f"Failed response: {repr(response)}")
                
                # Try to identify the issue
                if len(response) == 0:
                    logger.error("Response is empty")
                elif response[0] not in ['{', '[']:
                    logger.error(f"Response doesn't start with JSON delimiter, starts with: {repr(response[0])}")
                
        else:
            logger.error("Response is None or empty")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == "__main__":
    asyncio.run(test_groq_response())
