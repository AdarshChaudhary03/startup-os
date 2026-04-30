import pytest
import httpx
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app
from models import OrchestrateRequest, AgentExecutionRequest

# Create test client
client = TestClient(app)


class TestAgentEndpoints:
    """Test suite for agent endpoint routing and orchestration"""
    
    def test_social_publisher_endpoint_exists(self):
        """Test that social_publisher endpoint exists and is accessible"""
        # Test the standardized underscore endpoint
        response = client.post(
            "/api/agents/social_publisher",
            json={"task": "Test social media publishing"}
        )
        # Should not return 404
        assert response.status_code != 404, f"Endpoint /api/agents/social_publisher returned 404"
        
    def test_content_writer_endpoint_exists(self):
        """Test that content_writer endpoint exists and is accessible"""
        response = client.post(
            "/api/agents/content_writer",
            json={"task": "Test content writing"}
        )
        # Should not return 404
        assert response.status_code != 404, f"Endpoint /api/agents/content_writer returned 404"
        
    def test_orchestration_returns_correct_endpoints(self):
        """Test that orchestration returns correct endpoint formats"""
        response = client.post(
            "/api/orchestrate",
            json={"task": "Create a social media post about our new product launch"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that steps contain proper endpoints
        assert "steps" in data
        for step in data["steps"]:
            assert "endpoint" in step
            # Endpoint should use underscore format
            assert step["endpoint"].startswith("/api/agents/")
            # Extract agent_id from endpoint
            agent_id = step["endpoint"].replace("/api/agents/", "")
            # Should match the agent_id in the step
            assert agent_id == step["agent_id"]
            
    def test_all_agent_endpoints_standardized(self):
        """Test that all agent endpoints use standardized underscore format"""
        response = client.get("/api/agents/list")
        assert response.status_code == 200
        
        data = response.json()
        agents = data["agents"]
        
        for agent in agents:
            # Check endpoint format
            assert "endpoint" in agent
            endpoint = agent["endpoint"]
            agent_id = agent["agent_id"]
            
            # Endpoint should be /api/agents/{agent_id} with underscore format
            expected_endpoint = f"/api/agents/{agent_id}"
            assert endpoint == expected_endpoint, f"Agent {agent_id} has incorrect endpoint: {endpoint}"
            
            # Test that the endpoint is accessible
            response = client.post(
                endpoint,
                json={"task": f"Test task for {agent['agent_name']}"}
            )
            # Should not return 404
            assert response.status_code != 404, f"Endpoint {endpoint} returned 404"
            
    def test_ceo_delegation_to_social_publisher(self):
        """Test CEO agent delegation to social media publisher"""
        # First, get orchestration plan
        orchestrate_response = client.post(
            "/api/orchestrate",
            json={"task": "Create and publish a social media post about our product"}
        )
        
        assert orchestrate_response.status_code == 200
        plan = orchestrate_response.json()
        
        # Find social publisher in steps
        social_publisher_step = None
        for step in plan.get("steps", []):
            if step["agent_id"] == "social_publisher":
                social_publisher_step = step
                break
                
        if social_publisher_step:
            # Test the endpoint from orchestration
            endpoint = social_publisher_step["endpoint"]
            response = client.post(
                endpoint,
                json={
                    "task": social_publisher_step["instruction"],
                    "content": "Test content from content writer",
                    "platform": "instagram"
                }
            )
            # Should not return 404
            assert response.status_code != 404, f"Social publisher endpoint {endpoint} returned 404"
            
    def test_no_hyphenated_endpoints(self):
        """Test that no hyphenated endpoints exist"""
        # Test some common hyphenated formats that should NOT exist
        hyphenated_endpoints = [
            "/api/agents/content-writer",
            "/api/agents/social-media-publisher",
            "/api/agents/social-publisher",
            "/api/agents/seo-specialist",
            "/api/agents/frontend-engineer",
            "/api/agents/backend-engineer"
        ]
        
        for endpoint in hyphenated_endpoints:
            response = client.post(
                endpoint,
                json={"task": "Test task"}
            )
            # Should return 404 for hyphenated endpoints
            assert response.status_code == 404, f"Hyphenated endpoint {endpoint} should not exist but returned {response.status_code}"


if __name__ == "__main__":
    # Run tests
    test = TestAgentEndpoints()
    
    print("Testing agent endpoints...")
    
    try:
        test.test_social_publisher_endpoint_exists()
        print("✓ Social publisher endpoint exists")
    except AssertionError as e:
        print(f"✗ Social publisher endpoint test failed: {e}")
        
    try:
        test.test_content_writer_endpoint_exists()
        print("✓ Content writer endpoint exists")
    except AssertionError as e:
        print(f"✗ Content writer endpoint test failed: {e}")
        
    try:
        test.test_orchestration_returns_correct_endpoints()
        print("✓ Orchestration returns correct endpoints")
    except AssertionError as e:
        print(f"✗ Orchestration endpoint test failed: {e}")
        
    try:
        test.test_all_agent_endpoints_standardized()
        print("✓ All agent endpoints are standardized")
    except AssertionError as e:
        print(f"✗ Agent endpoint standardization test failed: {e}")
        
    try:
        test.test_ceo_delegation_to_social_publisher()
        print("✓ CEO delegation to social publisher works")
    except AssertionError as e:
        print(f"✗ CEO delegation test failed: {e}")
        
    try:
        test.test_no_hyphenated_endpoints()
        print("✓ No hyphenated endpoints exist")
    except AssertionError as e:
        print(f"✗ Hyphenated endpoint test failed: {e}")
        
    print("\nAll tests completed!")