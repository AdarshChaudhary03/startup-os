#!/usr/bin/env python3
"""
Test script for separate agent endpoints implementation.

This script tests:
1. Orchestration planning endpoint
2. Individual agent endpoints
3. Real-time progress workflow
4. Error handling
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List
import time

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


class SeparateEndpointsTestSuite:
    """Test suite for separate agent endpoints."""
    
    def __init__(self):
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details
        })
    
    async def test_orchestration_planning(self) -> Dict[str, Any]:
        """Test the orchestration planning endpoint."""
        print("\n🧪 Testing Orchestration Planning Endpoint...")
        
        test_task = "Write an Instagram caption for a sunny day in Delhi"
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/orchestrate/plan",
                headers=HEADERS,
                json={"task": test_task}
            ) as response:
                
                if response.status == 200:
                    plan_data = await response.json()
                    
                    # Validate plan structure
                    required_fields = ["request_id", "task", "mode", "rationale", "steps", "total_steps", "used_llm"]
                    missing_fields = [field for field in required_fields if field not in plan_data]
                    
                    if missing_fields:
                        self.log_test(
                            "Orchestration Planning - Structure", 
                            False, 
                            f"Missing fields: {missing_fields}"
                        )
                        return {}
                    
                    # Validate steps structure
                    steps = plan_data.get("steps", [])
                    if not steps:
                        self.log_test(
                            "Orchestration Planning - Steps", 
                            False, 
                            "No steps in orchestration plan"
                        )
                        return {}
                    
                    # Check if steps have required fields
                    step_fields = ["agent_id", "agent_name", "team_id", "team_name", "instruction", "endpoint"]
                    for i, step in enumerate(steps):
                        missing_step_fields = [field for field in step_fields if field not in step]
                        if missing_step_fields:
                            self.log_test(
                                f"Orchestration Planning - Step {i+1}", 
                                False, 
                                f"Missing step fields: {missing_step_fields}"
                            )
                            return {}
                    
                    self.log_test(
                        "Orchestration Planning - Success", 
                        True, 
                        f"Plan created with {len(steps)} steps in {plan_data['mode']} mode"
                    )
                    
                    return plan_data
                
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Orchestration Planning - HTTP Status", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    return {}
        
        except Exception as e:
            self.log_test(
                "Orchestration Planning - Exception", 
                False, 
                f"Exception: {str(e)}"
            )
            return {}
    
    async def test_individual_agent_execution(self, agent_endpoint: str, task: str, agent_name: str) -> Dict[str, Any]:
        """Test individual agent endpoint execution."""
        print(f"\n🤖 Testing {agent_name} Agent Endpoint...")
        
        try:
            start_time = time.time()
            
            async with self.session.post(
                f"{BASE_URL}{agent_endpoint}",
                headers=HEADERS,
                json={"task": task}
            ) as response:
                
                execution_time = time.time() - start_time
                
                if response.status == 200:
                    agent_data = await response.json()
                    
                    # Validate response structure
                    required_fields = [
                        "request_id", "agent_id", "agent_name", "team_id", 
                        "team_name", "task", "output", "success", "duration_ms", "timestamp"
                    ]
                    missing_fields = [field for field in required_fields if field not in agent_data]
                    
                    if missing_fields:
                        self.log_test(
                            f"{agent_name} - Structure", 
                            False, 
                            f"Missing fields: {missing_fields}"
                        )
                        return {}
                    
                    # Check if execution was successful
                    if agent_data.get("success", False):
                        output_preview = agent_data.get("output", "")[:100] + "..." if len(agent_data.get("output", "")) > 100 else agent_data.get("output", "")
                        self.log_test(
                            f"{agent_name} - Execution Success", 
                            True, 
                            f"Completed in {execution_time:.2f}s. Output: {output_preview}"
                        )
                    else:
                        error_msg = agent_data.get("error", "Unknown error")
                        self.log_test(
                            f"{agent_name} - Execution Success", 
                            False, 
                            f"Execution failed: {error_msg}"
                        )
                    
                    return agent_data
                
                else:
                    error_text = await response.text()
                    self.log_test(
                        f"{agent_name} - HTTP Status", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    return {}
        
        except Exception as e:
            self.log_test(
                f"{agent_name} - Exception", 
                False, 
                f"Exception: {str(e)}"
            )
            return {}
    
    async def test_real_time_workflow(self):
        """Test the complete real-time workflow."""
        print("\n🔄 Testing Real-Time Workflow...")
        
        # Step 1: Get orchestration plan
        plan_data = await self.test_orchestration_planning()
        if not plan_data:
            self.log_test("Real-Time Workflow", False, "Failed to get orchestration plan")
            return
        
        # Step 2: Execute each agent in the plan
        steps = plan_data.get("steps", [])
        execution_results = []
        
        for i, step in enumerate(steps):
            print(f"\n📋 Executing Step {i+1}/{len(steps)}: {step['agent_name']}")
            
            result = await self.test_individual_agent_execution(
                step["endpoint"],
                step["instruction"],
                step["agent_name"]
            )
            
            if result:
                execution_results.append(result)
            else:
                self.log_test(
                    "Real-Time Workflow - Step Execution", 
                    False, 
                    f"Failed to execute step {i+1}: {step['agent_name']}"
                )
                return
        
        # Step 3: Validate workflow completion
        if len(execution_results) == len(steps):
            total_duration = sum(result.get("duration_ms", 0) for result in execution_results)
            self.log_test(
                "Real-Time Workflow - Complete", 
                True, 
                f"All {len(steps)} agents executed successfully in {total_duration}ms total"
            )
        else:
            self.log_test(
                "Real-Time Workflow - Complete", 
                False, 
                f"Only {len(execution_results)}/{len(steps)} agents executed successfully"
            )
    
    async def test_agent_list_endpoint(self):
        """Test the agent list endpoint."""
        print("\n📋 Testing Agent List Endpoint...")
        
        try:
            async with self.session.get(f"{BASE_URL}/api/agents/list") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    
                    # Validate structure
                    if "agents" in agents_data and "total_agents" in agents_data:
                        agents_count = len(agents_data["agents"])
                        self.log_test(
                            "Agent List Endpoint", 
                            True, 
                            f"Retrieved {agents_count} agents successfully"
                        )
                        
                        # Validate agent structure
                        if agents_count > 0:
                            first_agent = agents_data["agents"][0]
                            required_fields = ["agent_id", "agent_name", "team_id", "team_name", "endpoint"]
                            missing_fields = [field for field in required_fields if field not in first_agent]
                            
                            if missing_fields:
                                self.log_test(
                                    "Agent List - Agent Structure", 
                                    False, 
                                    f"Missing fields in agent data: {missing_fields}"
                                )
                            else:
                                self.log_test(
                                    "Agent List - Agent Structure", 
                                    True, 
                                    "All required fields present in agent data"
                                )
                    else:
                        self.log_test(
                            "Agent List Endpoint", 
                            False, 
                            "Missing required fields in response"
                        )
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Agent List Endpoint", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
        
        except Exception as e:
            self.log_test(
                "Agent List Endpoint", 
                False, 
                f"Exception: {str(e)}"
            )
    
    async def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n⚠️  Testing Error Handling...")
        
        # Test empty task
        try:
            async with self.session.post(
                f"{BASE_URL}/api/orchestrate/plan",
                headers=HEADERS,
                json={"task": ""}
            ) as response:
                if response.status == 422:  # Validation error
                    self.log_test(
                        "Error Handling - Empty Task", 
                        True, 
                        "Correctly rejected empty task"
                    )
                else:
                    self.log_test(
                        "Error Handling - Empty Task", 
                        False, 
                        f"Unexpected status {response.status} for empty task"
                    )
        except Exception as e:
            self.log_test(
                "Error Handling - Empty Task", 
                False, 
                f"Exception: {str(e)}"
            )
        
        # Test invalid agent endpoint
        try:
            async with self.session.post(
                f"{BASE_URL}/api/agents/nonexistent-agent",
                headers=HEADERS,
                json={"task": "test task"}
            ) as response:
                if response.status == 404:  # Not found
                    self.log_test(
                        "Error Handling - Invalid Agent", 
                        True, 
                        "Correctly returned 404 for invalid agent endpoint"
                    )
                else:
                    self.log_test(
                        "Error Handling - Invalid Agent", 
                        False, 
                        f"Unexpected status {response.status} for invalid agent"
                    )
        except Exception as e:
            self.log_test(
                "Error Handling - Invalid Agent", 
                False, 
                f"Exception: {str(e)}"
            )
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("🧪 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        print("\n" + "="*60)


async def main():
    """Main test function."""
    print("🚀 Starting Separate Agent Endpoints Test Suite")
    print("="*60)
    
    async with SeparateEndpointsTestSuite() as test_suite:
        # Run all tests
        await test_suite.test_agent_list_endpoint()
        await test_suite.test_orchestration_planning()
        await test_suite.test_individual_agent_execution(
            "/api/agents/content-writer", 
            "Write a blog post about AI agents", 
            "Content Writer"
        )
        await test_suite.test_individual_agent_execution(
            "/api/agents/social-publisher", 
            "Schedule this post on Instagram", 
            "Social Media Publisher"
        )
        await test_suite.test_real_time_workflow()
        await test_suite.test_error_handling()
        
        # Print summary
        test_suite.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
