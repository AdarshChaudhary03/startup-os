#!/usr/bin/env python3
"""
Test script for separated orchestration workflow.
Tests the new planning-only orchestrate endpoint and individual agent execution.
"""

import asyncio
import aiohttp
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


async def test_orchestration_planning():
    """Test the new orchestrate endpoint that only does planning."""
    print("\n=== Testing Orchestration Planning ===")
    
    async with aiohttp.ClientSession() as session:
        # Test planning endpoint
        planning_data = {
            "task": "Write an Instagram caption for a sunny day in Delhi"
        }
        
        print(f"Calling /api/orchestrate with task: {planning_data['task']}")
        
        async with session.post(
            f"{BASE_URL}/api/orchestrate",
            json=planning_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                plan = await response.json()
                print(f"✅ Planning successful!")
                print(f"Request ID: {plan['request_id']}")
                print(f"Mode: {plan['mode']}")
                print(f"Rationale: {plan['rationale']}")
                print(f"Total Steps: {plan['total_steps']}")
                print(f"Used LLM: {plan['used_llm']}")
                
                print("\nExecution Plan:")
                for i, step in enumerate(plan['steps'], 1):
                    print(f"  {i}. {step['agent_name']} ({step['team_name']})")
                    print(f"     Endpoint: {step['endpoint']}")
                    print(f"     Instruction: {step['instruction']}")
                    print()
                
                return plan
            else:
                error = await response.text()
                print(f"❌ Planning failed: {response.status} - {error}")
                return None


async def test_individual_agent_execution(plan):
    """Test executing individual agents based on the plan."""
    if not plan or not plan.get('steps'):
        print("❌ No plan available for agent execution")
        return
    
    print("\n=== Testing Individual Agent Execution ===")
    
    async with aiohttp.ClientSession() as session:
        results = []
        
        for i, step in enumerate(plan['steps'], 1):
            print(f"\n--- Step {i}: Executing {step['agent_name']} ---")
            
            # Prepare agent execution request
            agent_data = {
                "task": step['instruction'],
                "context": json.dumps(results) if results else None,  # Pass previous results as context
                "metadata": {
                    "orchestration_request_id": plan['request_id'],
                    "step_number": i,
                    "total_steps": len(plan['steps'])
                }
            }
            
            print(f"Calling {step['endpoint']}...")
            
            async with session.post(
                f"{BASE_URL}{step['endpoint']}",
                json=agent_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ {step['agent_name']} completed successfully!")
                    print(f"Duration: {result['duration_ms']}ms")
                    print(f"Output Preview: {result['output'][:100]}...")
                    
                    results.append({
                        "agent_id": result['agent_id'],
                        "agent_name": result['agent_name'],
                        "output": result['output'],
                        "success": result['success'],
                        "duration_ms": result['duration_ms']
                    })
                else:
                    error = await response.text()
                    print(f"❌ {step['agent_name']} failed: {response.status} - {error}")
                    
                    results.append({
                        "agent_id": step['agent_id'],
                        "agent_name": step['agent_name'],
                        "output": f"Execution failed: {error}",
                        "success": False,
                        "duration_ms": 0
                    })
        
        return results


async def test_legacy_orchestration():
    """Test the legacy orchestration endpoint for comparison."""
    print("\n=== Testing Legacy Orchestration ===")
    
    async with aiohttp.ClientSession() as session:
        legacy_data = {
            "task": "Write an Instagram caption for a sunny day in Delhi"
        }
        
        print(f"Calling /api/orchestrate/legacy with task: {legacy_data['task']}")
        
        async with session.post(
            f"{BASE_URL}/api/orchestrate/legacy",
            json=legacy_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Legacy orchestration completed!")
                print(f"Request ID: {result['request_id']}")
                print(f"Mode: {result['mode']}")
                print(f"Duration: {result['duration_ms']}ms")
                print(f"Output: {result['output'][:100]}...")
                return result
            else:
                error = await response.text()
                print(f"❌ Legacy orchestration failed: {response.status} - {error}")
                return None


async def compare_workflows(separated_results, legacy_result):
    """Compare the results from separated vs legacy workflows."""
    print("\n=== Workflow Comparison ===")
    
    if separated_results and legacy_result:
        print("\n📊 Performance Comparison:")
        
        # Calculate total duration for separated workflow
        separated_total_duration = sum(r.get('duration_ms', 0) for r in separated_results)
        legacy_duration = legacy_result.get('duration_ms', 0)
        
        print(f"Separated Workflow Total Duration: {separated_total_duration}ms")
        print(f"Legacy Workflow Duration: {legacy_duration}ms")
        
        if separated_total_duration > 0 and legacy_duration > 0:
            if separated_total_duration < legacy_duration:
                print(f"✅ Separated workflow is {legacy_duration - separated_total_duration}ms faster")
            else:
                print(f"⚠️  Legacy workflow is {separated_total_duration - legacy_duration}ms faster")
        
        print("\n📈 Benefits of Separated Workflow:")
        print("✅ Real-time progress tracking")
        print("✅ Individual agent error handling")
        print("✅ Ability to retry specific agents")
        print("✅ Better scalability and parallelization")
        print("✅ More granular logging and monitoring")
        
        print("\n📋 Agent Execution Summary:")
        for result in separated_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['agent_name']}: {result['duration_ms']}ms")
    
    else:
        print("❌ Cannot compare - missing results from one or both workflows")


async def main():
    """Main test function."""
    print("🚀 Testing Separated Orchestration Workflow")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    
    try:
        # Test 1: Planning-only orchestration
        plan = await test_orchestration_planning()
        
        # Test 2: Individual agent execution
        separated_results = await test_individual_agent_execution(plan) if plan else None
        
        # Test 3: Legacy orchestration for comparison
        legacy_result = await test_legacy_orchestration()
        
        # Test 4: Compare workflows
        await compare_workflows(separated_results, legacy_result)
        
        print("\n🎉 Testing completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())