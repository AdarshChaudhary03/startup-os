import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from ceo_chat_interface import ChatSessionState

client = TestClient(app)


class TestCEOChatAPIIntegration:
    """Test suite for CEO chat API integration"""
    
    def test_start_chat_with_valid_request(self):
        """Test starting a chat session with valid request data"""
        
        # Mock the chat interface
        with patch('ceo_chat_routes.ceo_chat_interface') as mock_interface:
            mock_interface.start_chat_session.return_value = {
                "session_id": "test-session-123",
                "greeting": "Hello! I'm your CEO assistant.",
                "initial_questions": ["What is the main purpose?"],
                "max_questions": 5
            }
            
            response = client.post(
                "/api/ceo/chat/start",
                json={"initial_message": "I need to build a user authentication system"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "test-session-123"
            assert data["state"] == "gathering_requirements"
            assert "message" in data
            assert "timestamp" in data
    
    def test_start_chat_missing_initial_message(self):
        """Test starting a chat session without initial_message"""
        
        response = client.post(
            "/api/ceo/chat/start",
            json={}
        )
        
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail or "message" in error_detail
        error_msg = error_detail.get("detail", error_detail.get("message", ""))
        assert "initial_message is required" in error_msg
    
    def test_send_message_valid_request(self):
        """Test sending a message in an existing chat session"""
        
        # Mock the chat interface and conversation flow
        with patch('ceo_chat_message_routes.ceo_chat_interface') as mock_interface, \
             patch('ceo_chat_message_routes.ceo_conversation_flow') as mock_flow:
            
            # Setup mocks
            mock_interface.active_sessions = {
                "test-session-123": {
                    "state": ChatSessionState.ASKING_QUESTIONS,
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            }
            
            mock_flow.process_user_message.return_value = {
                "state": "gathering_requirements",
                "response": "Thank you for that information. Can you tell me more about your target audience?",
                "requirements": {"purpose": "user authentication"}
            }
            
            response = client.post(
                "/api/ceo/chat/message",
                json={
                    "conversation_id": "test-session-123",
                    "message": "The system is for enterprise users"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "test-session-123"
            assert data["state"] == "gathering_requirements"
            assert "message" in data
            assert "requirements" in data
    
    def test_send_message_missing_fields(self):
        """Test sending a message with missing required fields"""
        
        # Test missing conversation_id
        response = client.post(
            "/api/ceo/chat/message",
            json={"message": "test message"}
        )
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail or "message" in error_detail
        error_msg = error_detail.get("detail", error_detail.get("message", ""))
        assert "conversation_id and message are required" in error_msg
        
        # Test missing message
        response = client.post(
            "/api/ceo/chat/message",
            json={"conversation_id": "test-123"}
        )
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail or "message" in error_detail
        error_msg = error_detail.get("detail", error_detail.get("message", ""))
        assert "conversation_id and message are required" in error_msg
    
    def test_send_message_nonexistent_conversation(self):
        """Test sending a message to a non-existent conversation"""
        
        with patch('ceo_chat_message_routes.ceo_chat_interface') as mock_interface:
            mock_interface.active_sessions = {}
            
            response = client.post(
                "/api/ceo/chat/message",
                json={
                    "conversation_id": "nonexistent-123",
                    "message": "test message"
                }
            )
            
            assert response.status_code == 404
            error_detail = response.json()
            assert "detail" in error_detail or "message" in error_detail
            error_msg = error_detail.get("detail", error_detail.get("message", ""))
            assert "Conversation not found" in error_msg
    
    def test_get_chat_state(self):
        """Test getting the state of a chat conversation"""
        
        with patch('ceo_chat_message_routes.ceo_chat_interface') as mock_interface:
            mock_interface.active_sessions = {
                "test-session-123": {
                    "state": ChatSessionState.ASKING_QUESTIONS,
                    "polished_requirements": {"purpose": "authentication"},
                    "questions_asked": ["q1", "q2"]
                }
            }
            
            response = client.get("/api/ceo/chat/test-session-123/state")
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "test-session-123"
            assert data["state"] == "asking_questions"
            assert data["questions_asked"] == 2
    
    def test_finalize_requirements(self):
        """Test finalizing requirements and creating execution plan"""
        
        with patch('ceo_chat_message_routes.ceo_chat_interface') as mock_interface, \
             patch('ceo_chat_message_routes.ceo_conversation_flow') as mock_flow:
            
            mock_interface.active_sessions = {
                "test-session-123": {
                    "state": ChatSessionState.COMPLETE
                }
            }
            
            mock_flow.finalize_requirements.return_value = {
                "requirements": {
                    "purpose": "user authentication",
                    "target_audience": "enterprise users",
                    "key_features": ["SSO", "MFA", "Role-based access"]
                },
                "plan": {
                    "agents": ["backend_agent", "security_agent"],
                    "steps": ["Design API", "Implement auth logic", "Add security measures"]
                }
            }
            
            response = client.post("/api/ceo/chat/test-session-123/finalize")
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "test-session-123"
            assert data["success"] is True
            assert "requirements" in data
            assert "plan" in data
    
    def test_api_error_handling(self):
        """Test API error handling for various scenarios"""
        
        # Test internal server error handling
        with patch('ceo_chat_routes.ceo_chat_interface') as mock_interface:
            mock_interface.start_chat_session.side_effect = Exception("Internal error")
            
            response = client.post(
                "/api/ceo/chat/start",
                json={"initial_message": "test"}
            )
            
            assert response.status_code == 500
            error_detail = response.json()
            assert "detail" in error_detail or "message" in error_detail
            error_msg = error_detail.get("detail", error_detail.get("message", ""))
            assert "Internal error" in error_msg
    
    def test_frontend_api_client_integration(self):
        """Test that the frontend API client can properly handle responses"""
        
        # Simulate the exact request the frontend would make
        with patch('ceo_chat_routes.ceo_chat_interface') as mock_interface:
            mock_interface.start_chat_session.return_value = {
                "session_id": "test-session-123",
                "greeting": "Hello! Let me help you with your project.",
                "initial_questions": [],
                "max_questions": 5
            }
            
            # This mimics the exact request from the frontend
            response = client.post(
                "/api/ceo/chat/start",
                json={"initial_message": "Build a task management app"},
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            
            # Verify the response can be parsed as JSON
            data = response.json()
            
            # Verify the response structure matches what the frontend expects
            assert "conversation_id" in data
            assert "state" in data
            assert "message" in data
            assert "requirements" in data
            assert "timestamp" in data
            
            # Verify the response body hasn't been consumed
            # (This would have caused the "body stream already read" error)
            assert response.text  # This should not raise an error


if __name__ == "__main__":
    pytest.main(["-v", __file__])