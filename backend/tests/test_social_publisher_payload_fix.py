"""Test cases for social_publisher payload formatting fix.

This test suite verifies that social_publisher correctly receives and processes
content from content_writer through proper payload formatting.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Mock the necessary modules
import sys
sys.path.append('..')


class TestSocialPublisherPayloadFix:
    """Test suite for social_publisher payload formatting fix."""
    
    @pytest.fixture
    def sample_content_writer_output(self):
        """Sample content writer output with caption and hashtags."""
        return (
            "🤖💻 Discover the power of GenAI 🚀\n"
            "for students like you! 📚\n"
            "Learn how to harness AI tools 🛠️\n"
            "to boost your productivity 📊\n"
            "and creativity 🎨. From #AIforStudents \n"
            "to #GenAI, #ArtificialIntelligence, \n"
            "#MachineLearning, #DeepLearning, \n"
            "#NaturalLanguageProcessing, \n"
            "#Automation, #Robotics, \n"
            "#DataScience, #Python, #Coding, \n"
            "#FutureOfWork, #Innovation, \n"
            "#TechForGood, #EdTech, #Elearning, \n"
            "#OnlineEducation, #StudentLife, \n"
            "#AcademicSuccess, #InnovationNation, \n"
            "#FutureOfEducation, #TechSavvy, \n"
            "#DigitalLiteracy, #GenAIforGood, \n"
            "#AIethics, #ResponsibleAI, \n"
            "#StudentInnovation, #EdTechTools, \n"
            "#LearningWithAI, share your thoughts 🤔\n"
            "on how GenAI will impact your studies 📝\n"
            "and tag a friend who's interested 📚\n"
            "#GenAIcommunity #AIforgood 🚀\n"
            "Join the conversation now 🗣️\n"
            "and let's shape the future together 🤝! 💬"
        )
    
    @pytest.fixture
    def frontend_payload_with_context(self, sample_content_writer_output):
        """Frontend payload with context object (not stringified)."""
        return {
            "task": "Schedule and publish the caption on Instagram.",
            "context": {
                "content_writer_output": sample_content_writer_output,
                "caption": sample_content_writer_output,
                "metadata": {
                    "content_generated_at": "2026-04-30T08:09:52.870104+00:00",
                    "session_id": "session-1777533420715-ygafy0x8i"
                }
            },
            "caption": sample_content_writer_output,
            "content": sample_content_writer_output,
            "metadata": {
                "step_number": 2,
                "total_steps": 2,
                "session_id": "session-1777533420715-ygafy0x8i"
            }
        }
    
    @pytest.fixture
    def backend_request_body(self, sample_content_writer_output):
        """Backend request body that social_publisher should receive."""
        return {
            "task": "Schedule and publish the caption on Instagram.",
            "context": {
                "content_writer_output": sample_content_writer_output,
                "caption": sample_content_writer_output,
                "metadata": {
                    "content_generated_at": "2026-04-30T08:09:52.870104+00:00",
                    "session_id": "session-1777533420715-ygafy0x8i"
                }
            },
            "caption": sample_content_writer_output,
            "content": sample_content_writer_output
        }
    
    @pytest.mark.asyncio
    async def test_frontend_payload_not_stringified(self, frontend_payload_with_context):
        """Test that frontend doesn't stringify context for social_publisher."""
        # Verify context is an object, not a string
        assert isinstance(frontend_payload_with_context['context'], dict)
        assert 'content_writer_output' in frontend_payload_with_context['context']
        assert 'caption' in frontend_payload_with_context['context']
        
        # Verify caption and content are directly in payload
        assert 'caption' in frontend_payload_with_context
        assert 'content' in frontend_payload_with_context
        assert frontend_payload_with_context['caption'] == frontend_payload_with_context['context']['caption']
    
    @pytest.mark.asyncio
    async def test_agent_routes_passes_full_request(self):
        """Test that agent_routes passes full request body to social_publisher."""
        from agent_routes import execute_agent
        from models import AgentExecutionRequest
        
        # Mock request
        mock_request = Mock()
        mock_request.state.request_id = "test-request-id"
        mock_request.headers = {
            'X-Session-ID': 'session-1777533420715-ygafy0x8i'
        }
        
        # Create request with caption and content
        req = AgentExecutionRequest(
            task="Schedule and publish the caption on Instagram.",
            caption="Test caption content",
            content="Test content",
            context={"content_writer_output": "Test caption content"}
        )
        
        # Mock execute_agent_real to verify it receives full request
        with patch('utils.execute_agent_real', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "Success"
            
            # Execute for social_publisher
            await execute_agent("social_publisher", req, mock_request)
            
            # Verify execute_agent_real was called with full request dict
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0]
            
            # Should pass dict for social_publisher, not just task string
            assert call_args[0] == "social_publisher"
            assert isinstance(call_args[1], dict)
            assert 'caption' in call_args[1]
            assert 'content' in call_args[1]
            assert 'context' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_social_publisher_extracts_caption(self, backend_request_body, sample_content_writer_output):
        """Test that social_publisher correctly extracts caption from request."""
        from social_media_publisher.main_agent import SocialMediaPublisherMainAgent
        
        # Create agent instance
        agent = SocialMediaPublisherMainAgent()
        
        # Mock the AI provider
        with patch.object(agent, '_initialized', True):
            with patch.object(agent, '_publish_to_platform', new_callable=AsyncMock) as mock_publish:
                mock_publish.return_value = {
                    "success": True,
                    "platform": "instagram",
                    "post_id": "test-post-123"
                }
                
                # Call publish_content with the request body as task
                result = await agent.publish_content(
                    content="",  # Empty content to test extraction
                    request_id="test-request-id",
                    platform="instagram",
                    task=backend_request_body,  # Pass full request as task
                    session_id="session-1777533420715-ygafy0x8i"
                )
                
                # Verify the platform was called with correct content
                mock_publish.assert_called_once()
                call_args = mock_publish.call_args[0]
                
                # Should use the actual caption content, not the instruction
                published_content = call_args[1]
                assert published_content == sample_content_writer_output
                assert "Discover the power of GenAI" in published_content
                assert "Schedule and publish" not in published_content
    
    @pytest.mark.asyncio
    async def test_ceo_simplified_flow_content_passing(self, sample_content_writer_output):
        """Test that CEO simplified flow passes content correctly to social_publisher."""
        from ceo_simplified_flow import CEOSimplifiedFlow
        
        flow = CEOSimplifiedFlow()
        
        # Test prepare_agent_request for social_publisher
        payload = flow.prepare_agent_request(
            agent_id="social_publisher",
            instruction="Schedule and publish the written Instagram post.",
            previous_output=sample_content_writer_output,
            context={
                "previous_agent": "content_writer",
                "step_number": 2,
                "total_steps": 2
            }
        )
        
        # Verify payload has caption and content from previous output
        assert 'caption' in payload
        assert 'content' in payload
        assert payload['caption'] == sample_content_writer_output
        assert payload['content'] == sample_content_writer_output
        assert "Schedule and publish" not in payload['caption']
        assert "Discover the power of GenAI" in payload['caption']
    
    @pytest.mark.asyncio
    async def test_instagram_agent_uses_correct_caption(self, sample_content_writer_output):
        """Test that Instagram sub-agent uses the provided caption."""
        from social_media_publisher.sub_agents.instagram import InstagramAgent
        from social_media_publisher.config import SocialMediaPublisherConfig, InstagramConfig
        
        # Create Instagram agent
        config = SocialMediaPublisherConfig()
        instagram_config = InstagramConfig()
        agent = InstagramAgent(config, instagram_config)
        
        # Mock the Instagram API calls
        with patch.object(agent, '_publish_via_instagram_graph_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "success": True,
                "post_id": "ig_test_123",
                "platform": "instagram"
            }
            
            # Publish with the caption
            result = await agent.publish(
                content=sample_content_writer_output,
                request_id="test-request-id"
            )
            
            # Verify API was called with correct caption
            mock_api.assert_called_once()
            call_args = mock_api.call_args[0]
            post_data = call_args[0]
            
            assert 'content' in post_data
            assert post_data['content'] == sample_content_writer_output
            assert "Discover the power of GenAI" in post_data['content']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
