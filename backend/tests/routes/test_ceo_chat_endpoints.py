import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import uuid

from src.routes.ceo_chat_routes import ceo_chat_router
from src.agents.ceo.ceo_chat_interface import ChatSessionState
from src.core.models import CEOPolishedRequirement
from src.agents.ceo.ceo_conversation_flow import ConversationState


class TestCEOChatEndpoints:
    """Test cases for CEO chat endpoints"""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request object"""
        request = Mock()
        request.state = Mock()
        request.state.request_id = str(uuid.uuid4())
        return request
    
    @pytest.fixture
    def mock_ceo_chat_interface(self):
        """Create mock CEO chat interface"""
        with patch('src.routes.ceo_chat_routes.ceo_chat_interface') as mock:
            yield mock
    
    @pytest.fixture
    def mock_conversation_flow(self):
        """Create mock conversation flow"""
        with patch('src.agents.ceo.ceo_chat_interface.ceo_conversation_flow') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_start_chat_session_success(self, mock_request, mock_ceo_chat_interface):
        """Test successful chat session start"""
        # Arrange
        session_id = str(uuid.uuid4())
        request_data = {
            "initial_message": "I need to build a content management system",
            "user_context": {"industry": "tech"}
        }
        
        mock_session_info = {
            "session_id": session_id,
            "greeting": "Hello! I'll help you with your requirements.",
            "initial_questions": [
                {"id": "q1", "question": "What is the main purpose?"}
            ],
            "state": "gathering_requirements",
            "max_questions": 5,
            "ai_analysis": {"completeness_score": 6}
        }
        
        mock_ceo_chat_interface.start_chat_session = AsyncMock(return_value=mock_session_info)
        
        # Import the endpoint function
        from src.routes.ceo_chat_routes import start_chat_session
        
        # Act
        result = await start_chat_session(request_data, mock_request)
        
        # Assert
        assert result["conversation_id"] == session_id
        assert result["state"] == "gathering_requirements"
        assert result["message"] == mock_session_info["greeting"]
        assert "timestamp" in result
        assert "initial_questions" in result
        assert "ai_analysis" in result
    
    @pytest.mark.asyncio
    async def test_start_chat_session_missing_message(self, mock_request):
        """Test chat session start with missing initial message"""
        # Arrange
        request_data = {"user_context": {"industry": "tech"}}
        
        # Import the endpoint function
        from src.routes.ceo_chat_routes import start_chat_session
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await start_chat_session(request_data, mock_request)
        
        assert "initial_message is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_start_chat_session_with_error_handling(self, mock_request, mock_ceo_chat_interface):
        """Test chat session start with AI error - should handle gracefully"""
        # Arrange
        request_data = {
            "initial_message": "I need to build a system",
            "user_context": {}
        }
        
        # Simulate AI error
        mock_ceo_chat_interface.start_chat_session = AsyncMock(
            side_effect=Exception("AI service temporarily unavailable")
        )
        
        # Import the endpoint function
        from src.routes.ceo_chat_routes import start_chat_session
        
        # Act
        result = await start_chat_session(request_data, mock_request)
        
        # Assert - Should return graceful error response
        assert "conversation_id" in result
        assert result["state"] == "error"
        assert "encountered an issue" in result["message"]
        assert "error_details" in result
    
    @pytest.mark.asyncio
    async def test_submit_response_success(self, mock_request, mock_ceo_chat_interface):
        """Test successful response submission"""
        # Arrange
        session_id = str(uuid.uuid4())
        response_data = {
            "question_id": "q1",
            "response": "The main purpose is to manage blog content"
        }
        
        mock_result = {
            "action": "ask_next",
            "question": {"id": "q2", "question": "Who is your target audience?"},
            "message": "Let me ask you about another aspect.",
            "questions_remaining": 4,
            "ai_analysis": {"completeness_score": 7}
        }
        
        mock_ceo_chat_interface.process_user_response = AsyncMock(return_value=mock_result)
        
        # Import the endpoint function
        from src.routes.ceo_chat_routes import submit_response
        
        # Act
        result = await submit_response(session_id, response_data, mock_request)
        
        # Assert
        assert result["status"] == "success"
        assert result["action"] == "ask_next"
        assert result["next_question"] == mock_result["question"]
        assert result["questions_remaining"] == 4
    
    @pytest.mark.asyncio
    async def test_submit_response_error_handling(self, mock_request, mock_ceo_chat_interface):
        """Test response submission with error - should handle gracefully"""
        # Arrange
        session_id = str(uuid.uuid4())
        response_data = {
            "question_id": "q1",
            "response": "My response"
        }
        
        # Simulate processing error
        mock_ceo_chat_interface.process_user_response = AsyncMock(
            return_value={"action": "error", "message": "Processing failed", "error": "AI error"}
        )
        
        # Import the endpoint function
        from src.routes.ceo_chat_routes import submit_response
        
        # Act
        result = await submit_response(session_id, response_data, mock_request)
        
        # Assert - Should return warning status
        assert result["status"] == "warning"
        assert result["action"] == "continue"
    
    @pytest.mark.asyncio
    async def test_confirm_requirements_success(self, mock_request, mock_ceo_chat_interface):
        """Test successful requirements confirmation"""
        # Arrange
        session_id = str(uuid.uuid4())
        confirmation_data = {"confirmed": True}
        
        mock_polished_req = CEOPolishedRequirement(
            polished_task="Build a content management system for blogs",
            objective="Manage blog content efficiently",
            target_audience="Content creators",
            deliverables=["CMS platform"],
            success_criteria=["Easy to use"],
            constraints=["Budget: $10k"],
            timeline="3 months",
            additional_context="Tech blog focus",
            agent_plan_suggestion="Use Content Writer Agent"
        )
        
        mock_result = {
            "action": "requirements_complete",
            "polished_requirements": mock_polished_req,
            "message": "Perfect! Requirements finalized."
        }
        
        mock_ceo_chat_interface.confirm_requirements = AsyncMock(return_value=mock_result)
        mock_ceo_chat_interface.active_sessions = {
            session_id: {
                "original_task": "Build CMS",
                "responses": {"q1": "For blogs"}
            }
        }
        
        # Mock the analyzer and planner
        with patch('src.routes.ceo_chat_routes.ceo_requirements_analyzer') as mock_analyzer, \
             patch('src.routes.ceo_chat_routes.ceo_agent_planner') as mock_planner:
            
            mock_analyzer.analyze_requirements = AsyncMock(
                return_value={"analysis": "Complete"}
            )
            mock_planner.create_agent_plan = AsyncMock(
                return_value={"plan": "Use content agents"}
            )
            
            # Import the endpoint function
            from src.routes.ceo_chat_routes import confirm_requirements
            
            # Act
            result = await confirm_requirements(session_id, confirmation_data, mock_request)
            
            # Assert
            assert result["status"] == "success"
            assert result["action"] == "requirements_complete"
            assert "polished_requirements" in result
            assert result["next_step"] == "proceed_to_execution"
    
    @pytest.mark.asyncio
    async def test_confirm_requirements_with_adjustments(self, mock_request, mock_ceo_chat_interface):
        """Test requirements confirmation with adjustments"""
        # Arrange
        session_id = str(uuid.uuid4())
        confirmation_data = {
            "confirmed": False,
            "adjustments": "Please add mobile app support"
        }
        
        mock_result = {
            "action": "requirements_adjusted",
            "requirements_summary": {"updated": True},
            "message": "I've updated the requirements.",
            "next_step": "Please review the updated requirements."
        }
        
        mock_ceo_chat_interface.confirm_requirements = AsyncMock(return_value=mock_result)
        
        # Import the endpoint function
        from src.routes.ceo_chat_routes import confirm_requirements
        
        # Act
        result = await confirm_requirements(session_id, confirmation_data, mock_request)
        
        # Assert
        assert result["status"] == "success"
        assert result["action"] == "requirements_adjusted"
        assert "requirements_summary" in result
    
    @pytest.mark.asyncio
    async def test_get_chat_status_success(self, mock_ceo_chat_interface):
        """Test getting chat session status"""
        # Arrange
        session_id = str(uuid.uuid4())
        
        mock_status = {
            "session_id": session_id,
            "state": ChatSessionState.ASKING_QUESTIONS.value,
            "questions_asked": 2,
            "max_questions": 5,
            "responses_collected": 2,
            "current_question": {"id": "q3", "question": "What features?"},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_complete": False
        }
        
        mock_ceo_chat_interface.get_session_status.return_value = mock_status
        
        # Import the endpoint function
        from src.routes.ceo_chat_routes import get_chat_status
        
        # Act
        result = await get_chat_status(session_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["session_info"] == mock_status
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_list_active_sessions(self, mock_ceo_chat_interface):
        """Test listing active chat sessions"""
        # Arrange
        session1_id = str(uuid.uuid4())
        session2_id = str(uuid.uuid4())
        
        mock_ceo_chat_interface.active_sessions = {
            session1_id: {
                "state": ChatSessionState.ASKING_QUESTIONS,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "questions_asked": ["q1", "q2"]
            },
            session2_id: {
                "state": ChatSessionState.COMPLETE,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "questions_asked": ["q1", "q2", "q3"]
            }
        }
        
        # Import the endpoint function
        from src.routes.ceo_chat_routes import list_active_sessions
        
        # Act
        result = await list_active_sessions()
        
        # Assert
        assert result["status"] == "success"
        assert result["total_sessions"] == 2
        assert len(result["sessions"]) == 2
        
        # Check first session
        session1 = next(s for s in result["sessions"] if s["session_id"] == session1_id)
        assert session1["state"] == ChatSessionState.ASKING_QUESTIONS.value
        assert session1["questions_asked"] == 2
        assert not session1["is_complete"]
        
        # Check second session
        session2 = next(s for s in result["sessions"] if s["session_id"] == session2_id)
        assert session2["state"] == ChatSessionState.COMPLETE.value
        assert session2["questions_asked"] == 3
        assert session2["is_complete"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])