import pytest
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ceo_conversation_flow import CEOConversationFlow, ConversationState


class TestCEOConversationFlow:
    """Test suite for CEOConversationFlow class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.flow = CEOConversationFlow()
    
    def test_process_user_message_initial_state(self):
        """Test processing message in initial state"""
        session_data = {
            "state": ConversationState.INITIAL,
            "responses": {},
            "questions_asked": []
        }
        
        result = self.flow.process_user_message(
            session_id="test-session",
            message="I need help building a web application",
            session_data=session_data
        )
        
        assert "state" in result
        assert "response" in result
        assert "question" in result
        assert len(session_data["questions_asked"]) == 1
    
    def test_process_user_message_with_purpose_response(self):
        """Test processing purpose response"""
        session_data = {
            "state": ConversationState.GATHERING_PURPOSE,
            "responses": {},
            "questions_asked": [{
                "id": "q_purpose_1",
                "area": "purpose",
                "question": "What is the main purpose?",
                "type": "primary"
            }]
        }
        
        result = self.flow.process_user_message(
            session_id="test-session",
            message="I want to create an e-commerce platform for selling handmade crafts",
            session_data=session_data
        )
        
        assert session_data["responses"]["purpose"] == "I want to create an e-commerce platform for selling handmade crafts"
        assert "response" in result
        assert "requirements" in result
    
    def test_process_user_message_validation_failure(self):
        """Test validation failure for short responses"""
        session_data = {
            "state": ConversationState.GATHERING_PURPOSE,
            "responses": {},
            "questions_asked": [{
                "id": "q_purpose_1",
                "area": "purpose",
                "question": "What is the main purpose?",
                "type": "primary"
            }]
        }
        
        result = self.flow.process_user_message(
            session_id="test-session",
            message="Website",  # Too short
            session_data=session_data
        )
        
        # Should trigger follow-up due to short response
        assert len(session_data["questions_asked"]) == 2
        assert session_data["questions_asked"][-1]["type"] == "follow_up"
    
    def test_process_user_message_complete_requirements(self):
        """Test completing requirements gathering"""
        session_data = {
            "state": ConversationState.GATHERING_TIMELINE,
            "responses": {
                "purpose": "Build an e-commerce platform for handmade crafts",
                "audience": "Craft enthusiasts and collectors worldwide",
                "scope": "Product catalog, shopping cart, payment integration"
            },
            "questions_asked": [
                {"id": "q_purpose_1", "area": "purpose"},
                {"id": "q_audience_2", "area": "audience"},
                {"id": "q_scope_3", "area": "scope"}
            ]
        }
        
        result = self.flow.process_user_message(
            session_id="test-session",
            message="We need this completed within 3 months",
            session_data=session_data
        )
        
        assert result["state"] == "requirements_complete"
        assert "requirements" in result
        assert session_data["state"] == ConversationState.COMPLETE
    
    def test_process_user_message_vague_response_triggers_followup(self):
        """Test that vague responses trigger follow-up questions"""
        session_data = {
            "state": ConversationState.GATHERING_AUDIENCE,
            "responses": {"purpose": "Build a web application"},
            "questions_asked": [{
                "id": "q_audience_1",
                "area": "audience",
                "question": "Who is the target audience?",
                "type": "primary"
            }]
        }
        
        result = self.flow.process_user_message(
            session_id="test-session",
            message="Maybe some users, not sure exactly",
            session_data=session_data
        )
        
        # Should trigger follow-up due to vague response
        assert "question" in result
        assert result["question"]["type"] == "follow_up"
        # Verify a follow-up question was added to the session
        assert len(session_data["questions_asked"]) == 2
        assert session_data["questions_asked"][-1]["type"] == "follow_up"
    
    def test_finalize_requirements(self):
        """Test finalizing requirements and creating plan"""
        session_data = {
            "responses": {
                "purpose": "Build an e-commerce platform",
                "audience": "Craft enthusiasts",
                "scope": "Full e-commerce functionality",
                "timeline": "3 months",
                "constraints": "Budget of $50,000"
            }
        }
        
        result = self.flow.finalize_requirements(
            session_id="test-session",
            session_data=session_data
        )
        
        assert result["success"] is True
        assert "requirements" in result
        assert "plan" in result
        assert result["plan"]["ready_for_execution"] is True
    
    def test_process_user_message_max_questions_limit(self):
        """Test that conversation completes after maximum questions"""
        session_data = {
            "state": ConversationState.GATHERING_CONSTRAINTS,
            "responses": {
                "purpose": "Build a platform",
                "audience": "General users"
            },
            "questions_asked": [
                {"id": "q_1", "area": "purpose"},
                {"id": "q_2", "area": "audience"},
                {"id": "q_3", "area": "scope"},
                {"id": "q_4", "area": "timeline"},
                {"id": "q_5", "area": "constraints"}
            ]
        }
        
        result = self.flow.process_user_message(
            session_id="test-session",
            message="No specific constraints",
            session_data=session_data
        )
        
        # Should complete after 5 questions
        assert result["state"] == "requirements_complete"
        assert session_data["state"] == ConversationState.COMPLETE
    
    def test_process_user_message_urgent_timeline(self):
        """Test urgent timeline detection"""
        session_data = {
            "state": ConversationState.GATHERING_TIMELINE,
            "responses": {
                "purpose": "Build an app",
                "audience": "Mobile users"
            },
            "questions_asked": [{
                "id": "q_timeline_1",
                "area": "timeline",
                "question": "When do you need this?",
                "type": "primary"
            }]
        }
        
        result = self.flow.process_user_message(
            session_id="test-session",
            message="We need this ASAP, it's urgent!",
            session_data=session_data
        )
        
        assert "timeline" in session_data["responses"]
        requirements = result["requirements"]
        assert requirements["priority"] == "urgent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])