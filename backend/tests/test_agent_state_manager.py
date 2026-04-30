"""Unit tests for Agent State Management System"""

import pytest
import os
import json
import shutil
from datetime import datetime, timezone
import asyncio
from unittest.mock import patch, MagicMock

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_state_manager import (
    AgentStateManager,
    StateType,
    state_manager,
    save_agent_output_async,
    get_agent_output_async,
    get_previous_agent_output_async
)


class TestAgentStateManager:
    """Test cases for AgentStateManager"""
    
    @pytest.fixture
    def test_storage_path(self, tmp_path):
        """Create a temporary storage path for testing"""
        return str(tmp_path / "test_agent_states")
    
    @pytest.fixture
    def state_manager_instance(self, test_storage_path):
        """Create a test instance of AgentStateManager"""
        return AgentStateManager(storage_path=test_storage_path)
    
    def test_initialization(self, state_manager_instance, test_storage_path):
        """Test state manager initialization"""
        assert state_manager_instance.storage_path == test_storage_path
        assert os.path.exists(test_storage_path)
        assert state_manager_instance._state_cache == {}
    
    def test_save_agent_output(self, state_manager_instance):
        """Test saving agent output"""
        session_id = "test_session_123"
        agent_id = "content_writer"
        output = "This is the generated content for Instagram post about GenAI."
        metadata = {"word_count": 15, "platform": "instagram"}
        
        # Save output
        state_id = state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id=agent_id,
            output=output,
            metadata=metadata
        )
        
        # Verify state_id format
        assert state_id.startswith(f"{session_id}_{agent_id}_")
        
        # Verify cache update
        assert session_id in state_manager_instance._state_cache
        assert agent_id in state_manager_instance._state_cache[session_id]
        
        # Verify saved data
        saved_data = state_manager_instance._state_cache[session_id][agent_id]
        assert saved_data["output"] == output
        assert saved_data["metadata"] == metadata
        assert saved_data["state_type"] == StateType.AGENT_OUTPUT.value
    
    def test_get_agent_output(self, state_manager_instance):
        """Test retrieving agent output"""
        session_id = "test_session_456"
        agent_id = "content_writer"
        output = "Generated Instagram content with hashtags"
        
        # Save output
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id=agent_id,
            output=output
        )
        
        # Retrieve output
        retrieved_output = state_manager_instance.get_agent_output(
            session_id=session_id,
            agent_id=agent_id
        )
        
        assert retrieved_output == output
    
    def test_get_agent_output_with_metadata(self, state_manager_instance):
        """Test retrieving agent output with metadata"""
        session_id = "test_session_789"
        agent_id = "social_publisher"
        output = "Post published successfully"
        metadata = {"post_id": "ig_12345", "platform": "instagram"}
        
        # Save output
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id=agent_id,
            output=output,
            metadata=metadata
        )
        
        # Retrieve with metadata
        result = state_manager_instance.get_agent_output(
            session_id=session_id,
            agent_id=agent_id,
            include_metadata=True
        )
        
        assert result["output"] == output
        assert result["metadata"] == metadata
        assert "timestamp" in result
    
    def test_get_nonexistent_output(self, state_manager_instance):
        """Test retrieving non-existent output"""
        result = state_manager_instance.get_agent_output(
            session_id="nonexistent_session",
            agent_id="nonexistent_agent"
        )
        
        assert result is None
    
    def test_get_previous_agent_output(self, state_manager_instance):
        """Test retrieving previous agent output in chain"""
        session_id = "test_chain_session"
        
        # Save outputs from multiple agents in sequence
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output="Generated content for Instagram"
        )
        
        # Small delay to ensure different timestamps
        import time
        time.sleep(0.1)
        
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id="hashtag_generator",
            output="#GenAI #Learning #Tech"
        )
        
        # Get previous output for social_publisher
        previous_output = state_manager_instance.get_previous_agent_output(
            session_id=session_id,
            current_agent_id="social_publisher"
        )
        
        # Should get the most recent output (hashtag_generator)
        assert previous_output == "#GenAI #Learning #Tech"
    
    def test_get_previous_agent_output_specific(self, state_manager_instance):
        """Test retrieving specific previous agent output"""
        session_id = "test_specific_session"
        
        # Save outputs from multiple agents
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output="Content from content writer"
        )
        
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id="editor",
            output="Edited content"
        )
        
        # Get specific previous agent output
        content_writer_output = state_manager_instance.get_previous_agent_output(
            session_id=session_id,
            current_agent_id="social_publisher",
            previous_agent_id="content_writer"
        )
        
        assert content_writer_output == "Content from content writer"
    
    def test_save_and_get_orchestration_context(self, state_manager_instance):
        """Test saving and retrieving orchestration context"""
        session_id = "test_context_session"
        context = {
            "orchestration_plan": {
                "mode": "sequential",
                "steps": [
                    {"agent_id": "content_writer", "agent_name": "Content Writer"},
                    {"agent_id": "social_publisher", "agent_name": "Social Publisher"}
                ]
            },
            "polished_requirements": "Create Instagram post about GenAI"
        }
        
        # Save context
        state_manager_instance.save_orchestration_context(session_id, context)
        
        # Retrieve context
        retrieved_context = state_manager_instance.get_orchestration_context(session_id)
        
        assert retrieved_context == context
    
    def test_get_session_summary(self, state_manager_instance):
        """Test getting session summary"""
        session_id = "test_summary_session"
        
        # Save multiple agent outputs
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output="Content output",
            metadata={"type": "instagram_post"}
        )
        
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id="social_publisher",
            output="Published",
            metadata={"post_id": "12345"}
        )
        
        # Save context
        state_manager_instance.save_orchestration_context(
            session_id, {"plan": "test"}
        )
        
        # Get summary
        summary = state_manager_instance.get_session_summary(session_id)
        
        assert summary["session_id"] == session_id
        assert summary["total_agents"] == 2
        assert "content_writer" in summary["agents"]
        assert "social_publisher" in summary["agents"]
        assert summary["has_context"] is True
        assert len(summary["states"]) == 2
    
    def test_clear_session_state(self, state_manager_instance):
        """Test clearing session state"""
        session_id = "test_clear_session"
        
        # Save some data
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id="test_agent",
            output="Test output"
        )
        
        # Verify data exists
        assert state_manager_instance.get_agent_output(session_id, "test_agent") == "Test output"
        
        # Clear session
        state_manager_instance.clear_session_state(session_id)
        
        # Verify data is cleared
        assert state_manager_instance.get_agent_output(session_id, "test_agent") is None
        assert session_id not in state_manager_instance._state_cache
    
    def test_persistence_to_disk(self, state_manager_instance):
        """Test that state is persisted to disk"""
        session_id = "test_persist_session"
        agent_id = "content_writer"
        output = "Persisted content"
        
        # Save output
        state_manager_instance.save_agent_output(
            session_id=session_id,
            agent_id=agent_id,
            output=output
        )
        
        # Clear cache to force loading from disk
        state_manager_instance._state_cache.clear()
        
        # Retrieve output (should load from disk)
        retrieved_output = state_manager_instance.get_agent_output(
            session_id=session_id,
            agent_id=agent_id
        )
        
        assert retrieved_output == output
    
    @pytest.mark.asyncio
    async def test_async_wrappers(self, state_manager_instance):
        """Test async wrapper functions"""
        session_id = "test_async_session"
        agent_id = "async_agent"
        output = "Async output"
        
        # Test async save
        state_id = await save_agent_output_async(
            session_id=session_id,
            agent_id=agent_id,
            output=output
        )
        
        assert state_id.startswith(f"{session_id}_{agent_id}_")
        
        # Test async get
        retrieved_output = await get_agent_output_async(
            session_id=session_id,
            agent_id=agent_id
        )
        
        assert retrieved_output == output
        
        # Test async get previous
        previous_output = await get_previous_agent_output_async(
            session_id=session_id,
            current_agent_id="next_agent"
        )
        
        assert previous_output == output
    
    def test_thread_safety(self, state_manager_instance):
        """Test thread safety of state manager"""
        import threading
        import time
        
        session_id = "test_thread_session"
        results = []
        
        def save_output(agent_id, output):
            state_id = state_manager_instance.save_agent_output(
                session_id=session_id,
                agent_id=agent_id,
                output=output
            )
            results.append((agent_id, state_id))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=save_output,
                args=(f"agent_{i}", f"output_{i}")
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all outputs were saved
        assert len(results) == 5
        
        # Verify all outputs can be retrieved
        for i in range(5):
            output = state_manager_instance.get_agent_output(
                session_id=session_id,
                agent_id=f"agent_{i}"
            )
            assert output == f"output_{i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
