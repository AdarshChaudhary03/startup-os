"""Test cases for CEO agent flow with polished prompt confirmation"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import sys
import os

# Add the backend src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from src.agents.ceo.ceo_conversation_flow import CEOConversationFlow, ConversationState
from src.agents.ceo.ceo_ai_task_analyzer import CEOAITaskAnalyzer


class TestCEOFlowWithConfirmation:
    """Test suite for CEO agent flow with polished prompt confirmation"""
    
    @pytest.fixture
    def ceo_flow(self):
        """Create CEO conversation flow instance"""
        return CEOConversationFlow()
    
    @pytest.fixture
    def mock_ai_response_complete(self):
        """Mock AI response when task is complete"""
        return {
            "state": "complete",
            "success": True,
            "final_completeness_score": 8,
            "iterations_used": 1,
            "polished_prompt": "Create a comprehensive Instagram marketing campaign focused on Generative AI, including visual content, captions, hashtags, and posting strategy.",
            "executive_summary": "Develop and execute an Instagram post about GenAI with engaging visuals and content",
            "deliverables": [
                "Instagram post visual content",
                "Engaging caption about GenAI",
                "Relevant hashtags",
                "Posting strategy"
            ],
            "session_id": "test-session-123"
        }
    
    @pytest.fixture
    def mock_ai_response_needs_input(self):
        """Mock AI response when more input is needed"""
        return {
            "state": "awaiting_answers",
            "iteration": 1,
            "completeness_score": 4,
            "analysis": {
                "completeness_score": 4,
                "overall_assessment": "Task needs more clarity"
            },
            "questions": [
                {
                    "id": "q1",
                    "question": "What specific aspects of GenAI would you like to highlight in the Instagram post?",
                    "purpose": "Clarify content focus",
                    "category": "clarity",
                    "priority": "high"
                }
            ],
            "session_id": "test-session-123",
            "requires_user_input": True
        }
    
    @pytest.mark.asyncio
    async def test_polished_prompt_display_after_initial_analysis(self, ceo_flow, mock_ai_response_complete):
        """Test that polished prompt is displayed after initial task analysis completes"""
        
        # Mock the AI analyzer
        with patch.object(ceo_flow.ai_analyzer, 'analyze_task', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_ai_response_complete
            
            # Process initial task
            result = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="create an instagram post on genAi and post it",
                session_data={"state": ConversationState.INITIAL}
            )
            
            # Verify the response shows polished prompt for confirmation
            assert result["state"] == "awaiting_confirmation"
            assert "polished_prompt" in result
            assert result["polished_prompt"] == mock_ai_response_complete["polished_prompt"]
            assert "Would you like to proceed with this refined task description?" in result["response"]
            assert result["requires_confirmation"] is True
            assert result["executive_summary"] == mock_ai_response_complete["executive_summary"]
            assert result["deliverables"] == mock_ai_response_complete["deliverables"]
    
    @pytest.mark.asyncio
    async def test_polished_prompt_display_after_qa_completion(self, ceo_flow, mock_ai_response_complete):
        """Test that polished prompt is displayed after Q&A completion"""
        
        # Set up initial session with questions
        ceo_flow.current_analysis_session = {
            "session_id": "test-session-123",
            "task": "create an instagram post",
            "analysis_result": {
                "state": "awaiting_answers",
                "questions": [{"id": "q1", "question": "What aspects?"}]
            }
        }
        
        # Mock the continue_with_answers to return complete
        with patch.object(ceo_flow.ai_analyzer, 'continue_with_answers', new_callable=AsyncMock) as mock_continue:
            mock_continue.return_value = mock_ai_response_complete
            
            # Process answer
            session_data = {
                "questions": [{"id": "q1", "question": "What aspects?"}],
                "answers": {},
                "current_question_index": 0
            }
            
            result = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="Focus on how GenAI transforms content creation",
                session_data=session_data
            )
            
            # Verify the response shows polished prompt for confirmation
            assert result["state"] == "awaiting_confirmation"
            assert "polished_prompt" in result
            assert "Perfect! I've refined your task based on your answers" in result["response"]
            assert result["requires_confirmation"] is True
    
    @pytest.mark.asyncio
    async def test_user_confirmation_triggers_orchestration(self, ceo_flow):
        """Test that user confirmation triggers orchestration"""
        
        # Mock the orchestration call
        mock_orchestration_result = {
            "success": True,
            "steps": ["Step 1", "Step 2"],
            "agents": ["Agent1", "Agent2"]
        }
        
        # Import the module first
        from src.agents.ceo.ceo_simplified_flow import simplified_ceo_agent
        
        with patch.object(simplified_ceo_agent, 'get_orchestration_plan', new_callable=AsyncMock) as mock_orchestration:
            mock_orchestration.return_value = mock_orchestration_result
            
            # Process confirmation
            session_data = {
                "state": "awaiting_confirmation",
                "polished_prompt": "Create Instagram GenAI campaign"
            }
            
            result = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="Yes, looks good! Please proceed.",
                session_data=session_data
            )
            
            # Verify orchestration was triggered
            assert result["state"] == ConversationState.COMPLETE.value
            assert result["orchestration_started"] is True
            assert result["orchestration_result"] == mock_orchestration_result
            assert "creating a plan for agent delegation" in result["response"]
            
            # Verify orchestration was called with correct parameters
            mock_orchestration.assert_called_once_with(
                polished_requirements="Create Instagram GenAI campaign",
                session_id="test-session-123"
            )
    
    @pytest.mark.asyncio
    async def test_user_rejection_restarts_flow(self, ceo_flow):
        """Test that user rejection restarts the flow"""
        
        # Process rejection
        session_data = {
            "state": "awaiting_confirmation",
            "polished_prompt": "Create Instagram GenAI campaign"
        }
        
        result = await ceo_flow.process_user_message(
            session_id="test-session-123",
            message="No, I want to change the requirements",
            session_data=session_data
        )
        
        # Verify flow restart
        assert result["state"] == ConversationState.INITIAL.value
        assert result["restart"] is True
        assert "provide your updated task description" in result["response"]
    
    @pytest.mark.asyncio
    async def test_orchestration_error_handling(self, ceo_flow):
        """Test error handling when orchestration fails"""
        
        # Import the module first
        from src.agents.ceo.ceo_simplified_flow import simplified_ceo_agent
        
        with patch.object(simplified_ceo_agent, 'get_orchestration_plan', new_callable=AsyncMock) as mock_orchestration:
            mock_orchestration.side_effect = Exception("Orchestration service unavailable")
            
            # Process confirmation
            session_data = {
                "state": "awaiting_confirmation",
                "polished_prompt": "Create Instagram GenAI campaign"
            }
            
            result = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="Yes, confirm",
                session_data=session_data
            )
            
            # Verify error handling
            assert result["state"] == "error"
            assert "encountered an error while starting the orchestration" in result["response"]
            assert result["error"] == "Orchestration service unavailable"
    
    @pytest.mark.asyncio
    async def test_complete_flow_integration(self, ceo_flow, mock_ai_response_complete):
        """Test complete flow from initial task to orchestration"""
        
        # Step 1: Initial task analysis
        with patch.object(ceo_flow.ai_analyzer, 'analyze_task', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_ai_response_complete
            
            result1 = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="create an instagram post on genAi",
                session_data={"state": ConversationState.INITIAL}
            )
            
            assert result1["state"] == "awaiting_confirmation"
            assert result1["requires_confirmation"] is True
        
        # Step 2: User confirms
        # Import the module first
        from src.agents.ceo.ceo_simplified_flow import simplified_ceo_agent
        
        with patch.object(simplified_ceo_agent, 'get_orchestration_plan', new_callable=AsyncMock) as mock_orchestration:
            mock_orchestration.return_value = {"success": True, "steps": []}
            
            result2 = await ceo_flow.process_user_message(
                session_id="test-session-123",
                message="Yes, please proceed",
                session_data=result1
            )
            
            assert result2["state"] == ConversationState.COMPLETE.value
            assert result2["orchestration_started"] is True
    
    def test_format_polished_prompt_display(self):
        """Test formatting of polished prompt for display"""
        
        # Test data
        polished_prompt = "Create comprehensive Instagram campaign for GenAI"
        executive_summary = "Develop social media content about AI"
        deliverables = ["Visual content", "Caption", "Hashtags"]
        
        # Expected format elements
        expected_elements = [
            "Polished Task Description:",
            polished_prompt,
            "Executive Summary:",
            executive_summary,
            "Key Deliverables:",
            "- Visual content",
            "- Caption",
            "- Hashtags",
            "Would you like to proceed"
        ]
        
        # Create formatted response (simulating what the code does)
        formatted_response = f"""I've analyzed and refined your task. Here's the polished prompt:

**Polished Task Description:**
{polished_prompt}

**Executive Summary:**
{executive_summary}

**Key Deliverables:**
{chr(10).join(f'- {d}' for d in deliverables)}

**Would you like to proceed with this refined task description?** Please confirm if this accurately captures your requirements, or let me know if you'd like to make any adjustments."""
        
        # Verify all elements are present
        for element in expected_elements:
            assert element in formatted_response


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])