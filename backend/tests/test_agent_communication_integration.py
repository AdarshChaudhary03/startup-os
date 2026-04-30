"""Integration tests for agent communication with state management"""

import pytest
import asyncio
import os
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_state_manager import state_manager
from ceo_simplified_flow import SimplifiedCEOAgent


class TestAgentCommunicationIntegration:
    """Integration tests for Content Writer and Social Media Publisher communication"""
    
    @pytest.fixture
    def ceo_agent(self):
        """Create a CEO agent instance for testing"""
        return SimplifiedCEOAgent()
    
    @pytest.fixture
    def session_id(self):
        """Generate a unique session ID for testing"""
        return f"test_session_{uuid.uuid4().hex[:8]}"
    
    @pytest.fixture(autouse=True)
    def cleanup_state(self, session_id):
        """Clean up state after each test"""
        yield
        # Clean up session state after test
        state_manager.clear_session_state(session_id)
    
    @pytest.mark.asyncio
    async def test_content_writer_saves_output(self, session_id):
        """Test that Content Writer saves its output to state manager"""
        # Simulate Content Writer agent execution
        agent_id = "content_writer"
        content_output = "🚀 Unlock the Power of GenAI this Summer! Join CodeXAI's exclusive training sessions designed for IT professionals. #GenAI #CodeXAI #TechTraining"
        
        # Save output as Content Writer would
        state_id = state_manager.save_agent_output(
            session_id=session_id,
            agent_id=agent_id,
            output=content_output,
            metadata={
                "agent_name": "Content Writer",
                "task": "Write Instagram post about GenAI",
                "platform": "instagram",
                "hashtags": ["#GenAI", "#CodeXAI", "#TechTraining"]
            }
        )
        
        # Verify output was saved
        assert state_id is not None
        
        # Retrieve and verify output
        retrieved_output = state_manager.get_agent_output(session_id, agent_id)
        assert retrieved_output == content_output
    
    @pytest.mark.asyncio
    async def test_social_publisher_retrieves_content(self, session_id):
        """Test that Social Media Publisher retrieves content from state manager"""
        # First, save Content Writer output
        content_writer_output = "🎯 Level up your AI skills with CodeXAI's GenAI Summer Training! Perfect for IT professionals ready to lead the AI revolution. #GenAI #AITraining #ITProfessionals"
        
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=content_writer_output,
            metadata={"platform": "instagram"}
        )
        
        # Simulate Social Media Publisher retrieving content
        retrieved_content = state_manager.get_agent_output(session_id, "content_writer")
        
        # Verify content was retrieved correctly
        assert retrieved_content == content_writer_output
        assert retrieved_content != "Schedule and publish the created Instagram post to maximize visibility and reach the target audience."
    
    @pytest.mark.asyncio
    async def test_sequential_agent_execution_with_state(self, ceo_agent, session_id):
        """Test sequential execution of agents with state management"""
        # Mock orchestration plan
        orchestration_plan = {
            "mode": "sequential",
            "steps": [
                {
                    "agent_id": "content_writer",
                    "agent_name": "Content Writer",
                    "instruction": "Write an engaging Instagram post about GenAI trainings",
                    "endpoint": "/api/agents/content_writer"
                },
                {
                    "agent_id": "social_publisher",
                    "agent_name": "Social Media Publisher",
                    "instruction": "Publish the content to Instagram",
                    "endpoint": "/api/agents/social_publisher"
                }
            ]
        }
        
        # Mock agent responses
        content_writer_response = {
            "success": True,
            "response": {
                "output": "✨ Transform your career with GenAI! CodeXAI's summer training is here for IT professionals. Don't miss out! #GenAI #CodeXAI #CareerGrowth",
                "duration_ms": 1500
            }
        }
        
        social_publisher_response = {
            "success": True,
            "response": {
                "output": "Successfully published to Instagram with post ID: ig_test_12345",
                "post_id": "ig_test_12345",
                "duration_ms": 2000
            }
        }
        
        # Mock execute_agent method
        async def mock_execute_agent(agent_id, agent_name, endpoint, payload, session_id):
            if agent_id == "content_writer":
                # Save Content Writer output to state
                state_manager.save_agent_output(
                    session_id=session_id,
                    agent_id=agent_id,
                    output=content_writer_response["response"]["output"],
                    metadata={"agent_name": agent_name}
                )
                return content_writer_response
            elif agent_id == "social_publisher":
                # Verify Social Publisher receives correct content
                assert "content" in payload or "caption" in payload
                if "content" in payload:
                    # Should receive actual content, not instruction
                    assert payload["content"] != "Publish the content to Instagram"
                    assert "GenAI" in payload["content"]
                return social_publisher_response
            return {"success": False, "error": "Unknown agent"}
        
        # Patch execute_agent method
        with patch.object(ceo_agent, 'execute_agent', side_effect=mock_execute_agent):
            # Execute plan
            results = await ceo_agent.execute_plan_sequentially(
                orchestration_plan=orchestration_plan,
                polished_requirements="Create and publish Instagram post about GenAI",
                session_id=session_id
            )
        
        # Verify results
        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is True
        
        # Verify state was saved
        content_writer_output = state_manager.get_agent_output(session_id, "content_writer")
        assert content_writer_output == content_writer_response["response"]["output"]
    
    @pytest.mark.asyncio
    async def test_social_publisher_uses_state_content(self, session_id):
        """Test that Social Media Publisher uses content from state instead of instruction"""
        # Save Content Writer output
        actual_content = "🔥 Ready to master GenAI? Join CodeXAI's intensive summer training program designed exclusively for IT professionals! Limited seats available. #GenAI #CodeXAI #SummerTraining #ITSkills"
        
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=actual_content,
            metadata={
                "platform": "instagram",
                "hashtags": ["#GenAI", "#CodeXAI", "#SummerTraining", "#ITSkills"]
            }
        )
        
        # Simulate Social Media Publisher logic
        # This mimics what happens in the actual Social Media Publisher
        instruction = "Schedule and publish the created Instagram post to maximize visibility"
        
        # Check if we have content from previous agent
        content_from_state = state_manager.get_agent_output(session_id, "content_writer")
        
        # Use content from state if available, otherwise fall back to instruction
        final_content = content_from_state if content_from_state else instruction
        
        # Verify correct content is used
        assert final_content == actual_content
        assert final_content != instruction
        assert "GenAI" in final_content
        assert "CodeXAI" in final_content
    
    def test_state_persistence_between_agents(self, session_id):
        """Test that state persists correctly between agent executions"""
        # Agent 1: Content Writer
        content_output = "📚 GenAI Training Alert! CodeXAI brings you cutting-edge AI education this summer. Perfect for IT professionals looking to stay ahead. Register now! #GenAI #AIEducation #CodeXAI"
        
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=content_output,
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "word_count": len(content_output.split())
            }
        )
        
        # Agent 2: Hashtag Optimizer (hypothetical)
        hashtag_output = ["#GenAI", "#AIEducation", "#CodeXAI", "#SummerTraining", "#ITProfessionals"]
        
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="hashtag_optimizer",
            output=hashtag_output,
            metadata={"count": len(hashtag_output)}
        )
        
        # Agent 3: Social Publisher retrieves both
        content = state_manager.get_agent_output(session_id, "content_writer")
        hashtags = state_manager.get_agent_output(session_id, "hashtag_optimizer")
        
        # Verify both outputs are available
        assert content == content_output
        assert hashtags == hashtag_output
        
        # Get session summary
        summary = state_manager.get_session_summary(session_id)
        assert summary["total_agents"] == 2
        assert "content_writer" in summary["agents"]
        assert "hashtag_optimizer" in summary["agents"]
    
    def test_error_handling_missing_content(self, session_id):
        """Test handling when no content is available in state"""
        # Try to get content that doesn't exist
        missing_content = state_manager.get_agent_output(session_id, "content_writer")
        
        # Should return None
        assert missing_content is None
        
        # Social Publisher should handle this gracefully
        # In real implementation, it would use instruction as fallback
        fallback_content = missing_content or "Default instruction text"
        assert fallback_content == "Default instruction text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
