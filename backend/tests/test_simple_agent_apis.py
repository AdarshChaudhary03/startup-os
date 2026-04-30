"""Test cases for simplified agent API endpoints"""

import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime
import json

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = f"test-session-{int(datetime.now().timestamp())}"


class TestSimpleContentWriter:
    """Test cases for simplified Content Writer API"""
    
    @pytest.mark.asyncio
    async def test_content_writer_instagram_post(self):
        """Test generating Instagram post"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/simple/content_writer",
                json={
                    "topic": "GenAI for students",
                    "mode": "instagram_post"
                },
                headers={"X-Session-ID": TEST_SESSION_ID}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["mode"] == "instagram_post"
            assert data["topic"] == "GenAI for students"
            assert len(data["content"]) > 0
            assert data["word_count"] > 0
            assert "request_id" in data
            assert "timestamp" in data
            
            # Check for hashtags in Instagram posts
            if data.get("hashtags"):
                assert isinstance(data["hashtags"], list)
            
            print(f"✓ Generated Instagram post: {len(data['content'])} chars")
    
    @pytest.mark.asyncio
    async def test_content_writer_blog_post(self):
        """Test generating blog post"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/simple/content_writer",
                json={
                    "topic": "Benefits of AI in education",
                    "mode": "blog"
                },
                headers={"X-Session-ID": TEST_SESSION_ID}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["mode"] == "blog"
            assert len(data["content"]) > 100  # Blogs should be longer
            
            print(f"✓ Generated blog post: {data['word_count']} words")
    
    @pytest.mark.asyncio
    async def test_content_writer_missing_topic(self):
        """Test error handling for missing topic"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/simple/content_writer",
                json={"mode": "instagram_post"}
            )
            
            assert response.status_code == 422
            error = response.json()
            assert "detail" in error
            
            print("✓ Correctly rejected request with missing topic")
    
    @pytest.mark.asyncio
    async def test_content_writer_invalid_mode(self):
        """Test error handling for invalid mode"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/simple/content_writer",
                json={
                    "topic": "Test topic",
                    "mode": "invalid_mode"
                }
            )
            
            assert response.status_code == 422
            
            print("✓ Correctly rejected request with invalid mode")


class TestSimpleSocialPublisher:
    """Test cases for simplified Social Publisher API"""
    
    @pytest.mark.asyncio
    async def test_social_publisher_instagram(self):
        """Test publishing to Instagram"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # First generate content
            content_response = await client.post(
                "/api/simple/content_writer",
                json={
                    "topic": "GenAI for students",
                    "mode": "instagram_post"
                },
                headers={"X-Session-ID": TEST_SESSION_ID}
            )
            
            assert content_response.status_code == 200
            content_data = content_response.json()
            
            # Then publish it
            response = await client.post(
                "/api/simple/social_publisher",
                json={
                    "caption": content_data["content"],
                    "platform": "instagram"
                },
                headers={"X-Session-ID": TEST_SESSION_ID}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["platform"] == "instagram"
            assert "post_id" in data
            assert "request_id" in data
            assert "published_at" in data
            
            if data["success"]:
                assert data["post_url"] != ""
                print(f"✓ Published to Instagram: {data['post_url']}")
            else:
                print(f"✓ Instagram publish simulated (test mode): {data.get('error', 'Success')}")
    
    @pytest.mark.asyncio
    async def test_social_publisher_with_image(self):
        """Test publishing with image"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/simple/social_publisher",
                json={
                    "caption": "Check out GenAI! 🚀 #AI #Technology",
                    "platform": "instagram",
                    "image_url": "https://picsum.photos/1080/1080"
                },
                headers={"X-Session-ID": TEST_SESSION_ID}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["platform"] == "instagram"
            
            print(f"✓ Published with image to {data['platform']}")
    
    @pytest.mark.asyncio
    async def test_social_publisher_missing_caption(self):
        """Test error handling for missing caption"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/simple/social_publisher",
                json={"platform": "instagram"}
            )
            
            assert response.status_code == 422
            error = response.json()
            assert "detail" in error
            
            print("✓ Correctly rejected request with missing caption")
    
    @pytest.mark.asyncio
    async def test_social_publisher_invalid_platform(self):
        """Test error handling for invalid platform"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/simple/social_publisher",
                json={
                    "caption": "Test caption",
                    "platform": "invalid_platform"
                }
            )
            
            assert response.status_code == 422
            
            print("✓ Correctly rejected request with invalid platform")


class TestEndToEndWorkflow:
    """Test end-to-end workflow using simplified APIs"""
    
    @pytest.mark.asyncio
    async def test_generate_and_publish_workflow(self):
        """Test complete workflow: generate content then publish"""
        session_id = f"workflow-test-{int(datetime.now().timestamp())}"
        
        async with AsyncClient(base_url=BASE_URL) as client:
            # Step 1: Generate content
            print("\n1. Generating content...")
            content_response = await client.post(
                "/api/simple/content_writer",
                json={
                    "topic": "Benefits of AI in education",
                    "mode": "instagram_post"
                },
                headers={"X-Session-ID": session_id}
            )
            
            assert content_response.status_code == 200
            content_data = content_response.json()
            print(f"   Generated: {content_data['content'][:100]}...")
            
            # Step 2: Publish to Instagram
            print("\n2. Publishing to Instagram...")
            publish_response = await client.post(
                "/api/simple/social_publisher",
                json={
                    "caption": content_data["content"],
                    "platform": "instagram",
                    "image_url": "https://picsum.photos/1080/1080"
                },
                headers={"X-Session-ID": session_id}
            )
            
            assert publish_response.status_code == 200
            publish_data = publish_response.json()
            
            print(f"   Published: {publish_data.get('post_url', 'Simulated')}")
            print(f"   Success: {publish_data.get('success', False)}")
            
            print("\n✓ End-to-end workflow completed successfully!")


class TestAPIHealth:
    """Test API health and availability"""
    
    @pytest.mark.asyncio
    async def test_simple_api_health(self):
        """Test health endpoint"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/api/simple/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert "/api/simple/content_writer" in data["endpoints"]
            assert "/api/simple/social_publisher" in data["endpoints"]
            
            print("✓ Simple API endpoints are healthy")


def run_tests():
    """Run all test cases"""
    print("=" * 60)
    print("Running Simplified Agent API Tests")
    print("=" * 60)
    
    # Run tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_"
    ])


if __name__ == "__main__":
    # For standalone execution
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick test of basic functionality
        print("Running quick test...\n")
        
        async def quick_test():
            async with AsyncClient(base_url=BASE_URL) as client:
                # Test content generation
                response = await client.post(
                    "/api/simple/content_writer",
                    json={
                        "topic": "Quick test of GenAI",
                        "mode": "instagram_post"
                    }
                )
                
                if response.status_code == 200:
                    print("✓ Content Writer API is working")
                    print(f"  Generated: {response.json()['content'][:50]}...")
                else:
                    print(f"✗ Content Writer API failed: {response.status_code}")
                    print(f"  Error: {response.text}")
        
        asyncio.run(quick_test())
    else:
        # Run full test suite
        run_tests()