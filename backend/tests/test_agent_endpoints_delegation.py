"""Test cases for agent delegation endpoints"""

import pytest
import httpx
from datetime import datetime
import json


class TestAgentDelegationEndpoints:
    """Test suite for agent delegation endpoints"""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture
    def client(self):
        """Create HTTP client for tests"""
        return httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_content_writer_endpoint_underscore(self, client):
        """Test POST /api/agents/content_writer endpoint"""
        payload = {
            "task": "Write a blog post about AI in healthcare",
            "context": "Focus on recent advancements"
        }
        
        response = await client.post("/api/agents/content_writer", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "output" in data
        assert "agent_id" in data
        assert data["agent_id"] == "content_writer"
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_content_writer_endpoint_hyphen(self, client):
        """Test POST /api/agents/content-writer endpoint"""
        payload = {
            "task": "Write a technical documentation for API",
            "format": "markdown"
        }
        
        response = await client.post("/api/agents/content-writer", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "output" in data
        assert "agent_id" in data
        assert data["agent_id"] == "content_writer"
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_multiple_agent_endpoints(self, client):
        """Test multiple agent endpoints with both formats"""
        test_cases = [
            ("/api/agents/seo_specialist", "seo_specialist", "Optimize SEO for website"),
            ("/api/agents/seo-specialist", "seo_specialist", "Analyze keyword rankings"),
            ("/api/agents/frontend_engineer", "frontend_engineer", "Create React component"),
            ("/api/agents/frontend-engineer", "frontend_engineer", "Fix responsive design"),
            ("/api/agents/backend_engineer", "backend_engineer", "Design REST API"),
            ("/api/agents/backend-engineer", "backend_engineer", "Optimize database queries"),
        ]
        
        for endpoint, expected_agent_id, task in test_cases:
            payload = {"task": task}
            response = await client.post(endpoint, json=payload)
            
            assert response.status_code == 200, f"Endpoint {endpoint} failed: {response.status_code} - {response.text}"
            data = response.json()
            assert data["agent_id"] == expected_agent_id
            assert data["success"] is True
            assert "output" in data
    
    @pytest.mark.asyncio
    async def test_agent_list_endpoint(self, client):
        """Test GET /api/agents/list endpoint"""
        response = await client.get("/api/agents/list")
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total_agents" in data
        assert "total_teams" in data
        
        # Check that agents have both endpoint formats
        for agent in data["agents"]:
            assert "endpoint" in agent
            assert "endpoint_underscore" in agent
            assert "agent_id" in agent
            assert "agent_name" in agent
    
    @pytest.mark.asyncio
    async def test_ceo_delegation_to_content_writer(self, client):
        """Test CEO agent delegating to content_writer"""
        # First, get orchestration plan
        orchestrate_payload = {
            "task": "Create a blog post about machine learning"
        }
        
        orchestrate_response = await client.post("/api/orchestrate", json=orchestrate_payload)
        assert orchestrate_response.status_code == 200
        
        plan = orchestrate_response.json()
        assert "steps" in plan
        assert len(plan["steps"]) > 0
        
        # Execute each step
        for step in plan["steps"]:
            if step["agent_id"] == "content_writer":
                # Test with underscore endpoint
                endpoint = "/api/agents/content_writer"
                payload = {
                    "task": step["instruction"]
                }
                
                response = await client.post(endpoint, json=payload)
                assert response.status_code == 200, f"CEO delegation failed: {response.status_code} - {response.text}"
                
                data = response.json()
                assert data["success"] is True
                assert data["agent_id"] == "content_writer"
                assert "output" in data
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling for invalid requests"""
        # Test with empty task
        response = await client.post("/api/agents/content_writer", json={"task": ""})
        assert response.status_code == 400
        
        # Test with missing task
        response = await client.post("/api/agents/content_writer", json={})
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_agent_not_found(self, client):
        """Test endpoint for non-existent agent"""
        response = await client.post("/api/agents/non_existent_agent", json={"task": "Test"})
        assert response.status_code == 404


if __name__ == "__main__":
    # Run tests
    pytest.main(["-v", __file__])