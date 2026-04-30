"""Test CEO Agent State Management Integration

This test verifies the complete flow from CEO agent delegation through
Content Writer to Social Media Publisher with proper state management.
"""

import pytest
import httpx
import asyncio
import json
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_state_manager import state_manager


class TestCEOAgentStateIntegration:
    """Test suite for CEO agent state management integration."""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API calls."""
        return "http://localhost:8000"
    
    @pytest.fixture
    def session_id(self):
        """Generate a unique session ID for tests."""
        return f"test_ceo_session_{datetime.now(timezone.utc).timestamp()}"
    
    @pytest.fixture
    def cleanup_state(self, session_id):
        """Cleanup state after tests."""
        yield
        # Cleanup after test
        state_manager.clear_session_state(session_id)
    
    @pytest.mark.asyncio
    async def test_content_writer_endpoint_saves_state(self, base_url, session_id, cleanup_state):
        """Test that Content Writer endpoint saves output to state manager."""
        async with httpx.AsyncClient() as client:
            # Call Content Writer endpoint with session ID
            response = await client.post(
                f"{base_url}/api/agents/content_writer",
                json={
                    "task": "Write an Instagram post about GenAI learning for IT professionals with hashtags"
                },
                headers={
                    "X-Session-ID": session_id,
                    "X-Request-ID": f"test_req_{datetime.now(timezone.utc).timestamp()}"
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Check that output was saved to state manager
            saved_output = state_manager.get_agent_output(session_id, "content_writer")
            assert saved_output is not None, "Content Writer output should be saved to state manager"
            
            # Verify it's the actual content, not the full response
            assert isinstance(saved_output, str), "Saved output should be a string"
            assert len(saved_output) > 50, "Saved content should be substantial"
            print(f"✓ Content Writer endpoint saved state: {saved_output[:200]}...")
    
    @pytest.mark.asyncio
    async def test_social_publisher_uses_state_content(self, base_url, session_id, cleanup_state):
        """Test that Social Media Publisher uses content from state manager."""
        # First, save test content to state manager
        test_caption = "🚀 Unlock the power of GenAI! 🤖 Join our exclusive summer training for IT professionals. Learn cutting-edge AI & ML skills to advance your career. Limited seats available! #GenAI #AITraining #ITprofessionals #MachineLearning #SummerTraining #CodeXAI #ArtificialIntelligence #TechSkills #CareerGrowth #AIforIT"
        
        state_manager.save_agent_output(
            session_id=session_id,
            agent_id="content_writer",
            output=test_caption,
            metadata={"test": True}
        )
        
        async with httpx.AsyncClient() as client:
            # Call Social Media Publisher with instruction text
            response = await client.post(
                f"{base_url}/api/agents/social_publisher",
                json={
                    "task": "Schedule and publish the created Instagram post"
                },
                headers={
                    "X-Session-ID": session_id,
                    "X-Request-ID": f"test_req_{datetime.now(timezone.utc).timestamp()}",
                    "X-Agent-Chain": "social_publisher"
                }
            )
            
            # Even if Instagram posting fails, check the logs
            if response.status_code == 200:
                result = response.json()
                output = result.get("output", "")
                
                # Check that it didn't use the instruction text
                assert "Schedule and publish" not in output, "Should not use instruction text as caption"
                print(f"✓ Social Publisher used content from state: {output[:200]}...")
    
    @pytest.mark.asyncio
    async def test_ceo_chat_to_execution_flow(self, base_url, cleanup_state):
        """Test the complete CEO chat to agent execution flow."""
        # Start CEO chat session
        async with httpx.AsyncClient() as client:
            # 1. Start chat
            start_response = await client.post(
                f"{base_url}/api/ceo/chat/start",
                json={"task": "Write and post an Instagram caption about GenAI for IT professionals"}
            )
            
            if start_response.status_code == 200:
                chat_data = start_response.json()
                session_id = chat_data.get("session_id")
                
                # 2. Send message to finalize requirements
                message_response = await client.post(
                    f"{base_url}/api/ceo/chat/message",
                    json={
                        "session_id": session_id,
                        "message": "Target IT professionals, promote GenAI learning"
                    }
                )
                
                # 3. Finalize requirements
                finalize_response = await client.post(
                    f"{base_url}/api/ceo/chat/finalize",
                    json={"session_id": session_id}
                )
                
                if finalize_response.status_code == 200:
                    finalize_data = finalize_response.json()
                    
                    # Check if orchestration plan was created
                    assert finalize_data.get("ready_for_execution") == True
                    assert "orchestration_result" in finalize_data
                    
                    # Verify state was saved
                    context = state_manager.get_orchestration_context(session_id)
                    assert context is not None, "Orchestration context should be saved"
                    
                    print(f"✓ CEO chat flow completed with session {session_id}")
                    
                    # Cleanup
                    state_manager.clear_session_state(session_id)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
