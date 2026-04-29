#!/usr/bin/env python3
"""
Test script to verify the orchestrate API is working with Content Writer Agent
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_orchestrate_api():
    """Test the orchestrate API directly."""
    
    print("=== Orchestrate API Test ===")
    
    try:
        # Import required modules
        from utils import execute_task_dummy, route_task_to_agent
        from data import TEAMS
        
        # Test 1: Route a content writing task
        print("\n1. Testing task routing...")
        task = "Write a blog post about AI in startups"
        agent, team_id = route_task_to_agent(task)
        
        print(f"Task: {task}")
        print(f"Routed to agent: {agent['name']} (ID: {agent['id']})")
        print(f"Team: {team_id}")
        
        # Test 2: Execute the task
        print("\n2. Testing task execution...")
        request_id = "api-test-001"
        
        output = await execute_task_dummy(agent, task, request_id)
        
        print("\n=== Generated Output ===")
        print(output[:500] + "..." if len(output) > 500 else output)
        print("\n=== End Generated Output ===")
        
        # Check if it's real content or dummy data
        if "Task completed successfully" in output or len(output) < 100:
            print("[ERROR] Still receiving dummy data instead of real content")
            return False
        else:
            print("[SUCCESS] Received real LLM-generated content from orchestrate API")
            return True
            
    except Exception as e:
        print(f"[ERROR] Error during orchestrate API testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    
    success = await test_orchestrate_api()
    
    if success:
        print("\n[SUCCESS] Orchestrate API is working correctly with Content Writer Agent!")
    else:
        print("\n[ERROR] Orchestrate API is still returning dummy data")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
