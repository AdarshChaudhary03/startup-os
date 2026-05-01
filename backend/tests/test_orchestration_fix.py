import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the backend src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from agents.ceo.ceo_conversation_flow import ceo_conversation_flow, ConversationState
from agents.ceo.ceo_simplified_flow import simplified_ceo_agent


class TestOrchestrationFix:
    """Test cases to verify the orchestration API fix for null task parameter"""
    
    @pytest.mark.asyncio
    async def test_get_orchestration_plan_with_valid_task(self):
        """Test that get_orchestration_plan works with valid task parameter"""
        # Mock the httpx client
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "mode": "sequential",
                "steps": [
                    {
                        "agent_id": "content_writer",
                        "agent_name": "Content Writer",
                        "instruction": "Write content",
                        "endpoint": "/api/agents/content_writer"
                    }
                ]
            }
            
            # Configure async context manager
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test with valid polished requirements
            polished_requirements = "Create an Instagram post about GenAI with engaging content and relevant hashtags"
            session_id = "test-session-123"
            
            result = await simplified_ceo_agent.get_orchestration_plan(
                polished_requirements=polished_requirements,
                session_id=session_id
            )
            
            # Verify the API was called with correct parameters
            mock_client_instance.post.assert_called_once_with(
                "http://localhost:8000/api/orchestrate",
                json={"task": polished_requirements},
                headers={"X-Request-ID": session_id}
            )
            
            # Verify the result
            assert result["mode"] == "sequential"
            assert len(result["steps"]) == 1
            assert result["steps"][0]["agent_id"] == "content_writer"
    
    @pytest.mark.asyncio
    async def test_get_orchestration_plan_with_null_task(self):
        """Test that get_orchestration_plan raises error with null task parameter"""
        # Test with None
        with pytest.raises(ValueError, match="Polished requirements cannot be None or empty"):
            await simplified_ceo_agent.get_orchestration_plan(
                polished_requirements=None,
                session_id="test-session-123"
            )
        
        # Test with empty string
        with pytest.raises(ValueError, match="Polished requirements cannot be None or empty"):
            await simplified_ceo_agent.get_orchestration_plan(
                polished_requirements="",
                session_id="test-session-123"
            )
    
    @pytest.mark.asyncio
    async def test_conversation_flow_adds_task_field(self):
        """Test that conversation flow adds task field to response"""
        # Setup conversation flow with a polished prompt
        ceo_conversation_flow.current_analysis_session = {
            "session_id": "test-session-123",
            "task": "create an instagram post on genAi and post it",
            "analysis_result": {
                "state": "complete",
                "polished_prompt": "Create an Instagram post about GenAI",
                "final_completeness_score": 9
            }
        }
        
        # Mock the simplified CEO agent's get_orchestration_plan
        with patch.object(simplified_ceo_agent, 'get_orchestration_plan', new_callable=AsyncMock) as mock_orchestrate:
            mock_orchestrate.return_value = {
                "mode": "sequential",
                "steps": [{"agent_id": "content_writer"}]
            }
            
            # Process user confirmation
            result = await ceo_conversation_flow.process_user_message(
                session_id="test-session-123",
                message="yes",
                session_data={"state": "awaiting_confirmation", "polished_prompt": "Create an Instagram post about GenAI"}
            )
            
            # Verify task field is added to response
            assert "task" in result
            assert result["task"] == "Create an Instagram post about GenAI"
            assert result["polished_prompt"] == "Create an Instagram post about GenAI"
            assert result["orchestration_started"] == True
    
    @pytest.mark.asyncio
    async def test_finalize_requirements_validates_polished_prompt(self):
        """Test that finalize_requirements validates polished prompt before orchestration"""
        # Test with no polished prompt available
        ceo_conversation_flow.current_analysis_session = None
        
        result = await ceo_conversation_flow.finalize_requirements(
            session_id="test-session-123",
            session_data={},
            request_id="req-123"
        )
        
        assert result["success"] == False
        assert result["error"] == "No polished prompt available from AI analysis"
    
    @pytest.mark.asyncio
    async def test_orchestration_error_handling(self):
        """Test error handling when orchestration API fails"""
        # Mock the httpx client to simulate API error
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock to raise exception
            mock_client_instance = AsyncMock()
            mock_client_instance.post.side_effect = Exception("Connection error")
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Test orchestration with error
            with pytest.raises(Exception, match="Connection error"):
                await simplified_ceo_agent.get_orchestration_plan(
                    polished_requirements="Valid task",
                    session_id="test-session-123"
                )


def run_tests():
    """Run all tests and print results"""
    print("\n=== Running Orchestration Fix Tests ===")
    print("\nTesting orchestration API fix for null task parameter...\n")
    
    # Run pytest with verbose output
    pytest.main(["-v", __file__, "-s"])


if __name__ == "__main__":
    run_tests()
