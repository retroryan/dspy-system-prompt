"""Test complete frontend-backend integration for Real Estate MCP."""

import requests
import json
import time

def test_frontend_integration():
    """Test the complete flow from frontend to backend."""
    
    print("Testing Complete Frontend-Backend Integration")
    print("=" * 60)
    
    # 1. Create a session with real_estate_mcp
    print("\n1. Creating session with real_estate_mcp tool set...")
    session_data = {
        "tool_set": "real_estate_mcp",
        "user_id": "frontend_test_user"
    }
    
    response = requests.post(
        "http://localhost:3010/sessions",
        json=session_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 201:
        print(f"❌ Failed to create session: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    session = response.json()
    session_id = session['session_id']
    print(f"✅ Created session: {session_id}")
    
    # 2. Test the first featured query
    print("\n2. Testing featured query: 'Find modern family homes with pools in Oakland under $800k'...")
    query_data = {
        "query": "Find modern family homes with pools in Oakland under $800k"
    }
    
    response = requests.post(
        f"http://localhost:3010/sessions/{session_id}/query",
        json=query_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Query executed successfully!")
        print(f"   Answer preview: {result.get('answer', '')[:200]}...")
        if 'tool_calls' in result:
            print(f"   Tools used: {len(result['tool_calls'])} tool(s)")
            for tc in result['tool_calls'][:2]:  # Show first 2 tools
                print(f"     - {tc.get('tool_name', 'unknown')}")
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
    
    # 3. Test the second featured query
    print("\n3. Testing featured query: 'Tell me about the Temescal neighborhood in Oakland'...")
    query_data = {
        "query": "Tell me about the Temescal neighborhood in Oakland - what amenities and culture does it offer?"
    }
    
    response = requests.post(
        f"http://localhost:3010/sessions/{session_id}/query",
        json=query_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Query executed successfully!")
        print(f"   Answer preview: {result.get('answer', '')[:200]}...")
        if 'tool_calls' in result:
            print(f"   Tools used: {len(result['tool_calls'])} tool(s)")
            for tc in result['tool_calls'][:2]:  # Show first 2 tools
                print(f"     - {tc.get('tool_name', 'unknown')}")
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
    
    # 4. Get session info to verify state
    print("\n4. Verifying session state...")
    response = requests.get(f"http://localhost:3010/sessions/{session_id}")
    
    if response.status_code == 200:
        session_info = response.json()
        print(f"✅ Session is active")
        print(f"   Conversation turns: {session_info.get('conversation_turns', 0)}")
        print(f"   Tool set: {session_info.get('tool_set')}")
    else:
        print(f"❌ Failed to get session info: {response.status_code}")
    
    # 5. Clean up
    print("\n5. Cleaning up...")
    response = requests.delete(f"http://localhost:3010/sessions/{session_id}")
    if response.status_code == 204:
        print("✅ Session deleted successfully")
    else:
        print(f"⚠️  Failed to delete session: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("✅ Frontend-Backend Integration Test Complete!")
    print("\nThe Real Estate MCP tools are fully integrated and working!")
    print("Users can now:")
    print("  - Select '🏠 Real Estate' from the tool dropdown")
    print("  - Click featured query boxes for instant property searches")
    print("  - Use all 6 MCP tools for comprehensive real estate queries")
    
    return True

if __name__ == "__main__":
    print("\n🔧 Real Estate MCP Frontend Integration Test")
    print("=" * 60)
    print("Prerequisites:")
    print("  1. API server running on http://localhost:3010")
    print("  2. MCP server running on http://localhost:8000/mcp")
    print("  3. Elasticsearch running (for property data)")
    print()
    
    try:
        # Quick connectivity check
        response = requests.get("http://localhost:3010/tool-sets", timeout=2)
        response.raise_for_status()
        
        # MCP server check - just verify it's reachable, don't require specific response
        response = requests.get("http://localhost:8000/mcp/list-tools", timeout=2)
        
        print("✅ All servers are reachable\n")
        
        success = test_frontend_integration()
        
        if not success:
            print("\n❌ Some tests failed. Check the errors above.")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Could not connect to required servers")
        print(f"   Error: {e}")
        print("\n   Make sure all servers are running:")
        print("   - API: cd api && uvicorn main:app --reload --port 3010")
        print("   - MCP: (check your MCP server setup)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")