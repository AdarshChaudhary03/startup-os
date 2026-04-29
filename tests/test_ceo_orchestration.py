#!/usr/bin/env python3
"""
Test script for CEO orchestration workflow.
Tests the CEO-mediated agent execution where agents return responses to CEO for analysis and delegation.
"""

import asyncio
import httpx
import json
from datetime import datetime

# Base URL for the backend server
BASE_URL = "http://localhost:8000"


async def test_ceo_orchestration():
    """Test CEO orchestration workflow."""
    print("🤖 Testing CEO Orchestration Workflow")
    print("=" * 50)
    
    # Test data
    test_cases = [
        {
            "name": "Blog Creation and Social Media Posting",
            "task": "create a blog on GenAI in 100 words and post to Instagram",
            "expected_agents": ["content_writer", "social_publisher"]
        },
        {
            "name": "Instagram Caption Creation",
            "task": "Write an instagram caption for a sunny Day in Delhi",
            "expected_agents": ["content_writer", "social_publisher"]
        },
        {
            "name": "Marketing Content Workflow",
            "task": "Create marketing content for a new AI product and distribute on social media",
            "expected_agents": ["content_writer", "social_publisher"]
        }
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {test_case['name']}")
            print(f"Task: {test_case['task']}")
            print("-" * 40)
            
            try:
                # Test CEO orchestration
                await test_ceo_workflow(client, test_case)
                print(f"✅ Test Case {i} PASSED")
                
            except Exception as e:
                print(f"❌ Test Case {i} FAILED: {str(e)}")
                continue
    
    print("\n🎯 CEO Orchestration Testing Complete")


async def test_ceo_workflow(client: httpx.AsyncClient, test_case: dict):
    """Test CEO orchestration workflow for a specific test case."""
    
    # Step 1: Test CEO Orchestration
    print("\n🎯 Step 1: CEO Orchestration Workflow")
    
    ceo_payload = {
        "task": test_case["task"]
    }
    
    print(f"Calling: POST {BASE_URL}/api/ceo/orchestrate")
    print(f"Payload: {json.dumps(ceo_payload, indent=2)}")
    
    response = await client.post(
        f"{BASE_URL}/api/ceo/orchestrate",
        json=ceo_payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ CEO Orchestration failed: {response.text}")
        raise Exception(f"CEO orchestration failed with status {response.status_code}")
    
    ceo_result = response.json()
    print(f"✅ CEO Orchestration successful")
    print(f"Request ID: {ceo_result.get('request_id')}")
    print(f"Mode: {ceo_result.get('mode')}")
    print(f"Rationale: {ceo_result.get('rationale')}")
    print(f"Total Duration: {ceo_result.get('total_duration_ms')}ms")
    print(f"Success: {ceo_result.get('success')}")
    
    # Validate agent results
    agent_results = ceo_result.get('agent_results', [])
    print(f"\n📊 Agent Execution Results: {len(agent_results)} agents")
    
    for i, agent_result in enumerate(agent_results, 1):
        print(f"\n  Agent {i}: {agent_result.get('agent_name')}")
        print(f"    Team: {agent_result.get('team_name')}")
        print(f"    Success: {agent_result.get('success')}")
        print(f"    Duration: {agent_result.get('duration_ms')}ms")
        print(f"    Output Preview: {agent_result.get('output', '')[:100]}...")
        
        if not agent_result.get('success'):
            print(f"    ❌ Error: {agent_result.get('error')}")
    
    # Validate final output
    final_output = ceo_result.get('final_output', '')
    print(f"\n📝 CEO Final Analysis:")
    print(f"Length: {len(final_output)} characters")
    print(f"Preview: {final_output[:200]}...")
    
    # Validate workflow success
    if not ceo_result.get('success'):
        raise Exception("CEO orchestration workflow failed")
    
    if len(agent_results) == 0:
        raise Exception("No agents were executed")
    
    successful_agents = sum(1 for r in agent_results if r.get('success'))
    if successful_agents == 0:
        raise Exception("All agents failed to execute")
    
    print(f"\n✅ Workflow Validation: {successful_agents}/{len(agent_results)} agents successful")


async def test_ceo_analysis():
    """Test CEO analysis endpoint."""
    print("\n🧠 Testing CEO Analysis Endpoint")
    print("-" * 40)
    
    analysis_payload = {
        "agent_output": "# GenAI Blog Post\n\nGenerative AI is revolutionizing technology...",
        "agent_name": "Content Writer",
        "original_task": "create a blog on GenAI",
        "next_agent": "Social Media Publisher"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"Calling: POST {BASE_URL}/api/ceo/analyze")
        print(f"Payload: {json.dumps(analysis_payload, indent=2)}")
        
        response = await client.post(
            f"{BASE_URL}/api/ceo/analyze",
            json=analysis_payload
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ CEO Analysis failed: {response.text}")
            return False
        
        analysis_result = response.json()
        print(f"✅ CEO Analysis successful")
        print(f"Request ID: {analysis_result.get('request_id')}")
        print(f"Agent: {analysis_result.get('agent_name')}")
        print(f"Analysis Preview: {analysis_result.get('analysis', '')[:200]}...")
        
        return True


async def test_individual_agents():
    """Test individual agent endpoints."""
    print("\n🔧 Testing Individual Agent Endpoints")
    print("-" * 40)
    
    agent_tests = [
        {
            "name": "Content Writer",
            "endpoint": "/api/agents/content-writer",
            "payload": {"task": "create a blog on GenAI in 100 words"}
        },
        {
            "name": "Social Media Publisher",
            "endpoint": "/api/agents/social-media-publisher",
            "payload": {
                "task": "post to instagram",
                "content": "Sample content for posting"
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for agent_test in agent_tests:
            print(f"\n🤖 Testing {agent_test['name']}")
            
            try:
                response = await client.post(
                    f"{BASE_URL}{agent_test['endpoint']}",
                    json=agent_test['payload']
                )
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {agent_test['name']} successful")
                    print(f"Success: {result.get('success')}")
                    print(f"Duration: {result.get('duration_ms')}ms")
                    print(f"Output Preview: {result.get('output', '')[:100]}...")
                else:
                    print(f"❌ {agent_test['name']} failed: {response.text}")
                    
            except Exception as e:
                print(f"❌ {agent_test['name']} error: {str(e)}")


async def main():
    """Main test function."""
    print("🚀 Starting CEO Orchestration Tests")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BASE_URL}")
    print("=" * 60)
    
    try:
        # Test individual agents first
        await test_individual_agents()
        
        # Test CEO analysis
        await test_ceo_analysis()
        
        # Test full CEO orchestration workflow
        await test_ceo_orchestration()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Test suite failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())