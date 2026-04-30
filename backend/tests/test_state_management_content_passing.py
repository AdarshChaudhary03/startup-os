"""Test State Management Content Passing Between Agents

This test verifies that Content Writer outputs are properly saved to state manager
and Social Media Publisher can retrieve the actual generated captions.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_state_manager import state_manager
from utils import execute_agent_real


class TestStateManagementContentPassing:
    """Test suite for state management content passing functionality."""
    
    @pytest.fixture
    def session_id(self):
        """Generate a unique session ID for tests."""
        return f"test_session_{datetime.now(timezone.utc).timestamp()}"
    
    @pytest.fixture
    def cleanup_state(self, session_id):
        """Cleanup state after tests."""
        yield
        # Cleanup after test
        state_manager.clear_session_state(session_id)
    
    @pytest.mark.asyncio
    async def test_content_writer_saves_actual_content(self, session_id, cleanup_state):
        """Test that Content Writer saves actual generated content to state manager."""
        # Test task for Content Writer
        task = "Write an Instagram post about GenAI learning and roadmap for IT professionals"
        request_id = f"test_req_{datetime.now(timezone.utc).timestamp()}"
        
        # Execute Content Writer
        output = await execute_agent_real("content_writer", task, request_id)
        
        # Save to state manager (simulating what agent_routes does)
        # Check if output is JSON and extract content
        output_to_save = output
        try:
            parsed_output = json.loads(output) if isinstance(output, str) else output
            if isinstance(parsed_output, dict) and "content" in parsed_output:
                output_to_save = parsed_output["content"]
        except:
            pass
        
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=output_to_save,
            metadata={"task": task, "request_id": request_id}
        )
        
        # Retrieve from state manager
        retrieved_output = state_manager.get_agent_output(session_id, "content_writer")
        
        # Assertions
        assert retrieved_output is not None, "Content Writer output should be saved"
        assert isinstance(retrieved_output, str), "Retrieved output should be a string"
        assert len(retrieved_output) > 50, "Content should be substantial"
        assert "#" in retrieved_output or "GenAI" in retrieved_output, "Content should be relevant"
        print(f"✓ Content Writer saved actual content: {retrieved_output[:200]}...")
    
    @pytest.mark.asyncio
    async def test_social_media_publisher_retrieves_content(self, session_id, cleanup_state):
        """Test that Social Media Publisher retrieves content from state manager."""
        # First, save some test content as if Content Writer generated it
        test_caption = "🚀 Upskill with GenAI 🤖 Learn the latest in AI and machine learning 💻 #AIforIT #MachineLearningEngineer #DataScience #GenAI #ITprofessionals"
        
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=test_caption,
            metadata={"task": "Generate Instagram caption", "request_id": "test_123"}
        )
        
        # Retrieve as Social Media Publisher would
        content_writer_output = state_manager.get_agent_output(session_id, "content_writer")
        
        # Assertions
        assert content_writer_output is not None, "Should retrieve Content Writer output"
        assert content_writer_output == test_caption, "Should retrieve exact content"
        assert "#AIforIT" in content_writer_output, "Should contain hashtags"
        assert "🚀" in content_writer_output, "Should contain emojis"
        print(f"✓ Social Media Publisher retrieved content: {content_writer_output[:100]}...")
    
    @pytest.mark.asyncio
    async def test_previous_agent_output_retrieval(self, session_id, cleanup_state):
        """Test retrieving previous agent output in a chain."""
        # Save outputs from multiple agents
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output="Generated Instagram caption with hashtags",
            metadata={"step": 1}
        )
        
        await asyncio.sleep(0.1)  # Ensure different timestamps
        
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="qa_tester",
            output="Content validated successfully",
            metadata={"step": 2}
        )
        
        # Get previous output for social_publisher
        previous_output = state_manager.get_previous_agent_output(
            session_id=session_id,
            current_agent_id="social_publisher"
        )
        
        # Should get the most recent output (qa_tester)
        assert previous_output == "Content validated successfully"
        
        # Get specific previous agent output
        content_writer_output = state_manager.get_previous_agent_output(
            session_id=session_id,
            current_agent_id="social_publisher",
            previous_agent_id="content_writer"
        )
        
        assert content_writer_output == "Generated Instagram caption with hashtags"
        print("✓ Previous agent output retrieval works correctly")
    
    @pytest.mark.asyncio
    async def test_session_summary(self, session_id, cleanup_state):
        """Test session summary functionality."""
        # Save outputs from multiple agents
        agents = [
            ("content_writer", "Instagram post about GenAI"),
            ("social_publisher", "Published to Instagram successfully")
        ]
        
        for agent_id, output in agents:
            state_manager.save_agent_output(
                session_id=session_id,
                agent_id=agent_id,
                output=output,
                metadata={"test": True}
            )
        
        # Get session summary
        summary = state_manager.get_session_summary(session_id)
        
        # Assertions
        assert summary["session_id"] == session_id
        assert summary["total_agents"] == 2
        assert "content_writer" in summary["agents"]
        assert "social_publisher" in summary["agents"]
        assert len(summary["states"]) == 2
        print(f"✓ Session summary: {summary}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
