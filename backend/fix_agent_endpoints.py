#!/usr/bin/env python3
"""
Fix script for agent endpoints 404 errors
This script analyzes and fixes the endpoint routing issues
"""

import os
import sys

def check_server_status():
    """Check if server is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Server is running and healthy")
            return True
        else:
            print(f"[WARNING] Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server is not running or not accessible")
        return False
    except Exception as e:
        print(f"[ERROR] Error checking server: {e}")
        return False

def check_agent_routes():
    """Check agent routes configuration"""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/agents/list", timeout=5)
        if response.status_code == 200:
            agents = response.json()
            print("\nAvailable Agent Endpoints:")
            for agent in agents.get('agents', []):
                print(f"  - {agent['endpoint']} ({agent['agent_name']})")
            return True
        else:
            print(f"[WARNING] Agent list endpoint responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Error checking agent routes: {e}")
        return False

def test_specific_endpoints():
    """Test specific problematic endpoints"""
    endpoints_to_test = [
        "/api/agents/content-writer",
        "/api/agents/social-media-publisher",
        "/api/agents/social-publisher"  # Check if old endpoint still exists
    ]
    
    print("\nTesting Specific Endpoints:")
    
    for endpoint in endpoints_to_test:
        try:
            import requests
            url = f"http://localhost:8000{endpoint}"
            
            # Test with OPTIONS method first (to check if endpoint exists)
            options_response = requests.options(url, timeout=5)
            print(f"  {endpoint}: OPTIONS {options_response.status_code}")
            
            # Test with POST method
            post_response = requests.post(url, json={"task": "test"}, timeout=5)
            print(f"  {endpoint}: POST {post_response.status_code}")
            
            if post_response.status_code == 422:  # Validation error is expected
                print(f"    [OK] Endpoint exists (validation error expected)")
            elif post_response.status_code == 404:
                print(f"    [ERROR] Endpoint not found")
            else:
                print(f"    [WARNING] Unexpected status: {post_response.status_code}")
                
        except Exception as e:
            print(f"  {endpoint}: [ERROR] Error - {e}")

def analyze_route_files():
    """Analyze route files for issues"""
    print("\nAnalyzing Route Files:")
    
    files_to_check = [
        "agent_routes.py",
        "server.py",
        "orchestration_routes.py"
    ]
    
    for file_name in files_to_check:
        if os.path.exists(file_name):
            print(f"  [OK] {file_name} exists")
            
            # Check for specific patterns
            with open(file_name, 'r') as f:
                content = f.read()
                
            if file_name == "agent_routes.py":
                if "@agent_router.post(\"/content-writer\")" in content:
                    print(f"    [OK] Content Writer endpoint defined")
                else:
                    print(f"    [ERROR] Content Writer endpoint not found")
                    
                if "@agent_router.post(\"/social-media-publisher\")" in content:
                    print(f"    [OK] Social Media Publisher endpoint defined")
                else:
                    print(f"    [ERROR] Social Media Publisher endpoint not found")
                    
            elif file_name == "server.py":
                if "app.include_router(agent_router)" in content:
                    print(f"    [OK] Agent router included in server")
                else:
                    print(f"    [ERROR] Agent router not included in server")
        else:
            print(f"  [ERROR] {file_name} not found")

def main():
    """Main analysis function"""
    print("Agent Endpoints Fix Analysis")
    print("===============================")
    
    # Check server status
    if not check_server_status():
        print("\nSolution: Start the server with 'python server.py'")
        return
    
    # Check agent routes
    check_agent_routes()
    
    # Test specific endpoints
    test_specific_endpoints()
    
    # Analyze route files
    analyze_route_files()
    
    print("\nAnalysis Complete!")
    print("\nNext Steps:")
    print("1. Ensure server is running: python server.py")
    print("2. Test endpoints with: python test_agent_endpoints.py")
    print("3. Check logs for detailed error information")

if __name__ == "__main__":
    main()