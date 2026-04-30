import requests
import json

# Test the social_publisher endpoint
print("Testing social_publisher endpoint...")

try:
    response = requests.post(
        "http://localhost:8000/api/agents/social_publisher",
        json={"task": "Test social media publishing"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 404:
        print("ERROR: Endpoint not found!")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test the list agents endpoint
print("\nTesting list agents endpoint...")
try:
    response = requests.get("http://localhost:8000/api/agents/list")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        # Find social publisher
        for agent in data.get("agents", []):
            if agent["agent_id"] == "social_publisher":
                print(f"\nSocial Publisher endpoint: {agent['endpoint']}")
                break
except Exception as e:
    print(f"Error: {e}")