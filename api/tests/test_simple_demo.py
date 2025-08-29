#!/usr/bin/env python3
"""
Simple test script for the Agentic Loop API.

This script demonstrates the basic API workflow:
1. Create a session
2. Execute queries
3. View session info
4. Clean up
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time
from datetime import datetime


# API base URL
BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed")
        print(f"   Status: {data['status']}")
        print(f"   Version: {data['version']}")
        print(f"   Uptime: {data['uptime_seconds']:.1f}s")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        

def test_tool_sets():
    """Test tool set endpoints."""
    print("\n=== Testing Tool Set Endpoints ===")
    
    # List all tool sets
    response = requests.get(f"{BASE_URL}/tool-sets")
    if response.status_code == 200:
        tool_sets = response.json()
        print(f"✅ Found {len(tool_sets)} tool sets:")
        for ts in tool_sets:
            print(f"   - {ts['name']}: {ts['description']}")
    else:
        print(f"❌ Failed to list tool sets: {response.status_code}")


def test_session_workflow():
    """Test complete session workflow."""
    print("\n=== Testing Session Workflow ===")
    
    # 1. Create session
    print("\n1. Creating session...")
    session_data = {
        "tool_set": "ecommerce",
        "user_id": "test_user",
        "config": {
            "max_messages": 20,
            "summarize_removed": True
        }
    }
    
    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 201:
        print(f"❌ Failed to create session: {response.status_code}")
        print(response.json())
        return
    
    session = response.json()
    session_id = session["session_id"]
    print(f"✅ Created session: {session_id}")
    print(f"   Tool set: {session['tool_set']}")
    print(f"   User: {session['user_id']}")
    
    # 2. Execute queries
    print("\n2. Executing queries...")
    
    queries = [
        "Show me all my delivered orders",
        "Find gaming keyboards under $200",
        "Add the cheapest gaming keyboard to my cart"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n   Query {i}: {query}")
        query_data = {
            "query": query,
            "max_iterations": 5
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/query",
            json=query_data
        )
        
        if response.status_code == 200:
            result = response.json()
            elapsed = time.time() - start_time
            
            print(f"   ✅ Query completed in {elapsed:.2f}s")
            print(f"      Iterations: {result['iterations']}")
            print(f"      Tools used: {', '.join(result['tools_used']) if result['tools_used'] else 'None'}")
            print(f"      Answer: {result['answer'][:200]}...")
        else:
            print(f"   ❌ Query failed: {response.status_code}")
            print(f"      {response.json()}")
    
    # 3. Get session info
    print("\n3. Getting session info...")
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    
    if response.status_code == 200:
        session = response.json()
        print(f"✅ Session info retrieved")
        print(f"   Conversation turns: {session['conversation_turns']}")
        print(f"   Status: {session['status']}")
    else:
        print(f"❌ Failed to get session: {response.status_code}")
    
    # 4. Reset session
    print("\n4. Resetting session...")
    response = requests.post(f"{BASE_URL}/sessions/{session_id}/reset")
    
    if response.status_code == 200:
        print(f"✅ Session reset successfully")
    else:
        print(f"❌ Failed to reset session: {response.status_code}")
    
    # 5. Delete session
    print("\n5. Deleting session...")
    response = requests.delete(f"{BASE_URL}/sessions/{session_id}")
    
    if response.status_code == 204:
        print(f"✅ Session deleted successfully")
    else:
        print(f"❌ Failed to delete session: {response.status_code}")


def test_metrics():
    """Test metrics endpoint."""
    print("\n=== Testing Metrics Endpoint ===")
    response = requests.get(f"{BASE_URL}/metrics")
    
    if response.status_code == 200:
        metrics = response.json()
        print(f"✅ Metrics retrieved")
        print(f"   Total requests: {metrics['total_requests']}")
        print(f"   Total queries: {metrics['total_queries']}")
        print(f"   Active sessions: {metrics['active_sessions']}")
        print(f"   Avg query time: {metrics['average_query_time']:.2f}s")
    else:
        print(f"❌ Failed to get metrics: {response.status_code}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Agentic Loop API Test Suite")
    print("=" * 60)
    print(f"Testing API at: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/", timeout=2)
        if response.status_code != 200:
            print("\n❌ API server not responding correctly")
            return
    except requests.exceptions.RequestException:
        print("\n❌ Cannot connect to API server")
        print("   Please start the server with: uvicorn api.main:app")
        return
    
    # Run tests
    test_health()
    test_tool_sets()
    test_session_workflow()
    test_metrics()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()