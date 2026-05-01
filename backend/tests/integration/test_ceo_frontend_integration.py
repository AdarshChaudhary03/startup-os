import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json
import sys
import os

# Add the backend src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from fastapi.testclient import TestClient
from src.routes.ceo_chat_message_routes import ceo_message_router
from src.agents.ceo.ceo_chat_interface import ceo_chat_interface


class TestCEOFrontendIntegration:
    """Integration tests for CEO chat frontend-backend flow"""
    
    @pytest.fixture
    def test_client(self):
        """Create a test client for the CEO message router"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(ceo_message_router)
        return TestClient(app)
    
    def test_message_response_includes_confirmation_flag(self, test_client):
        """Test that message response includes requires_confirmation flag"""
        # Set up mock session
        conversation_id = "test-conv-123"
        ceo_chat_interface.active_sessions[conversation_id] = {
            "conversation_id": conversation_id,
            "state": "initial",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        # Mock the conversation flow to return polished prompt
        with patch('src.routes.ceo_chat_message_routes.ceo_conversation_flow.process_user_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "state": "awaiting_confirmation",
                "response": "Here's the polished prompt...",
                "requires_confirmation": True,
                "polished_prompt": "Test polished prompt",
                "executive_summary": "Test summary",
                "deliverables": ["Test deliverable"]
            }
            
            # Send message
            response = test_client.post(
                "/api/ceo/chat/message",
                json={
                    "conversation_id": conversation_id,
                    "message": "create an instagram post"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response includes confirmation fields
            assert data["requires_confirmation"] == True
            assert data["polished_prompt"] == "Test polished prompt"
            assert data["executive_summary"] == "Test summary"
            assert data["deliverables"] == ["Test deliverable"]
    
    def test_session_data_stores_polished_prompt(self, test_client):
        """Test that session data properly stores polished prompt"""
        conversation_id = "test-conv-456"
        ceo_chat_interface.active_sessions[conversation_id] = {
            "conversation_id": conversation_id,
            "state": "initial"
        }
        
        with patch('src.routes.ceo_chat_message_routes.ceo_conversation_flow.process_user_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "state": "awaiting_confirmation",
                "response": "Polished prompt ready",
                "polished_prompt": "Stored polished prompt",
                "executive_summary": "Stored summary",
                "deliverables": ["Deliverable 1", "Deliverable 2"]
            }
            
            response = test_client.post(
                "/api/ceo/chat/message",
                json={
                    "conversation_id": conversation_id,
                    "message": "test message"
                }
            )
            
            assert response.status_code == 200
            
            # Verify session data was updated
            session = ceo_chat_interface.active_sessions[conversation_id]
            assert session["polished_prompt"] == "Stored polished prompt"
            assert session["executive_summary"] == "Stored summary"
            assert session["deliverables"] == ["Deliverable 1", "Deliverable 2"]
    
    def test_orchestration_receives_polished_prompt(self, test_client):
        """Test that orchestration receives the polished prompt correctly"""
        conversation_id = "test-conv-789"
        polished_prompt = "Final polished prompt for orchestration"
        
        # Set up session with polished prompt
        ceo_chat_interface.active_sessions[conversation_id] = {
            "conversation_id": conversation_id,
            "state": "awaiting_confirmation",
            "polished_prompt": polished_prompt
        }
        
        # Mock the conversation flow confirmation handling
        with patch('src.routes.ceo_chat_message_routes.ceo_conversation_flow.process_user_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "state": "complete",
                "response": "Orchestration started",
                "orchestration_started": True,
                "polished_prompt": polished_prompt,
                "task": polished_prompt,
                "orchestration_result": {
                    "mode": "sequential",
                    "steps": [{"agent_name": "test_agent"}]
                }
            }
            
            response = test_client.post(
                "/api/ceo/chat/message",
                json={
                    "conversation_id": conversation_id,
                    "message": "confirm"
                }
            )
            
            assert response.status_code == 200
            
            # Verify the mock was called with correct session data
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            assert call_args[1]["session_data"]["polished_prompt"] == polished_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
