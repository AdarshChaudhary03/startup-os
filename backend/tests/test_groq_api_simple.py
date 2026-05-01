"""Simple test to debug Groq API 400 error"""

import asyncio
import httpx
import json
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Get API key from environment
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')


async def test_groq_direct():
    """Test Groq API directly to debug 400 error"""
    
    print(f"\nTesting Groq API with key: {GROQ_API_KEY[:10]}...{GROQ_API_KEY[-5:]}")
    
    # Test payload
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "user", "content": "What is 2+2? Reply with just the number."}
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": False
    }
    
    print(f"\nPayload: {json.dumps(payload, indent=2)}")
    
    # Make request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0
            )
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nSuccess! Response: {data['choices'][0]['message']['content']}")
            else:
                print(f"\nError Response: {response.text}")
                
        except Exception as e:
            print(f"\nException: {type(e).__name__}: {e}")


async def test_groq_models():
    """Test different Groq models"""
    
    models = [
        "mixtral-8x7b-32768",
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it"
    ]
    
    print("\n\nTesting different models:")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        for model in models:
            print(f"\nTesting model: {model}")
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ],
                "temperature": 0.7,
                "max_tokens": 10
            }
            
            try:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    print(f"  ✓ Success")
                else:
                    print(f"  ✗ Failed: {response.status_code} - {response.text[:100]}")
                    
            except Exception as e:
                print(f"  ✗ Exception: {e}")


if __name__ == "__main__":
    print("Groq API Debug Test")
    print("=" * 50)
    
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not found in environment")
        sys.exit(1)
    
    asyncio.run(test_groq_direct())
    asyncio.run(test_groq_models())
