"""Test if the API recognizes the real_estate_mcp tool set."""

import requests
import json

def test_api_tool_sets():
    """Test the API tool sets endpoint."""
    
    print("Testing API tool sets endpoint...")
    
    # Test getting all tool sets
    response = requests.get("http://localhost:3010/tool-sets")
    
    if response.status_code == 200:
        tool_sets = response.json()
        print(f"✅ Found {len(tool_sets)} tool sets:")
        for ts in tool_sets:
            print(f"  - {ts['name']}: {ts['description']}")
        
        # Check if real_estate_mcp is in the list
        names = [ts['name'] for ts in tool_sets]
        if 'real_estate_mcp' in names:
            print("\n✅ real_estate_mcp tool set is registered!")
        else:
            print("\n❌ real_estate_mcp tool set NOT found!")
            return False
    else:
        print(f"❌ Failed to get tool sets: {response.status_code}")
        return False
    
    # Test getting specific real_estate_mcp tool set
    print("\nTesting specific real_estate_mcp tool set...")
    response = requests.get("http://localhost:3010/tool-sets/real_estate_mcp")
    
    if response.status_code == 200:
        tool_set = response.json()
        print(f"✅ Got real_estate_mcp tool set:")
        print(f"  Tools: {', '.join(tool_set['tools'])}")
        print(f"  Example queries: {len(tool_set['example_queries'])} queries")
    else:
        print(f"❌ Failed to get real_estate_mcp: {response.status_code}")
        if response.text:
            print(f"  Error: {response.text}")
        return False
    
    # Test creating a session with real_estate_mcp
    print("\nTesting session creation with real_estate_mcp...")
    session_data = {
        "tool_set": "real_estate_mcp",
        "user_id": "test_user_123"
    }
    
    response = requests.post(
        "http://localhost:3010/sessions",
        json=session_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        session = response.json()
        print(f"✅ Created session with real_estate_mcp:")
        print(f"  Session ID: {session['session_id']}")
        print(f"  Tool set: {session['tool_set']}")
        print(f"  Status: {session['status']}")
        
        # Clean up - delete the session
        requests.delete(f"http://localhost:3010/sessions/{session['session_id']}")
        return True
    else:
        print(f"❌ Failed to create session: {response.status_code}")
        if response.text:
            try:
                error = response.json()
                print(f"  Error: {error.get('detail', response.text)}")
            except:
                print(f"  Error: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Real Estate MCP Tool Set in API")
    print("=" * 60)
    print("\nMake sure the API server is running on http://localhost:3010")
    print()
    
    try:
        success = test_api_tool_sets()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ All API tests passed! Real Estate MCP is properly registered.")
        else:
            print("❌ Some tests failed. Check the errors above.")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server at http://localhost:3010")
        print("   Make sure the API server is running with:")
        print("   cd api && uvicorn main:app --reload --port 8080")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")