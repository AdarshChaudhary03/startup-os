#!/usr/bin/env python3
"""Test script to verify the orchestrate API is using real Content Writer Agent."""

import asyncio
import json
import time
from fastapi.testclient import TestClient
from server import app

def test_orchestrate_api():
    """Test the orchestrate API endpoint."""
    print("=== Testing Orchestrate API with Content Writer Agent ===")
    
    # Create test client
    client = TestClient(app)
    
    # Test data
    test_payload = {
        "task": "create a blog on GenAI in 100 words"
    }
    
    print(f"Sending request: {json.dumps(test_payload, indent=2)}")
    
    # Make request
    start_time = time.time()
    response = client.post("/api/orchestrate", json=test_payload)
    end_time = time.time()
    
    print(f"Response time: {end_time - start_time:.2f} seconds")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n=== Response Analysis ===")
        print(f"Request ID: {result.get('request_id')}")
        print(f"Task: {result.get('task')}")
        print(f"Mode: {result.get('mode')}")
        print(f"Chosen Agent: {result.get('chosen_agent_name')}")
        print(f"Duration: {result.get('duration_ms')}ms")
        print(f"Used LLM: {result.get('used_llm')}")
        
        # Check the output
        output = result.get('output', '')
        print(f"\nOutput Length: {len(output)}")
        print(f"Word Count: {len(output.split())}")
        print(f"Output Preview: {output[:200]}...")
        
        # Check if it's dummy data
        dummy_indicators = [
            "Long-form article outline complete",
            "SEO-targeted intro",
            "citation placeholders",
            "Task completed successfully"
        ]
        
        is_dummy = any(indicator in output for indicator in dummy_indicators)
        print(f"\nIs Dummy Data: {is_dummy}")
        
        if is_dummy:
            print("X ISSUE: Still returning dummy data!")
            print("\n=== Agent Runs Analysis ===")
            for run in result.get('agent_runs', []):
                print(f"Agent: {run.get('agent_name')}")
                print(f"Instruction: {run.get('instruction')}")
                print(f"Output: {run.get('output')}")
        else:
            print("OK SUCCESS: Real content generated!")
            
        print("\n=== Full Response ===")
        print(json.dumps(result, indent=2))
        
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_orchestrate_api()
