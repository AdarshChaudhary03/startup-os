import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the backend src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from src.agents.ceo.ceo_conversation_flow import CEOConversationFlow
from src.agents.ceo.ceo_ai_task_analyzer import CEOAITaskAnalyzer


class TestCEOPolishedPromptFlow:
    """Test cases for CEO agent polished prompt storage and confirmation flow"""
    
    @pytest.fixture
    def ceo_flow(self):
        """Create a CEO conversation flow instance"""
        return CEOConversationFlow()
    
    @pytest.fixture
    def mock_session_data(self):
        """Create mock session data"""
        return {
            "state": "initial",
            "conversation_id": "test-session-123",
            "questions_asked": [],
            "answers": {}
        }
    
    @pytest.mark.asyncio
    async def test_polished_prompt_storage_in_session(self, ceo_flow, mock_session_data):
        """Test that polished prompt is stored in session data when created"""
        # Mock the AI task analyzer to return a polished prompt
        with patch.object(ceo_flow.ai_analyzer, 'analyze_task', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "state": "complete",
                "requires_user_input": False,
                "polished_prompt": "Test polished prompt for Instagram post",
                "executive_summary": "Create engaging Instagram content",
                "deliverables": ["Instagram post", "Caption", "Hashtags"],
                "final_completeness_score": 9,
                "iterations_used": 1
            }
            
            # Process initial message
            result = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="create an instagram post on genAi and post it",
                session_data=mock_session_data
            )
            
            # Verify response includes confirmation requirement
            assert result["state"] == "awaiting_confirmation"
            assert result["requires_confirmation"] == True
            assert result["polished_prompt"] == "Test polished prompt for Instagram post"
            assert "executive_summary" in result
            assert "deliverables" in result
    
    @pytest.mark.asyncio
    async def test_confirm_button_visibility_flag(self, ceo_flow, mock_session_data):
        """Test that requires_confirmation flag is set for frontend button visibility"""
        with patch.object(ceo_flow.ai_analyzer, 'analyze_task', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "state": "complete",
                "requires_user_input": False,
                "polished_prompt": "Refined task description",
                "executive_summary": "Summary",
                "deliverables": [],
                "final_completeness_score": 8
            }
            
            result = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="test task",
                session_data=mock_session_data
            )
            
            # Check that requires_confirmation flag is present
            assert result["requires_confirmation"] == True
            assert "Would you like to proceed" in result["response"]
    
    @pytest.mark.asyncio
    async def test_polished_prompt_retrieval_on_confirmation(self, ceo_flow, mock_session_data):
        """Test that polished prompt is retrieved correctly when user confirms"""
        # Set up session data with polished prompt
        mock_session_data["state"] = "awaiting_confirmation"
        mock_session_data["polished_prompt"] = "Test polished prompt"
        
        # Mock the simplified CEO agent
        with patch('src.agents.ceo.ceo_simplified_flow.simplified_ceo_agent') as mock_agent:
            mock_orchestrate = AsyncMock(return_value={
                "mode": "sequential",
                "steps": [{"agent_name": "content_writer", "instruction": "Write content"}]
            })
            mock_agent.get_orchestration_plan = mock_orchestrate
            
            # Process confirmation message
            result = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="yes, confirm",
                session_data=mock_session_data
            )
            
            # Verify orchestration was called with polished prompt
            mock_orchestrate.assert_called_once_with(
                polished_requirements="Test polished prompt",
                session_id="test-session-123"
            )
            
            assert result["orchestration_started"] == True
            assert result["polished_prompt"] == "Test polished prompt"
    
    @pytest.mark.asyncio
    async def test_polished_prompt_fallback_retrieval(self, ceo_flow, mock_session_data):
        """Test fallback retrieval from current analysis when not in session data"""
        # Set up session without polished prompt
        mock_session_data["state"] = "awaiting_confirmation"
        # No polished_prompt in session_data
        
        # Set up current analysis session with polished prompt
        ceo_flow.current_analysis_session = {
            "session_id": "test-session-123",
            "task": "test task",
            "analysis_result": {
                "state": "complete",
                "polished_prompt": "Fallback polished prompt"
            }
        }
        
        with patch('src.agents.ceo.ceo_simplified_flow.simplified_ceo_agent') as mock_agent:
            mock_orchestrate = AsyncMock(return_value={
                "mode": "sequential",
                "steps": []
            })
            mock_agent.get_orchestration_plan = mock_orchestrate
            
            # Process confirmation
            result = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="confirm",
                session_data=mock_session_data
            )
            
            # Verify fallback retrieval worked
            mock_orchestrate.assert_called_once_with(
                polished_requirements="Fallback polished prompt",
                session_id="test-session-123"
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_when_no_polished_prompt(self, ceo_flow, mock_session_data):
        """Test error handling when polished prompt is not available"""
        # Set up session without polished prompt
        mock_session_data["state"] = "awaiting_confirmation"
        # No polished_prompt in session_data
        
        # No current analysis session either
        ceo_flow.current_analysis_session = None
        
        # Process confirmation
        result = await ceo_flow.process_user_message(
            session_id="test-session-123",
            message="confirm",
            session_data=mock_session_data
        )
        
        # Verify error response
        assert result["state"] == "error"
        assert "couldn't find the polished prompt" in result["response"]
        assert result["error"] == "Polished prompt not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
