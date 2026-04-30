import pytest
import httpx
import asyncio
from typing import Dict, Any
import json

# Test configuration
BASE_URL = "http://localhost:8000"


class TestCEOChatEndpoint:
    """Integration tests for CEO chat endpoint"""
    
    @pytest.mark.asyncio
    async def test_chat_message_endpoint(self):
        """Test the /api/ceo/chat/message endpoint"""
        
        async with httpx.AsyncClient() as client:
            # First, start a chat session
            start_response = await client.post(
                f"{BASE_URL}/api/ceo/chat/start",
                json={
                    "task": "Build a web application for e-commerce"
                }
            )
            
            # Check if start endpoint is working
            if start_response.status_code != 200:
                print(f"Start endpoint failed with status: {start_response.status_code}")
                print(f"Response: {start_response.text}")
                return
            
            start_data = start_response.json()
            conversation_id = start_data.get("conversation_id")
            
            # Now test the message endpoint
            message_response = await client.post(
                f"{BASE_URL}/api/ceo/chat/message",
                json={
                    "conversation_id": conversation_id,
                    "message": "The main purpose is to create an online marketplace for handmade crafts"
                }
            )
            
            # Verify the response
            assert message_response.status_code == 200, f"Expected 200, got {message_response.status_code}"
            
            message_data = message_response.json()
            assert "conversation_id" in message_data
            assert "state" in message_data
            assert "message" in message_data
            assert "requirements" in message_data
            
            print("✓ CEO chat message endpoint is working correctly")
            print(f"Response state: {message_data['state']}")
            print(f"Response message: {message_data['message'][:100]}...")
    
    def test_sync_endpoint(self):
        """Synchronous test for the endpoint"""
        import requests
        
        # Start a chat session
        start_response = requests.post(
            f"{BASE_URL}/api/ceo/chat/start",
            json={
                "task": "Build a mobile app for fitness tracking"
            }
        )
        
        if start_response.status_code != 200:
            print(f"Start endpoint failed with status: {start_response.status_code}")
            print(f"Response: {start_response.text}")
            return
        
        start_data = start_response.json()
        conversation_id = start_data.get("conversation_id")
        
        # Test the message endpoint
        message_response = requests.post(
            f"{BASE_URL}/api/ceo/chat/message",
            json={
                "conversation_id": conversation_id,
                "message": "The app should help users track their workouts and nutrition"
            }
        )
        
        # Verify no AttributeError occurs
        assert message_response.status_code == 200, f"Expected 200, got {message_response.status_code}"
        assert "'CEOConversationFlow' object has no attribute 'process_user_message'" not in message_response.text
        
        print("✓ No AttributeError - process_user_message method is working")


if __name__ == "__main__":
    # Run the synchronous test
    test = TestCEOChatEndpoint()
    
    print("Testing CEO chat endpoint...")
    print("="*50)
    
    try:
        test.test_sync_endpoint()
        print("\n✅ CEO chat endpoint test passed!")
        print("The AttributeError has been fixed.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nMake sure the backend server is running on http://localhost:8000")