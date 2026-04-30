"""Test cases for Social Media Publisher 422 error fix.

This test suite verifies that the social media publisher correctly handles
various payload formats and extracts content properly.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import AgentExecutionRequest, AgentExecutionResponse
from utils import execute_agent_real
from agent_state_manager import state_manager


class TestSocialPublisher422Fix:
    """Test cases for social media publisher 422 error fix."""
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return "🤖 Discover the power of AI with GenAI 🚀\nfor students like you 📚. \n\nLearn to code, \nbuild projects, \nand innovate 🌟 with \n#GenAI #AIforStudents #ArtificialIntelligence"
    
    @pytest.fixture
    def mock_social_publisher(self):
        """Mock social media publisher."""
        with patch('utils.SocialMediaPublisherMainAgent') as mock_agent:
            mock_instance = AsyncMock()
            mock_instance.initialize = AsyncMock()
            mock_instance.publish_content = AsyncMock(return_value={
                "success": True,
                "platforms_published": ["instagram"],
                "post_id": "test_post_123",
                "url": "https://instagram.com/p/test_post_123"
            })
            mock_agent.return_value = mock_instance
            yield mock_instance
    
    @pytest.mark.asyncio
    async def test_extract_content_from_caption_field(self, sample_content, mock_social_publisher):
        """Test extracting content from caption field."""
        # Test data with caption field
        task_data = {
            "task": "Schedule and publish the caption on Instagram.",
            "caption": sample_content,
            "content": "Schedule and publish the caption on Instagram.",
            "context": {
                "content_writer_output": sample_content,
                "metadata": {"session_id": "test-session-123"}
            },
            "metadata": {"session_id": "test-session-123"}
        }
        
        # Execute agent
        result = await execute_agent_real("social_publisher", task_data, "test-request-123")
        
        # Verify the correct content was passed to publish_content
        mock_social_publisher.publish_content.assert_called_once()
        call_args = mock_social_publisher.publish_content.call_args
        
        # Check that the actual content (not instruction) was used
        assert call_args.kwargs['content'] == sample_content
        assert call_args.kwargs['caption'] == sample_content
        assert "Schedule and publish" not in call_args.kwargs['content']
    
    @pytest.mark.asyncio
    async def test_extract_content_from_context(self, sample_content, mock_social_publisher):
        """Test extracting content from context when caption is missing."""
        # Test data without caption field
        task_data = {
            "task": "Schedule and publish the caption on Instagram.",
            "context": {
                "content_writer_output": sample_content,
                "caption": sample_content,
                "metadata": {"content_generated_at": "2024-01-01T00:00:00Z"}
            },
            "metadata": {"session_id": "test-session-456"}
        }
        
        # Execute agent
        result = await execute_agent_real("social_publisher", task_data, "test-request-456")
        
        # Verify the correct content was extracted from context
        mock_social_publisher.publish_content.assert_called_once()
        call_args = mock_social_publisher.publish_content.call_args
        
        assert call_args.kwargs['content'] == sample_content
        assert "Schedule and publish" not in call_args.kwargs['content']
    
    @pytest.mark.asyncio
    async def test_extract_content_from_state_manager(self, sample_content, mock_social_publisher):
        """Test extracting content from state manager when only instruction is provided."""
        # Store content in state manager
        session_id = "test-session-789"
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=sample_content,
            metadata={"generated_at": "2024-01-01T00:00:00Z"}
        )
        
        # Test data with only instruction
        task_data = {
            "task": "Schedule and publish the caption on Instagram.",
            "session_id": session_id,
            "metadata": {"session_id": session_id}
        }
        
        # Execute agent
        result = await execute_agent_real("social_publisher", task_data, "test-request-789")
        
        # Verify content was retrieved from state manager
        mock_social_publisher.publish_content.assert_called_once()
        call_args = mock_social_publisher.publish_content.call_args
        
        assert call_args.kwargs['content'] == sample_content
        assert call_args.kwargs['session_id'] == session_id
    
    @pytest.mark.asyncio
    async def test_handle_json_string_context(self, sample_content, mock_social_publisher):
        """Test handling context as JSON string."""
        # Test data with context as JSON string
        context_dict = {
            "content_writer_output": sample_content,
            "caption": sample_content
        }
        
        task_data = {
            "task": "Schedule and publish the caption on Instagram.",
            "context": json.dumps(context_dict),
            "metadata": {"session_id": "test-session-json"}
        }
        
        # Execute agent
        result = await execute_agent_real("social_publisher", task_data, "test-request-json")
        
        # Verify content was extracted from JSON string context
        mock_social_publisher.publish_content.assert_called_once()
        call_args = mock_social_publisher.publish_content.call_args
        
        assert call_args.kwargs['content'] == sample_content
    
    @pytest.mark.asyncio
    async def test_validation_with_proper_payload(self, sample_content):
        """Test that proper payload passes validation."""
        # Create request with all fields
        request = AgentExecutionRequest(
            task="Schedule and publish the caption on Instagram.",
            caption=sample_content,
            content=sample_content,
            context={
                "content_writer_output": sample_content,
                "metadata": {"session_id": "test-validation"}
            },
            metadata={"session_id": "test-validation"}
        )
        
        # Verify model validation passes
        assert request.task == "Schedule and publish the caption on Instagram."
        assert request.caption == sample_content
        assert request.content == sample_content
        assert isinstance(request.context, dict)
        assert request.context["content_writer_output"] == sample_content
    
    @pytest.mark.asyncio
    async def test_fallback_to_task_when_no_content(self, mock_social_publisher):
        """Test fallback to task field when no content is available."""
        # Test data with actual content in task field
        actual_content = "This is the actual content to publish on social media #test"
        
        task_data = {
            "task": actual_content,
            "metadata": {"session_id": "test-fallback"}
        }
        
        # Execute agent
        result = await execute_agent_real("social_publisher", task_data, "test-request-fallback")
        
        # Verify task content was used
        mock_social_publisher.publish_content.assert_called_once()
        call_args = mock_social_publisher.publish_content.call_args
        
        assert call_args.kwargs['content'] == actual_content


def test_agent_execution_request_model_validation():
    """Test AgentExecutionRequest model validation."""
    # Test with minimal required fields
    request = AgentExecutionRequest(task="Test task")
    assert request.task == "Test task"
    assert request.context is None
    assert request.metadata is None
    assert request.caption is None
    assert request.content is None
    
    # Test with all fields
    request_full = AgentExecutionRequest(
        task="Test task",
        context={"key": "value"},
        metadata={"session_id": "123"},
        caption="Test caption",
        content="Test content"
    )
    assert request_full.task == "Test task"
    assert request_full.context == {"key": "value"}
    assert request_full.metadata == {"session_id": "123"}
    assert request_full.caption == "Test caption"
    assert request_full.content == "Test content"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])