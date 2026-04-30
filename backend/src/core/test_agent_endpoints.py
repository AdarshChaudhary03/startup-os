#!/usr/bin/env python3
"""
Test script for individual agent endpoints
Tests Content Writer and Social Media Publisher endpoints
"""

import requests
import json
import sys

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_content_writer():
    """Test Content Writer agent endpoint"""
    print("\n=== Testing Content Writer Agent ===")
    
    url = f"{BASE_URL}/api/agents/content-writer"
    payload = {
        "task": "create a blog on GenAI in 100 words"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Making request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nSuccess! Response:")
            print(json.dumps(result, indent=2))
            
            # Check if it's real content or dummy data
            output = result.get('output', '')
            if 'Long-form article outline complete' in output:
                print("\n[WARNING] Still returning dummy data!")
            else:
                print("\n[SUCCESS] Real LLM-generated content detected!")
        else:
            print(f"\nError Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server. Is the server running on port 8000?")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def test_social_media_publisher():
    """Test Social Media Publisher agent endpoint"""
    print("\n=== Testing Social Media Publisher Agent ===")
    
    url = f"{BASE_URL}/api/agents/social-publisher"
    payload = {
        "task": "post this content to Instagram: Sunny day in Delhi! Perfect weather for exploring the city. #Delhi #SunnyDay #Travel"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Making request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nSuccess! Response:")
            print(json.dumps(result, indent=2))
            
            # Check if it's real content or dummy data
            output = result.get('output', '')
            if any(dummy in output for dummy in ['Successfully published to Instagram', 'LinkedIn post published', 'Facebook event created']):
                print("\n[WARNING] Still returning dummy data!")
            else:
                print("\n[SUCCESS] Real platform integration detected!")
        else:
            print(f"\nError Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to server. Is the server running on port 8000?")
    except Exception as e:
        print(f"\n[ERROR] {e}")

def test_orchestrate_endpoint():
    """Test orchestrate endpoint for comparison"""
    print("\n=== Testing Orchestrate Endpoint ===")
    
    url = f"{BASE_URL}/api/orchestrate"
    payload = {
        "task": "create a blog on GenAI in 100 words"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Making request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nOrchestrate Response:")
            print(f"Chosen Agent: {result.get('chosen_agent_name')}")
            print(f"Output: {result.get('output')}")
            print(f"Used LLM: {result.get('used_llm')}")
        else:
            print(f"\nError Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to server. Is the server running on port 8000?")
    except Exception as e:
        print(f"\n[ERROR] {e}")

def main():
    """Main test function"""
    print("Testing Individual Agent Endpoints")
    print("=====================================")
    
    # Test individual agent endpoints
    test_content_writer()
    test_social_media_publisher()
    
    # Test orchestrate endpoint for comparison
    test_orchestrate_endpoint()
    
    print("\nTesting Complete!")

if __name__ == "__main__":
    main()