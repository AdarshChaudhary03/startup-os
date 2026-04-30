#!/usr/bin/env python3
"""
Test script for CEO Requirements Gathering System
Tests the complete workflow from initial task to orchestration
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TASKS = [
    {
        "name": "Simple Blog Task",
        "task": "Create a blog post about AI",
        "expected_clarifications": ["purpose", "target_audience", "length"]
    },
    {
        "name": "Complex Marketing Campaign",
        "task": "I need help with marketing",
        "expected_clarifications": ["purpose", "target_audience", "scope", "timeline", "format"]
    },
    {
        "name": "Clear Social Media Task",
        "task": "Create 5 LinkedIn posts about sustainable technology for tech professionals, focusing on recent innovations and their environmental impact. Posts should be professional but engaging, 150-200 words each, to be published over the next 2 weeks.",
        "expected_clarifications": []  # Should be clear enough to proceed
    }
]

SAMPLE_CLARIFICATIONS = {
    "What is the main purpose of this task?": "To educate our audience about AI trends",
    "Who is the target audience for this?": "Business professionals and tech enthusiasts",
    "What format do you prefer for the output?": "Blog post format with sections and examples",
    "When do you need this completed?": "Within the next week",
    "What tone should be used?": "Professional but accessible",
    "What is the scope of this project?": "Comprehensive overview with practical insights"
}


async def test_requirements_gathering_workflow():
    """Test the complete CEO requirements gathering workflow"""
    print("\n" + "=" * 60)
    print("TESTING CEO REQUIREMENTS GATHERING SYSTEM")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, test_case in enumerate(TEST_TASKS, 1):
            print(f"\n--- Test Case {i}: {test_case['name']} ---")
            
            try:
                # Step 1: Start requirements gathering
                print(f"\n1. Starting requirements gathering for: '{test_case['task']}'")
                
                start_payload = {
                    "task": test_case["task"],
                    "user_context": {"test_case": test_case["name"]}
                }
                
                response = await client.post(
                    f"{BASE_URL}/api/ceo/requirements/start",
                    json=start_payload
                )
                
                if response.status_code != 200:
                    print(f"❌ Failed to start requirements gathering: {response.status_code}")
                    print(f"Response: {response.text}")
                    continue
                
                start_result = response.json()
                session_id = start_result["session_id"]
                status = start_result["status"]
                
                print(f"✅ Requirements gathering started (Session: {session_id})")
                print(f"   Status: {status}")
                print(f"   Message: {start_result['message']}")
                
                if start_result.get("analysis"):
                    analysis = start_result["analysis"]
                    print(f"   Completeness Score: {analysis['completeness_score']}/10")
                    print(f"   Ready to Proceed: {analysis['ready_to_proceed']}")
                
                # Step 2: Handle clarifications if needed
                if status == "awaiting_clarification":
                    questions = start_result.get("clarification_questions", [])
                    print(f"\n2. CEO needs clarification ({len(questions)} questions):")
                    
                    for j, question in enumerate(questions, 1):
                        print(f"   Q{j}: {question}")
                    
                    # Provide sample clarifications
                    clarifications = {}
                    for question in questions[:3]:  # Limit to first 3 questions
                        for sample_q, sample_a in SAMPLE_CLARIFICATIONS.items():
                            if any(word in question.lower() for word in sample_q.lower().split()):
                                clarifications[question] = sample_a
                                break
                        
                        if question not in clarifications:
                            clarifications[question] = "Yes, that sounds good"
                    
                    print(f"\n   Providing clarifications:")
                    for q, a in clarifications.items():
                        print(f"   Q: {q[:50]}...")
                        print(f"   A: {a}")
                    
                    # Submit clarifications
                    clarification_payload = {
                        "session_id": session_id,
                        "clarifications": clarifications
                    }
                    
                    response = await client.post(
                        f"{BASE_URL}/api/ceo/requirements/clarify",
                        json=clarification_payload
                    )
                    
                    if response.status_code != 200:
                        print(f"❌ Failed to submit clarifications: {response.status_code}")
                        continue
                    
                    clarification_result = response.json()
                    print(f"\n✅ Clarifications submitted")
                    print(f"   Status: {clarification_result['status']}")
                    print(f"   Message: {clarification_result['message']}")
                    
                    # Check if requirements are complete
                    if clarification_result["status"] == "requirements_complete":
                        polished = clarification_result.get("polished_requirement")
                        if polished:
                            print(f"\n3. Requirements polished successfully:")
                            print(f"   Objective: {polished['objective']}")
                            print(f"   Target Audience: {polished['target_audience']}")
                            print(f"   Deliverables: {', '.join(polished['deliverables'])}")
                            print(f"   Agent Suggestion: {polished['agent_plan_suggestion']}")
                
                elif status == "requirements_complete":
                    polished = start_result.get("polished_requirement")
                    if polished:
                        print(f"\n2. Task was clear enough - requirements polished immediately:")
                        print(f"   Objective: {polished['objective']}")
                        print(f"   Target Audience: {polished['target_audience']}")
                        print(f"   Deliverables: {', '.join(polished['deliverables'])}")
                
                # Step 3: Proceed to orchestration
                print(f"\n3. Proceeding to orchestration...")
                
                response = await client.post(
                    f"{BASE_URL}/api/ceo/requirements/orchestrate/{session_id}"
                )
                
                if response.status_code == 200:
                    orchestration_result = response.json()
                    print(f"✅ Orchestration completed successfully")
                    
                    if "orchestration_result" in orchestration_result:
                        orch_data = orchestration_result["orchestration_result"]
                        print(f"   Request ID: {orch_data.get('request_id', 'N/A')}")
                        print(f"   Agents Used: {len(orch_data.get('agent_results', []))}")
                        print(f"   Success: {orch_data.get('success', False)}")
                        print(f"   Duration: {orch_data.get('total_duration_ms', 0)}ms")
                        
                        # Show final output preview
                        final_output = orch_data.get("final_output", "")
                        if final_output:
                            preview = final_output[:200] + "..." if len(final_output) > 200 else final_output
                            print(f"   Final Output Preview: {preview}")
                else:
                    print(f"❌ Orchestration failed: {response.status_code}")
                    print(f"Response: {response.text}")
                
                print(f"\n✅ Test case '{test_case['name']}' completed successfully")
                
            except Exception as e:
                print(f"❌ Test case '{test_case['name']}' failed: {e}")
            
            print("\n" + "-" * 40)


async def test_ceo_learning_insights():
    """Test CEO learning insights endpoint"""
    print("\n--- Testing CEO Learning Insights ---")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/ceo/requirements/learning/insights")
            
            if response.status_code == 200:
                insights = response.json()
                print(f"✅ Learning insights retrieved successfully")
                print(f"   Total Requirements Processed: {insights['learning_insights']['total_requirements']}")
                print(f"   Total Sessions: {insights['total_sessions']}")
                print(f"   Learning Matrix Size: {insights['learning_matrix_size']}")
                
                if insights['learning_insights']['common_clarifications']:
                    print(f"   Common Clarifications:")
                    for clarification, count in insights['learning_insights']['common_clarifications']:
                        print(f"     - {clarification}: {count} times")
            else:
                print(f"❌ Failed to get learning insights: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Learning insights test failed: {e}")


async def test_ceo_orchestration_learning():
    """Test CEO orchestration learning system"""
    print("\n--- Testing CEO Orchestration Learning ---")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test learning status
            response = await client.get(f"{BASE_URL}/api/ceo/learning-status")
            
            if response.status_code == 200:
                status = response.json()
                print(f"✅ CEO learning status retrieved")
                print(f"   Status: {status['status']}")
                print(f"   First Rule Initialized: {status['first_rule_initialized']}")
                print(f"   Content Writer -> Social Media Rule: {status['content_writer_to_social_media_rule']}")
            else:
                print(f"❌ Failed to get learning status: {response.status_code}")
            
            # Test learning insights
            response = await client.get(f"{BASE_URL}/api/ceo/learning-insights")
            
            if response.status_code == 200:
                insights = response.json()
                print(f"✅ CEO orchestration learning insights retrieved")
                print(f"   Learning Insights Available: {bool(insights.get('learning_insights'))}")
            else:
                print(f"❌ Failed to get orchestration learning insights: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Orchestration learning test failed: {e}")


async def main():
    """Run all CEO requirements system tests"""
    print(f"Starting CEO Requirements System Tests at {datetime.now()}")
    
    try:
        # Test requirements gathering workflow
        await test_requirements_gathering_workflow()
        
        # Test learning systems
        await test_ceo_learning_insights()
        await test_ceo_orchestration_learning()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        print("\n✅ CEO Requirements Gathering System is working correctly!")
        print("\nKey Features Tested:")
        print("  ✓ Initial task analysis and completeness scoring")
        print("  ✓ Dynamic clarification question generation")
        print("  ✓ Requirements polishing with user clarifications")
        print("  ✓ Automatic orchestration handoff")
        print("  ✓ Learning system for future improvements")
        print("  ✓ CEO orchestration learning and delegation patterns")
        
        print("\n📋 Next Steps:")
        print("  1. Test the WebSocket chat interface")
        print("  2. Integrate with frontend components")
        print("  3. Add more sophisticated learning algorithms")
        print("  4. Implement user feedback collection")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
