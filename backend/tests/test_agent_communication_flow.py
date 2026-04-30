"""Test cases for agent communication and data flow

This module tests the data flow between Content Writer, CEO agent, and Social Media Publisher,
ensuring the 'output' attribute is properly passed and used.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ceo_simplified_flow import SimplifiedCEOAgent, CEOFlowState
from agent_state_manager import AgentStateManager, state_manager
from content_writer_v2.main_agent import ContentWriterMainAgent
from social_media_publisher.main_agent import SocialMediaPublisherMainAgent


class TestAgentCommunicationFlow:
    """Test suite for agent communication and data flow"""
    
    @pytest.fixture
    def ceo_agent(self):
        """Create a CEO agent instance"""
        return SimplifiedCEOAgent()
    
    @pytest.fixture
    def state_manager_instance(self):
        """Create a fresh state manager instance"""
        return AgentStateManager(storage_path="./test_agent_states")
    
    @pytest.fixture
    def sample_content_writer_output(self):
        """Sample Content Writer output with Instagram caption"""
        return "🚀 Upskill with GenAI 🤖 Learn the latest in AI and machine learning 💻 to boost your career in IT 📈 From #AIforIT to #MachineLearningEngineer and #DataScience, stay ahead 📊 with #ArtificialIntelligence #ITprofessionals #TechTrends #Innovation #FutureOfWork #DigitalTransformation #GenAI #AIlearning #RoadmapToSuccess #CareerGrowth #ITcareers #EmergingTech #AIexpert #MLalgorithms #NLP #DeepLearning #BusinessIntelligence #DataAnalytics #ITsolutions #TechSkills #FutureTech #AIapplications #ITindustry 👉 Share your GenAI learning journey 📚 and tag a friend who needs to upskill 🤝 #GenAIcommunity #ITcommunity #LearnWithUs #AItraining #MachineLearningCourse #DataScienceCourse #ITcertifications #TechEducation #FutureReady #GenAIroadmap 💡 Get started with GenAI today 📊 and take your IT career to the next level 🚀 #GenAIlearning #ITprofessional #CareerAdvice #TechCareer #AIcareer #GenAIexpert 🤖"
    
    @pytest.fixture
    def sample_orchestration_plan(self):
        """Sample orchestration plan with Content Writer and Social Media Publisher"""
        return {
            "request_id": "test-request-123",
            "mode": "sequential",
            "steps": [
                {
                    "agent_id": "content_writer",
                    "agent_name": "Content Writer",
                    "instruction": "Write an Instagram post about GenAI for IT professionals",
                    "endpoint": "/api/agents/content_writer"
                },
                {
                    "agent_id": "social_publisher",
                    "agent_name": "Social Media Publisher",
                    "instruction": "Publish the Instagram post",
                    "endpoint": "/api/agents/social_publisher"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_content_writer_output_saved_to_state(self, state_manager_instance, sample_content_writer_output):
        """Test that Content Writer output is properly saved to state manager"""
        session_id = "test-session-123"
        agent_id = "content_writer"
        
        # Save Content Writer output
        state_id = state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id=agent_id,
            output=sample_content_writer_output,
            metadata={"agent_name": "Content Writer", "step_number": 1}
        )
        
        # Verify output was saved
        assert state_id is not None
        assert state_id.startswith(f"{session_id}_{agent_id}_")
        
        # Retrieve output
        retrieved_output = state_manager_instance.get_agent_output(session_id, agent_id)
        assert retrieved_output == sample_content_writer_output
    
    @pytest.mark.asyncio
    async def test_social_publisher_retrieves_content_from_state(self, state_manager_instance, sample_content_writer_output):
        """Test that Social Media Publisher can retrieve Content Writer output from state"""
        session_id = "test-session-456"
        
        # Save Content Writer output
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=sample_content_writer_output
        )
        
        # Retrieve as Social Media Publisher would
        content = state_manager_instance.get_agent_output(session_id, "content_writer")
        assert content == sample_content_writer_output
        assert "GenAI" in content
        assert "#ITprofessionals" in content
    
    @pytest.mark.asyncio
    async def test_ceo_agent_payload_preparation(self, ceo_agent, sample_content_writer_output):
        """Test CEO agent prepares correct payload for Social Media Publisher"""
        # Test payload for Content Writer (no previous output)
        cw_payload = ceo_agent.prepare_agent_request(
            agent_id="content_writer",
            instruction="Write an Instagram post about GenAI",
            previous_output=None,
            context={"polished_requirements": "GenAI post for IT professionals"}
        )
        
        assert cw_payload["task"] == "Write an Instagram post about GenAI"
        assert cw_payload["format"] == "structured"
        assert cw_payload["tone"] == "professional"
        
        # Test payload for Social Media Publisher (with previous output)
        sm_payload = ceo_agent.prepare_agent_request(
            agent_id="social_publisher",
            instruction="Publish the Instagram post",
            previous_output=sample_content_writer_output,
            context={"previous_agent": "Content Writer"}
        )
        
        assert sm_payload["task"] == "Publish the Instagram post"
        assert sm_payload["content"] == sample_content_writer_output
        assert sm_payload["caption"] == sample_content_writer_output
        assert sm_payload["platform"] == "instagram"
    
    @pytest.mark.asyncio
    async def test_end_to_end_content_flow(self, ceo_agent, state_manager_instance, sample_orchestration_plan):
        """Test end-to-end content flow from Content Writer to Social Media Publisher"""
        session_id = "test-session-789"
        
        # Mock the execute_agent method to simulate agent responses
        async def mock_execute_agent(agent_id, agent_name, endpoint, payload, session_id):
            if agent_id == "content_writer":
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "response": {
                        "output": "🚀 Exciting GenAI content for IT professionals! #GenAI #ITprofessionals #AI #MachineLearning",
                        "duration_ms": 1000
                    }
                }
            elif agent_id == "social_publisher":
                # Verify that content was passed correctly
                assert "content" in payload
                assert "caption" in payload
                assert "GenAI content" in payload["content"]
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "response": {
                        "output": "Successfully published to Instagram",
                        "post_id": "ig_12345",
                        "duration_ms": 500
                    }
                }
        
        # Replace state manager with test instance
        with patch('ceo_simplified_flow.state_manager', state_manager_instance):
            ceo_agent.execute_agent = mock_execute_agent
            
            # Execute the plan
            results = await ceo_agent.execute_plan_sequentially(
                orchestration_plan=sample_orchestration_plan,
                polished_requirements="Create GenAI post for IT professionals",
                session_id=session_id
            )
        
        # Verify results
        assert len(results) == 2
        assert results[0]["agent_id"] == "content_writer"
        assert results[0]["success"] is True
        assert "GenAI content" in results[0]["output"]
        
        assert results[1]["agent_id"] == "social_publisher"
        assert results[1]["success"] is True
        assert "Successfully published" in results[1]["output"]
        
        # Verify state was saved
        cw_output = state_manager_instance.get_agent_output(session_id, "content_writer")
        assert cw_output is not None
        assert "GenAI content" in cw_output
    
    @pytest.mark.asyncio
    async def test_social_publisher_uses_caption_parameter(self):
        """Test that Social Media Publisher uses caption parameter when provided"""
        publisher = SocialMediaPublisherMainAgent()
        
        # Mock the publish method to check what content is used
        published_content = None
        
        async def mock_publish_to_platform(*args, **kwargs):
            nonlocal published_content
            published_content = args[1]  # content is the second argument
            return {"success": True, "post_id": "test_123"}
        
        publisher._publish_to_platform = mock_publish_to_platform
        publisher._initialized = True
        
        # Test with caption parameter
        test_caption = "This is the actual content from Content Writer with #hashtags"
        result = await publisher.publish_content(
            content="Schedule and publish the post",  # instruction
            caption=test_caption,  # actual content
            request_id="test-req-123",
            platform="instagram"
        )
        
        # Verify the actual content was used, not the instruction
        assert published_content == test_caption
    
    def test_state_manager_logging(self, caplog, state_manager_instance, sample_content_writer_output):
        """Test that state manager produces proper debug logs"""
        import logging
        state_manager_instance.logger.setLevel(logging.DEBUG)
        
        session_id = "test-log-session"
        agent_id = "content_writer"
        
        # Save output
        with caplog.at_level(logging.DEBUG):
            state_manager_instance.save_agent_output(
                session_id=session_id,
                agent_id=agent_id,
                output=sample_content_writer_output
            )
        
        # Check logs
        assert "[STATE_DEBUG] Saved agent output" in caplog.text
        assert f"Session: {session_id}" in caplog.text
        assert f"Agent: {agent_id}" in caplog.text
        
        # Retrieve output
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            output = state_manager_instance.get_agent_output(session_id, agent_id)
        
        # Check retrieval logs
        assert "[STATE_DEBUG] Attempting to retrieve output" in caplog.text
        assert "[STATE_DEBUG] Retrieved agent output" in caplog.text
        assert output == sample_content_writer_output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
