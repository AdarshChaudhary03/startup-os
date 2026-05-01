"""Test script to verify CEO chat fixes

This test verifies:
1. Async/await issues are fixed
2. Groq API integration works correctly
3. CEO chat initialization is successful
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.ceo.ceo_chat_interface import ceo_chat_interface
from src.agents.ceo.ceo_conversation_flow import ceo_conversation_flow
from src.agents.ceo.ceo_ai_task_analyzer import ceo_ai_task_analyzer
from src.services.ai_service import ai_service
from src.core.ai_startup import initialize_ai_providers


class TestCEOChatFix:
    """Test suite for CEO chat fixes"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        if passed:
            self.passed += 1
            print(f"[PASS] {test_name}: PASSED")
        else:
            self.failed += 1
            print(f"[FAIL] {test_name}: FAILED - {details}")
    
    async def test_ai_provider_initialization(self):
        """Test AI provider initialization"""
        try:
            # Initialize AI providers
            await initialize_ai_providers()
            
            # Check if Groq provider is available
            providers = ai_service.list_providers()
            if "groq" not in providers:
                self.log_result(
                    "AI Provider Initialization",
                    False,
                    "Groq provider not found in available providers"
                )
                return
            
            # Test health check
            health_status = await ai_service.health_check("groq")
            if not health_status.get("groq", False):
                self.log_result(
                    "AI Provider Initialization",
                    False,
                    "Groq provider health check failed"
                )
                return
            
            self.log_result("AI Provider Initialization", True)
            
        except Exception as e:
            self.log_result(
                "AI Provider Initialization",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_groq_api_call(self):
        """Test Groq API call without invalid parameters"""
        try:
            # Simple test prompt
            test_prompt = "What is 2+2? Reply with just the number."
            
            # Call Groq API
            response = await ai_service.generate_content(
                prompt=test_prompt,
                provider_name="groq",
                model="mixtral-8x7b-32768"
            )
            
            if response:
                self.log_result("Groq API Call", True, f"Response: {response[:50]}...")
            else:
                self.log_result("Groq API Call", False, "Empty response from Groq")
                
        except Exception as e:
            self.log_result(
                "Groq API Call",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_ceo_chat_start(self):
        """Test CEO chat session start"""
        try:
            # Start a chat session
            task = "Create a simple web application for task management"
            result = await ceo_chat_interface.start_chat_session(task)
            
            # Check result structure
            if not isinstance(result, dict):
                self.log_result(
                    "CEO Chat Start",
                    False,
                    "Result is not a dictionary"
                )
                return
            
            # Check required fields
            required_fields = ["session_id", "greeting", "state"]
            missing_fields = [f for f in required_fields if f not in result]
            
            if missing_fields:
                self.log_result(
                    "CEO Chat Start",
                    False,
                    f"Missing fields: {missing_fields}"
                )
                return
            
            # Check if session was created
            session_id = result["session_id"]
            if session_id not in ceo_chat_interface.active_sessions:
                self.log_result(
                    "CEO Chat Start",
                    False,
                    "Session not found in active sessions"
                )
                return
            
            self.log_result(
                "CEO Chat Start",
                True,
                f"Session ID: {session_id}, State: {result['state']}"
            )
            
        except Exception as e:
            self.log_result(
                "CEO Chat Start",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_process_user_message(self):
        """Test process_user_message with proper async/await"""
        try:
            # Create a test session
            task = "Build a REST API for user authentication"
            start_result = await ceo_chat_interface.start_chat_session(task)
            session_id = start_result["session_id"]
            
            # Get session data
            session_data = ceo_chat_interface.active_sessions[session_id]
            
            # Process a message through conversation flow
            message = "The API should support JWT tokens and OAuth2"
            result = await ceo_conversation_flow.process_user_message(
                session_id=session_id,
                message=message,
                session_data=session_data
            )
            
            # Check result
            if not isinstance(result, dict):
                self.log_result(
                    "Process User Message",
                    False,
                    "Result is not a dictionary"
                )
                return
            
            # Check for required fields
            if "state" not in result or "response" not in result:
                self.log_result(
                    "Process User Message",
                    False,
                    "Missing state or response in result"
                )
                return
            
            self.log_result(
                "Process User Message",
                True,
                f"State: {result['state']}"
            )
            
        except Exception as e:
            self.log_result(
                "Process User Message",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_ai_task_analyzer(self):
        """Test AI task analyzer without invalid parameters"""
        try:
            # Test task
            task = "Create a mobile app for fitness tracking"
            session_id = "test-session-123"
            
            # Analyze task
            result = await ceo_ai_task_analyzer.analyze_task(
                task=task,
                session_id=session_id
            )
            
            # Check result
            if not isinstance(result, dict):
                self.log_result(
                    "AI Task Analyzer",
                    False,
                    "Result is not a dictionary"
                )
                return
            
            # Check for required fields
            if "state" not in result:
                self.log_result(
                    "AI Task Analyzer",
                    False,
                    "Missing state in result"
                )
                return
            
            # Check if it's awaiting answers or complete
            valid_states = ["awaiting_answers", "complete", "error"]
            if result["state"] not in valid_states:
                self.log_result(
                    "AI Task Analyzer",
                    False,
                    f"Invalid state: {result['state']}"
                )
                return
            
            self.log_result(
                "AI Task Analyzer",
                True,
                f"State: {result['state']}, Score: {result.get('completeness_score', 'N/A')}"
            )
            
        except Exception as e:
            self.log_result(
                "AI Task Analyzer",
                False,
                f"Exception: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Run all tests"""
        print("\n[TEST] Running CEO Chat Fix Tests...\n")
        
        # Run tests in order
        await self.test_ai_provider_initialization()
        await self.test_groq_api_call()
        await self.test_ceo_chat_start()
        await self.test_process_user_message()
        await self.test_ai_task_analyzer()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"[SUMMARY] Test Summary:")
        print(f"   [PASS] Passed: {self.passed}")
        print(f"   [FAIL] Failed: {self.failed}")
        print(f"   [TOTAL] Total: {self.passed + self.failed}")
        print("=" * 50 + "\n")
        
        # Save detailed results
        results_file = Path(__file__).parent / "ceo_chat_test_results.json"
        with open(results_file, "w") as f:
            json.dump({
                "summary": {
                    "passed": self.passed,
                    "failed": self.failed,
                    "total": self.passed + self.failed
                },
                "tests": self.test_results
            }, f, indent=2)
        
        print(f"[RESULTS] Detailed results saved to: {results_file}")
        
        # Return success if all tests passed
        return self.failed == 0


async def main():
    """Main test runner"""
    tester = TestCEOChatFix()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Run tests
    asyncio.run(main())
