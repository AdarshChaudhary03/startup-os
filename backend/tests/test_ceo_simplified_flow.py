"""Test cases for Simplified CEO Agent Flow

This module contains comprehensive test cases for the simplified CEO agent architecture.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ceo_simplified_flow import SimplifiedCEOAgent, CEOFlowState


class TestSimplifiedCEOAgent:
    """Test suite for SimplifiedCEOAgent"""
    
    @pytest.fixture
    def ceo_agent(self):
        """Create a CEO agent instance for testing"""
        return SimplifiedCEOAgent()
    
    @pytest.fixture
    def mock_orchestration_response(self):
        """Mock orchestration response"""
        return {
            "request_id": "test-123",
            "task": "Create a blog post about AI",
            "mode": "sequential",
            "rationale": "Content creation task requiring content writer",
            "steps": [
                {
                    "agent_id": "content_writer",
                    "agent_name": "Content Writer",
                    "team_id": "content",
                    "team_name": "Content Team",
                    "instruction": "Write a blog post about AI benefits",
                    "endpoint": "/api/agents/content-writer"
                },
                {
                    "agent_id": "qa_tester",
                    "agent_name": "QA Tester",
                    "team_id": "qa",
                    "team_name": "QA Team",
                    "instruction": "Review the blog post for quality",
                    "endpoint": "/api/agents/qa-tester"
                }
            ],
            "total_steps": 2,
            "used_llm": True
        }
    
    def test_format_requirements(self, ceo_agent):
        """Test requirements formatting"""
        clarified_requirements = {
            "original_task": "Create a blog post",
            "purpose": "Educate readers about AI benefits",
            "target_audience": "Tech professionals",
            "scope": "1000-1500 words covering key AI applications",
            "constraints": "Must be SEO optimized",
            "timeline": "2 days",
            "success_criteria": ["Engaging content", "SEO friendly", "Accurate information"]
        }
        
        formatted = ceo_agent.format_requirements(clarified_requirements)
        
        assert "Task: Create a blog post" in formatted
        assert "Purpose: Educate readers about AI benefits" in formatted
        assert "Target Audience: Tech professionals" in formatted
        assert "- Engaging content" in formatted
        assert "- SEO friendly" in formatted
    
    @pytest.mark.asyncio
    async def test_get_orchestration_plan(self, ceo_agent, mock_orchestration_response):
        """Test orchestration plan retrieval"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_orchestration_response
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            plan = await ceo_agent.get_orchestration_plan(
                "Formatted requirements here",
                "test-session-123"
            )
            
            assert plan["mode"] == "sequential"
            assert len(plan["steps"]) == 2
            assert plan["steps"][0]["agent_id"] == "content_writer"
    
    def test_prepare_agent_request(self, ceo_agent):
        """Test agent request preparation"""
        # Test content writer request
        payload = ceo_agent.prepare_agent_request(
            agent_id="content_writer",
            instruction="Write a blog post",
            previous_output=None,
            context={"polished_requirements": "Requirements here"}
        )
        
        assert payload["task"] == "Write a blog post"
        assert payload["format"] == "structured"
        assert payload["tone"] == "professional"
        
        # Test QA tester with previous output
        payload = ceo_agent.prepare_agent_request(
            agent_id="qa_tester",
            instruction="Review the blog post",
            previous_output="Blog post content here...",
            context={"previous_agent": "Content Writer"}
        )
        
        assert payload["task"] == "Review the blog post"
        assert "Previous work from Content Writer" in payload["context"]
        assert payload["code_to_test"] == "Blog post content here..."
        assert "unit" in payload["test_types"]
    
    @pytest.mark.asyncio
    async def test_execute_agent_success(self, ceo_agent):
        """Test successful agent execution"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "output": "Blog post content generated successfully",
                "duration_ms": 1500,
                "success": True
            }
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await ceo_agent.execute_agent(
                agent_id="content_writer",
                agent_name="Content Writer",
                endpoint="/api/agents/content-writer",
                payload={"task": "Write blog"},
                session_id="test-123"
            )
            
            assert result["success"] is True
            assert result["agent_id"] == "content_writer"
            assert "output" in result["response"]
    
    @pytest.mark.asyncio
    async def test_execute_agent_failure(self, ceo_agent):
        """Test agent execution failure"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await ceo_agent.execute_agent(
                agent_id="content_writer",
                agent_name="Content Writer",
                endpoint="/api/agents/content-writer",
                payload={"task": "Write blog"},
                session_id="test-123"
            )
            
            assert result["success"] is False
            assert "Status 500" in result["error"]
    
    def test_process_agent_response(self, ceo_agent):
        """Test agent response processing"""
        # Test successful response
        agent_result = {
            "success": True,
            "agent_id": "content_writer",
            "agent_name": "Content Writer",
            "response": {
                "output": "Generated blog post content",
                "duration_ms": 2000
            }
        }
        
        processed = ceo_agent.process_agent_response(agent_result)
        
        assert processed["success"] is True
        assert processed["output"] == "Generated blog post content"
        assert processed["duration_ms"] == 2000
        assert "timestamp" in processed
        
        # Test failed response
        failed_result = {
            "success": False,
            "agent_id": "content_writer",
            "agent_name": "Content Writer",
            "error": "Failed to generate content"
        }
        
        processed_failed = ceo_agent.process_agent_response(failed_result)
        assert processed_failed["success"] is False
    
    @pytest.mark.asyncio
    async def test_execute_plan_sequentially(self, ceo_agent, mock_orchestration_response):
        """Test sequential plan execution"""
        with patch.object(ceo_agent, 'execute_agent') as mock_execute:
            # Mock successful executions
            mock_execute.side_effect = [
                {
                    "success": True,
                    "agent_id": "content_writer",
                    "agent_name": "Content Writer",
                    "response": {"output": "Blog post content"}
                },
                {
                    "success": True,
                    "agent_id": "qa_tester",
                    "agent_name": "QA Tester",
                    "response": {"output": "Quality review passed"}
                }
            ]
            
            results = await ceo_agent.execute_plan_sequentially(
                mock_orchestration_response,
                "Polished requirements",
                "test-session-123"
            )
            
            assert len(results) == 2
            assert results[0]["agent_id"] == "content_writer"
            assert results[0]["output"] == "Blog post content"
            assert results[1]["agent_id"] == "qa_tester"
            assert results[1]["output"] == "Quality review passed"
            assert ceo_agent.current_state == CEOFlowState.COMPLETED
    
    @pytest.mark.asyncio
    async def test_process_user_task_complete_flow(self, ceo_agent, mock_orchestration_response):
        """Test complete user task processing flow"""
        with patch.object(ceo_agent, 'clarify_requirements') as mock_clarify:
            mock_clarify.return_value = {
                "original_task": "Create a blog post",
                "purpose": "Educate about AI",
                "target_audience": "Tech professionals",
                "scope": "1000 words",
                "constraints": "SEO optimized",
                "timeline": "2 days",
                "success_criteria": ["Engaging", "Accurate"]
            }
            
            with patch.object(ceo_agent, 'get_orchestration_plan') as mock_orchestrate:
                mock_orchestrate.return_value = mock_orchestration_response
                
                with patch.object(ceo_agent, 'execute_plan_sequentially') as mock_execute:
                    mock_execute.return_value = [
                        {"agent_id": "content_writer", "success": True, "output": "Blog created"},
                        {"agent_id": "qa_tester", "success": True, "output": "Quality verified"}
                    ]
                    
                    result = await ceo_agent.process_user_task(
                        "Create a blog post about AI",
                        "test-session-123"
                    )
                    
                    assert result["success"] is True
                    assert result["final_state"] == CEOFlowState.COMPLETED.value
                    assert len(result["execution_results"]) == 2
                    assert "polished_requirements" in result
                    assert "orchestration_plan" in result
    
    def test_get_agent_payload_format(self, ceo_agent):
        """Test getting agent payload formats"""
        # Test known agent
        format_content = ceo_agent.get_agent_payload_format("content_writer")
        assert format_content["task"] == "string"
        assert "tone" in format_content
        
        # Test unknown agent
        format_unknown = ceo_agent.get_agent_payload_format("unknown_agent")
        assert format_unknown["task"] == "string"
        assert format_unknown["context"] == "optional<string>"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, ceo_agent):
        """Test error handling in the flow"""
        with patch.object(ceo_agent, 'clarify_requirements') as mock_clarify:
            mock_clarify.side_effect = Exception("Requirements clarification failed")
            
            result = await ceo_agent.process_user_task(
                "Create a blog post",
                "test-session-123"
            )
            
            assert result["success"] is False
            assert "Requirements clarification failed" in result["error"]
            assert result["final_state"] == CEOFlowState.FAILED.value


if __name__ == "__main__":
    pytest.main(["-v", __file__])
