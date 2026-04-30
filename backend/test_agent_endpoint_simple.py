"""Simple test to verify agent endpoints are working"""

import requests
import json

# Test the content_writer endpoint with underscore format
url = "http://localhost:8000/api/agents/content_writer"
payload = {
    "task": "Write a simple test message"
}

print(f"Testing endpoint: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! The content_writer endpoint is working.")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"\n❌ ERROR: Got status code {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Could not connect to the server. Make sure the backend is running on http://localhost:8000")
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")

# Test the list endpoint to see all available agents
print("\n" + "="*50)
print("Testing list agents endpoint...")

try:
    list_response = requests.get("http://localhost:8000/api/agents/list", timeout=10)
    if list_response.status_code == 200:
        agents_data = list_response.json()
        print(f"\nTotal agents: {agents_data.get('total_agents', 0)}")
        print(f"Total teams: {agents_data.get('total_teams', 0)}")
        
        # Find content_writer agent
        content_writer_agents = [a for a in agents_data.get('agents', []) if a['agent_id'] == 'content_writer']
        if content_writer_agents:
            agent = content_writer_agents[0]
            print(f"\nContent Writer Agent found:")
            print(f"  - Name: {agent['agent_name']}")
            print(f"  - Hyphen endpoint: {agent['endpoint']}")
            print(f"  - Underscore endpoint: {agent.get('endpoint_underscore', 'Not available')}")
        else:
            print("\n❌ Content Writer agent not found in the list!")
    else:
        print(f"\n❌ List endpoint error: {list_response.status_code}")
        
except Exception as e:
    print(f"\n❌ List endpoint error: {type(e).__name__}: {e}")