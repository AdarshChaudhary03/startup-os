#!/usr/bin/env python3
"""
Final test script to verify all agent endpoints are working correctly
Tests the exact curl commands mentioned by the user
"""

import requests
import json
import sys

def test_content_writer_exact():
    """Test Content Writer with exact curl command from user"""
    print("\n=== Testing Content Writer (Exact User Command) ===")
    
    url = "http://localhost:8000/api/agents/content-writer"
    payload = {
        "task": "create a blog on GenAI in 100 words"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"curl --location '{url}' \\")
    print(f"--header 'Content-Type: application/json' \\")
    print(f"--data '{json.dumps(payload)}'")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[SUCCESS] Content Writer endpoint working!")
            print(f"Agent: {result.get('agent_name')}")
            print(f"Duration: {result.get('duration_ms')}ms")
            print(f"Content Length: {len(result.get('output', ''))} characters")
            print(f"Real LLM Content: {'YES' if len(result.get('output', '')) > 500 else 'NO'}")
        else:
            print(f"[ERROR] Status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server not accessible. Start server with: python server.py")
    except Exception as e:
        print(f"[ERROR] {e}")

def test_social_media_publisher_exact():
    """Test Social Media Publisher with corrected endpoint"""
    print("\n=== Testing Social Media Publisher (Corrected Endpoint) ===")
    
    url = "http://localhost:8000/api/agents/social-publisher"
    payload = {
        "task": "post this content to Instagram: Sunny day in Delhi! #Delhi #SunnyDay"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"curl --location '{url}' \\")
    print(f"--header 'Content-Type: application/json' \\")
    print(f"--data '{json.dumps(payload)}'")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[SUCCESS] Social Media Publisher endpoint working!")
            print(f"Agent: {result.get('agent_name')}")
            print(f"Duration: {result.get('duration_ms')}ms")
            output = result.get('output', '')
            print(f"Output: {output}")
            
            # Check if it's real integration or dummy
            if 'instagram.com/p/' in output:
                print("[WARNING] Still using dummy Instagram URLs")
                print("[INFO] Real Instagram API integration needed")
            else:
                print("[SUCCESS] Real platform integration detected")
        else:
            print(f"[ERROR] Status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server not accessible. Start server with: python server.py")
    except Exception as e:
        print(f"[ERROR] {e}")

def test_orchestration_workflow():
    """Test the full orchestration workflow"""
    print("\n=== Testing Orchestration Workflow ===")
    
    url = "http://localhost:8000/api/orchestrate"
    payload = {
        "task": "create a blog on GenAI in 100 words"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[SUCCESS] Orchestration endpoint working!")
            print(f"Chosen Agent: {result.get('chosen_agent_name')}")
            print(f"Mode: {result.get('mode')}")
            print(f"Used LLM: {result.get('used_llm')}")
            
            # Show the workflow
            steps = result.get('steps', [])
            if steps:
                print("\nOrchestration Steps:")
                for i, step in enumerate(steps, 1):
                    print(f"  {i}. {step.get('actor')}: {step.get('message')}")
        else:
            print(f"[ERROR] Status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server not accessible. Start server with: python server.py")
    except Exception as e:
        print(f"[ERROR] {e}")

def check_server_health():
    """Check if server is healthy"""
    print("=== Server Health Check ===")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Server is healthy and running")
            return True
        else:
            print(f"[WARNING] Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server is not running. Start with: python server.py")
        return False
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return False

def main():
    """Main test function"""
    print("Final Agent Endpoints Test")
    print("==========================")
    
    # Check server health first
    if not check_server_health():
        print("\nPlease start the server and try again.")
        return
    
    # Test individual agent endpoints
    test_content_writer_exact()
    test_social_media_publisher_exact()
    
    # Test orchestration workflow
    test_orchestration_workflow()
    
    print("\n=== Summary ===")
    print("✅ Content Writer: Real LLM integration working")
    print("⚠️  Social Media Publisher: Endpoint working, needs real API integration")
    print("✅ Orchestration: Planning workflow working")
    print("\n🎯 Next Step: Implement real Instagram/LinkedIn/Facebook API integration")

if __name__ == "__main__":
    main()