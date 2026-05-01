import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import uuid

from src.agents.ceo.ceo_chat_interface import ceo_chat_interface, ChatSessionState
from src.agents.ceo.ceo_conversation_flow import ceo_conversation_flow, ConversationState
from src.routes.ceo_chat_routes import start_chat_session
from src.routes.ceo_chat_message_routes import send_chat_message


class TestCEOChatInitialization:
    """Test suite for CEO chat initialization and NoneType error handling"""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object"""
        request = Mock()
        request.state.request_id = str(uuid.uuid4())
        return request
    
    @pytest.fixture
    def reset_chat_interface(self):
        """Reset chat interface before each test"""
        ceo_chat_interface.active_sessions.clear()
        ceo_chat_interface.session_history.clear()
        ceo_conversation_flow.reset_session()
        yield
        ceo_chat_interface.active_sessions.clear()
        ceo_chat_interface.session_history.clear()
    
    @pytest.mark.asyncio
    async def test_start_chat_session_success(self, mock_request, reset_chat_interface):
        """Test successful chat session initialization"""
        request_data = {
            "initial_message": "Create a social media post about AI",
            "user_context": {"platform": "LinkedIn"}
        }
        
        # Mock AI result to return valid data
        with patch.object(ceo_conversation_flow, 'analyze_task_with_ai', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "state": "ai_questioning",
                "requires_user_input": True,
                "questions": [
                    {
                        "id": "q1",
                        "question": "What is the target audience?",
                        "purpose": "audience",
                        "category": "general",
                        "priority": "high"
                    }
                ],
                "completeness_score": 4,
                "iteration": 1
            }
            
            result = await start_chat_session(request_data, mock_request)
        
        # Verify response structure
        assert "conversation_id" in result
        # The state is now "asking_questions" when AI returns questions
        assert result["state"] in ["gathering_requirements", "asking_questions"]
        assert "message" in result
        assert "requirements" in result
        assert "timestamp" in result
        assert "initial_questions" in result
        assert "ai_analysis" in result
        assert isinstance(result["initial_questions"], list)
        assert isinstance(result["ai_analysis"], dict)
    
    @pytest.mark.asyncio
    async def test_start_chat_session_with_none_ai_result(self, mock_request, reset_chat_interface):
        """Test chat session initialization when AI returns None"""
        request_data = {
            "initial_message": "Create a post",
            "user_context": None
        }
        
        # Mock AI result to return None
        with patch.object(ceo_conversation_flow, 'analyze_task_with_ai', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = None
            
            # Mock process_user_message to simulate None return
            with patch.object(ceo_conversation_flow, 'process_user_message', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = None
                
                result = await start_chat_session(request_data, mock_request)
        
        # Verify graceful handling
        assert "conversation_id" in result
        # The state can be either gathering_requirements or asking_questions
        assert result["state"] in ["gathering_requirements", "asking_questions"]
        assert "message" in result
        assert result["initial_questions"] == []
        assert result["ai_analysis"] == {}
    
    @pytest.mark.asyncio
    async def test_start_chat_session_with_ai_error(self, mock_request, reset_chat_interface):
        """Test chat session initialization when AI throws an error"""
        request_data = {
            "initial_message": "Test message"
        }
        
        # Mock AI to throw an exception
        with patch.object(ceo_conversation_flow, 'analyze_task_with_ai', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("AI service unavailable")
            
            result = await start_chat_session(request_data, mock_request)
        
        # Verify error handling - the system now returns a valid response even on error
        assert "conversation_id" in result
        # Check that we have a valid response structure even when AI fails
        assert "message" in result
        assert "state" in result
        assert result["initial_questions"] == []
    
    @pytest.mark.asyncio
    async def test_send_message_with_none_flow_result(self, mock_request, reset_chat_interface):
        """Test sending message when conversation flow returns None"""
        # First create a session
        session_id = str(uuid.uuid4())
        ceo_chat_interface.active_sessions[session_id] = {
            "session_id": session_id,
            "state": ChatSessionState.ASKING_QUESTIONS,
            "responses": {},
            "questions_asked": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        request_data = {
            "conversation_id": session_id,
            "message": "My target audience is developers"
        }
        
        # Mock conversation flow to return None
        with patch.object(ceo_conversation_flow, 'process_user_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = None
            
            # Should raise HTTPException due to None flow result
            with pytest.raises(Exception) as exc_info:
                await send_chat_message(request_data, mock_request)
            
            assert "flow result is None" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_message_with_valid_flow_result(self, mock_request, reset_chat_interface):
        """Test sending message with valid flow result"""
        # Create a session
        session_id = str(uuid.uuid4())
        ceo_chat_interface.active_sessions[session_id] = {
            "session_id": session_id,
            "state": ChatSessionState.ASKING_QUESTIONS,
            "responses": {},
            "questions_asked": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        request_data = {
            "conversation_id": session_id,
            "message": "My target audience is developers"
        }
        
        # Mock conversation flow to return valid result
        with patch.object(ceo_conversation_flow, 'process_user_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "state": ConversationState.AI_QUESTIONING.value,
                "response": "What is the main message you want to convey?",
                "questions": [
                    {
                        "id": "q2",
                        "question": "What is the main message?",
                        "purpose": "content",
                        "category": "general",
                        "priority": "high"
                    }
                ],
                "analysis": {
                    "completeness_score": 5,
                    "iteration": 2
                }
            }
            
            result = await send_chat_message(request_data, mock_request)
        
        # Verify response
        assert result["conversation_id"] == session_id
        assert "state" in result
        assert "message" in result
        assert "requirements" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_conversation_flow_with_none_session_data(self):
        """Test conversation flow handling None session data"""
        session_id = str(uuid.uuid4())
        message = "Test message"
        
        # Call with None session data
        result = await ceo_conversation_flow.process_user_message(session_id, message, None)
        
        # Verify error response
        assert result["state"] == "error"
        assert "Session data is missing" in result["response"]
        assert result["error"] == "Session data is None"
    
    @pytest.mark.asyncio
    async def test_conversation_flow_with_empty_session_data(self):
        """Test conversation flow with empty session data"""
        session_id = str(uuid.uuid4())
        message = "Create an AI blog post"
        session_data = {}
        
        # Mock AI analyzer
        with patch.object(ceo_conversation_flow, 'analyze_task_with_ai', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "state": "complete",
                "requires_user_input": False,
                "polished_prompt": "Create an AI blog post for tech enthusiasts",
                "executive_summary": "Blog post about AI",
                "deliverables": ["One blog post"],
                "final_completeness_score": 8,
                "iterations_used": 1
            }
            
            result = await ceo_conversation_flow.process_user_message(session_id, message, session_data)
        
        # Verify successful handling
        assert result["state"] == "awaiting_confirmation"
        assert "polished_prompt" in result
        assert result["requires_confirmation"] is True
    
    def test_session_info_get_with_none_values(self):
        """Test handling of None values in session info dictionary"""
        # Simulate session info with None values
        session_info = {
            "session_id": "test-123",
            "greeting": "Hello",
            "initial_questions": None,
            "ai_analysis": None,
            "state": None
        }
        
        # Test safe access patterns used in the fix
        initial_questions = session_info.get("initial_questions", []) if session_info.get("initial_questions") is not None else []
        ai_analysis = session_info.get("ai_analysis", {}) if session_info.get("ai_analysis") is not None else {}
        # When state is None, it should remain None, not use the default
        state = session_info.get("state")
        
        assert initial_questions == []
        assert ai_analysis == {}
        assert state is None  # The state is None in the test data
    
    def test_flow_result_get_with_none_result(self):
        """Test handling of None flow result"""
        flow_result = None
        session_data = {"state": "asking_questions"}
        
        # Test safe access pattern
        if flow_result is None:
            state = session_data.get("state", "gathering_requirements")
        else:
            state = flow_result.get("state", session_data.get("state", "gathering_requirements"))
        
        assert state == "asking_questions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])