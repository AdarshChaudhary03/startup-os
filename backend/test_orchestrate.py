import requests
import json

def test_orchestrate_api():
    """Test the orchestrate API to verify Content Writer routing."""
    
    url = "http://localhost:8000/api/orchestrate"
    payload = {
        "task": "Write an instagram caption for a sunny Day in Delhi"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Testing orchestrate API...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nResponse Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse JSON:")
            print(json.dumps(result, indent=2))
            
            # Check which agent was chosen
            chosen_agent = result.get('chosen_agent_id', 'unknown')
            chosen_agent_name = result.get('chosen_agent_name', 'unknown')
            
            print(f"\n=== ROUTING ANALYSIS ===")
            print(f"Chosen Agent ID: {chosen_agent}")
            print(f"Chosen Agent Name: {chosen_agent_name}")
            
            if chosen_agent == 'content_writer':
                print("SUCCESS: Task correctly routed to Content Writer")
            elif chosen_agent == 'social_publisher':
                print("ISSUE: Task incorrectly routed to Social Media Publisher")
            else:
                print(f"UNEXPECTED: Task routed to {chosen_agent_name}")
                
            # Check the actual output
            output = result.get('output', '')
            print(f"\nOutput Preview: {output[:100]}...")
            
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Is the server running on localhost:8000?")
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_orchestrate_api()
