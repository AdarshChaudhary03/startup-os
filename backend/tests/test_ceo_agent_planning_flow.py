import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import uuid

from ceo_conversation_flow import ceo_conversation_flow
from ceo_agent_planner import ceo_agent_planner
from ceo_chat_interface import ceo_chat_interface, ChatSessionState


class TestCEOAgentPlanningFlow:
    """Test suite for CEO agent planning flow integration"""
    
    @pytest.fixture
    def sample_session_data(self):
        """Create sample session data for testing"""
        return {
            "session_id": "test-session-123",
            "request_id": str(uuid.uuid4()),
            "original_task": "Create a blog post about AI trends",
            "state": ChatSessionState.COMPLETE,
            "responses": {
                "purpose": "Create an informative blog post about current AI trends for tech professionals",
                "audience": "Tech professionals and AI enthusiasts",
                "scope": "Cover machine learning, NLP, and computer vision trends",
                "timeline": "Within 2 weeks",
                "constraints": "Keep it under 2000 words, include real examples"
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    @pytest.fixture
    def sample_requirements(self):
        """Create sample requirements for testing"""
        return {
            "purpose": "Create an informative blog post about current AI trends for tech professionals",
            "target_audience": "Tech professionals and AI enthusiasts",
            "scope": {
                "included": "Cover machine learning, NLP, and computer vision trends",
                "excluded": "None specified"
            },
            "constraints": "Keep it under 2000 words, include real examples",
            "timeline": "Within 2 weeks",
            "success_criteria": ["Completed implementation as per requirements"],
            "priority": "normal",
            "estimated_complexity": "medium"
        }
    
    @pytest.mark.asyncio
    async def test_finalize_requirements_success(self, sample_session_data, sample_requirements):
        """Test successful finalization of requirements with agent planning"""
        request_id = str(uuid.uuid4())
        
        # Mock the agent planner response
        mock_agent_plan = {
            "success": True,
            "plan": {
                "plan_id": "plan-123",
                "workflow_type": "sequential",
                "total_steps": 2,
                "steps": [
                    {
                        "step_number": 1,
                        "agent_id": "content_writer",
                        "agent_name": "Content Writer Agent",
                        "instructions": "Create blog post about AI trends"
                    },
                    {
                        "step_number": 2,
                        "agent_id": "social_media_publisher",
                        "agent_name": "Social Media Publisher Agent",
                        "instructions": "Publish blog post on social media"
                    }
                ]
            },
            "selected_agents": ["content_writer", "social_media_publisher"],
            "confidence_score": 0.85
        }
        
        with patch.object(ceo_agent_planner, 'create_agent_plan', new_callable=AsyncMock) as mock_create_plan:
            mock_create_plan.return_value = mock_agent_plan
            
            # Call finalize_requirements
            result = await ceo_conversation_flow.finalize_requirements(
                session_id="test-session-123",
                session_data=sample_session_data,
                request_id=request_id
            )
            
            # Verify the result
            assert result["success"] == True
            assert "requirements" in result
            assert "plan" in result
            assert "agent_plan" in result
            assert result["agent_plan"]["success"] == True
            assert len(result["agent_plan"]["plan"]["steps"]) == 2
            
            # Verify agent planner was called with correct parameters
            mock_create_plan.assert_called_once()
            call_args = mock_create_plan.call_args[1]
            assert call_args["request_id"] == request_id
            assert "polished_task" in call_args["requirements"]
            assert "objective" in call_args["requirements"]
    
    @pytest.mark.asyncio
    async def test_finalize_requirements_agent_planner_failure(self, sample_session_data):
        """Test handling of agent planner failure"""
        request_id = str(uuid.uuid4())
        
        # Mock agent planner to raise an exception
        with patch.object(ceo_agent_planner, 'create_agent_plan', new_callable=AsyncMock) as mock_create_plan:
            mock_create_plan.side_effect = Exception("Agent planner service unavailable")
            
            # Call finalize_requirements
            result = await ceo_conversation_flow.finalize_requirements(
                session_id="test-session-123",
                session_data=sample_session_data,
                request_id=request_id
            )
            
            # Verify graceful failure handling
            assert result["success"] == False
            assert "agent_plan" in result
            assert result["agent_plan"]["success"] == False
            assert "error" in result["agent_plan"]
            assert "Agent planner service unavailable" in result["agent_plan"]["error"]
            assert "fallback_plan" in result["agent_plan"]
    
    @pytest.mark.asyncio
    async def test_extract_deliverables_from_requirements(self):
        """Test deliverables extraction from requirements"""
        # Test with scope included
        requirements = {
            "scope": {"included": "Blog post, Social media content, Newsletter"},
            "purpose": "Create content for marketing campaign"
        }
        deliverables = ceo_conversation_flow._extract_deliverables_from_requirements(requirements)
        assert len(deliverables) == 4  # 3 from scope + 1 from purpose
        assert "Blog post" in deliverables
        assert "Social media content" in deliverables
        assert "Newsletter" in deliverables
        
        # Test with create/build in purpose
        requirements = {
            "purpose": "Build a new feature for the application"
        }
        deliverables = ceo_conversation_flow._extract_deliverables_from_requirements(requirements)
        assert "Completed implementation as per requirements" in deliverables
        
        # Test with no specific deliverables
        requirements = {"purpose": "Review existing code"}
        deliverables = ceo_conversation_flow._extract_deliverables_from_requirements(requirements)
        assert "Complete the requested task as specified" in deliverables
    
    @pytest.mark.asyncio
    async def test_end_to_end_chat_to_plan_flow(self, sample_session_data):
        """Test complete flow from chat finalization to agent plan creation"""
        request_id = str(uuid.uuid4())
        session_id = "test-session-456"
        
        # Setup session in chat interface
        ceo_chat_interface.active_sessions[session_id] = sample_session_data
        
        # Mock agent planner
        mock_agent_plan = {
            "success": True,
            "plan": {
                "plan_id": "plan-456",
                "workflow_type": "sequential",
                "total_steps": 1,
                "steps": [
                    {
                        "step_number": 1,
                        "agent_id": "content_writer",
                        "agent_name": "Content Writer Agent"
                    }
                ]
            }
        }
        
        with patch.object(ceo_agent_planner, 'create_agent_plan', new_callable=AsyncMock) as mock_create_plan:
            mock_create_plan.return_value = mock_agent_plan
            
            # Simulate the finalize endpoint call
            from ceo_chat_message_routes import finalize_requirements
            from fastapi import Request
            
            # Create mock request
            mock_request = Mock(spec=Request)
            mock_request.state = Mock()
            mock_request.state.request_id = request_id
            
            # Call the endpoint
            response = await finalize_requirements(session_id, mock_request)
            
            # Verify response
            assert response["success"] == True
            assert response["conversation_id"] == session_id
            assert "requirements" in response
            assert "plan" in response
            assert "agent_plan" in response
            assert response["agent_plan"]["success"] == True
    
    def test_agent_planner_keyword_analysis(self):
        """Test agent planner's keyword-based analysis fallback"""
        # Test content creation detection
        analysis = ceo_agent_planner._keyword_based_analysis(
            "Write a blog post",
            "Create engaging content",
            ["Blog post", "Social media posts"]
        )
        assert "content_writer" in analysis["required_agents"]
        assert "social_media_publisher" in analysis["required_agents"]
        assert analysis["primary_domain"] == "content"
        
        # Test engineering task detection
        analysis = ceo_agent_planner._keyword_based_analysis(
            "Develop and test new feature",
            "Create unit tests and ensure code quality",
            ["Tested code", "PR with review"]
        )
        assert "unit_test" in analysis["required_agents"]
        assert "pr_agent" in analysis["required_agents"]
        assert analysis["primary_domain"] == "engineering"
    
    @pytest.mark.asyncio
    async def test_agent_plan_validation(self):
        """Test agent plan validation"""
        # Valid plan
        valid_plan = {
            "plan_id": "test-plan-123",
            "workflow_type": "sequential",
            "steps": [
                {
                    "agent_id": "content_writer",
                    "instructions": "Write content",
                    "endpoint": "/api/agents/content-writer"
                }
            ]
        }
        is_valid, issues = ceo_agent_planner.validate_plan(valid_plan)
        assert is_valid == True
        assert len(issues) == 0
        
        # Invalid plan - missing required fields
        invalid_plan = {
            "workflow_type": "sequential",
            "steps": []
        }
        is_valid, issues = ceo_agent_planner.validate_plan(invalid_plan)
        assert is_valid == False
        assert "Missing required field: plan_id" in issues
        assert "Plan has no steps" in issues
        
        # Invalid plan - unknown agent
        invalid_plan = {
            "plan_id": "test-plan-456",
            "workflow_type": "sequential",
            "steps": [
                {
                    "agent_id": "unknown_agent",
                    "instructions": "Do something",
                    "endpoint": "/api/agents/unknown"
                }
            ]
        }
        is_valid, issues = ceo_agent_planner.validate_plan(invalid_plan)
        assert is_valid == False
        assert "Unknown agent: unknown_agent" in issues


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-v", __file__])