#!/usr/bin/env python3
"""
Example client for the Agentic Loop API.

This module demonstrates how to interact with the API using Python requests library.
Includes examples for all major operations and error handling.
"""

import requests
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime


class AgenticLoopClient:
    """
    Python client for the Agentic Loop API.
    
    Provides a clean interface for interacting with the API endpoints.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client.
        
        Args:
            base_url: API server base URL
        """
        self.base_url = base_url.rstrip('/')
        self.session_id: Optional[str] = None
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check API health status.
        
        Returns:
            Health status information
        """
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def list_tool_sets(self) -> List[Dict[str, Any]]:
        """
        List all available tool sets.
        
        Returns:
            List of tool set information
        """
        response = requests.get(f"{self.base_url}/tool-sets")
        response.raise_for_status()
        return response.json()
    
    def get_tool_set(self, name: str) -> Dict[str, Any]:
        """
        Get information about a specific tool set.
        
        Args:
            name: Tool set name
            
        Returns:
            Tool set details
        """
        response = requests.get(f"{self.base_url}/tool-sets/{name}")
        response.raise_for_status()
        return response.json()
    
    def create_session(
        self,
        tool_set: str,
        user_id: str,
        max_messages: int = 50,
        summarize_removed: bool = True
    ) -> str:
        """
        Create a new agent session.
        
        Args:
            tool_set: Tool set to use (ecommerce, agriculture, events)
            user_id: User identifier
            max_messages: Max conversation messages to keep
            summarize_removed: Whether to summarize old messages
            
        Returns:
            Session ID
        """
        data = {
            "tool_set": tool_set,
            "user_id": user_id,
            "config": {
                "max_messages": max_messages,
                "summarize_removed": summarize_removed
            }
        }
        
        response = requests.post(f"{self.base_url}/sessions", json=data)
        response.raise_for_status()
        
        result = response.json()
        self.session_id = result["session_id"]
        return self.session_id
    
    def get_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get session information.
        
        Args:
            session_id: Session ID (uses stored ID if not provided)
            
        Returns:
            Session information
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided or stored")
        
        response = requests.get(f"{self.base_url}/sessions/{sid}")
        response.raise_for_status()
        return response.json()
    
    def query(
        self,
        text: str,
        max_iterations: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a query in the session.
        
        Args:
            text: Query text
            max_iterations: Maximum React loop iterations
            session_id: Session ID (uses stored ID if not provided)
            
        Returns:
            Query response with answer and metadata
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided or stored")
        
        data = {
            "query": text,
            "max_iterations": max_iterations
        }
        
        response = requests.post(
            f"{self.base_url}/sessions/{sid}/query",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def reset_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Reset session conversation history.
        
        Args:
            session_id: Session ID (uses stored ID if not provided)
            
        Returns:
            Updated session information
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided or stored")
        
        response = requests.post(f"{self.base_url}/sessions/{sid}/reset")
        response.raise_for_status()
        return response.json()
    
    def delete_session(self, session_id: Optional[str] = None) -> None:
        """
        Delete a session.
        
        Args:
            session_id: Session ID (uses stored ID if not provided)
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided or stored")
        
        response = requests.delete(f"{self.base_url}/sessions/{sid}")
        response.raise_for_status()
        
        if sid == self.session_id:
            self.session_id = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get server metrics.
        
        Returns:
            Server metrics information
        """
        response = requests.get(f"{self.base_url}/metrics")
        response.raise_for_status()
        return response.json()


def example_basic_workflow():
    """Demonstrate basic API workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Basic Workflow")
    print("=" * 60)
    
    # Initialize client
    client = AgenticLoopClient()
    
    # Check health
    health = client.check_health()
    print(f"\n✓ Server Status: {health['status']}")
    print(f"  Version: {health['version']}")
    
    # List tool sets
    tool_sets = client.list_tool_sets()
    print(f"\n✓ Available Tool Sets: {len(tool_sets)}")
    for ts in tool_sets:
        print(f"  - {ts['name']}: {len(ts['tools'])} tools")
    
    # Create session
    session_id = client.create_session(
        tool_set="ecommerce",
        user_id="demo_user"
    )
    print(f"\n✓ Created Session: {session_id}")
    
    # Execute query
    result = client.query("Show me my recent orders")
    print(f"\n✓ Query executed in {result['execution_time']:.2f}s")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Tools used: {', '.join(result['tools_used'])}")
    print(f"  Answer: {result['answer'][:100]}...")
    
    # Clean up
    client.delete_session()
    print("\n✓ Session deleted")


def example_conversation_flow():
    """Demonstrate multi-turn conversation with context."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Multi-turn Conversation")
    print("=" * 60)
    
    client = AgenticLoopClient()
    
    # Create e-commerce session
    session_id = client.create_session(
        tool_set="ecommerce",
        user_id="power_user",
        max_messages=30
    )
    print(f"\n✓ Session created: {session_id}")
    
    # Conversation queries that build on each other
    queries = [
        "What gaming keyboards do you have under $150?",
        "Compare the top 3 options you found",
        "Add the one with the best reviews to my cart",
        "What's my cart total now?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n→ Query {i}: {query}")
        
        try:
            result = client.query(query)
            print(f"  ✓ Completed in {result['execution_time']:.2f}s")
            print(f"    Context available: {result['had_context']}")
            print(f"    Answer preview: {result['answer'][:80]}...")
            
            # Small delay between queries
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Check final session state
    session_info = client.get_session()
    print(f"\n✓ Final conversation turns: {session_info['conversation_turns']}")
    
    # Clean up
    client.delete_session()


def example_error_handling():
    """Demonstrate error handling patterns."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Error Handling")
    print("=" * 60)
    
    client = AgenticLoopClient()
    
    # Try invalid tool set
    print("\n→ Testing invalid tool set...")
    try:
        client.create_session(
            tool_set="invalid_toolset",
            user_id="test_user"
        )
    except requests.HTTPError as e:
        error_data = e.response.json()
        print(f"  ✓ Caught expected error: {error_data['error']['code']}")
        print(f"    Message: {error_data['error']['message']}")
    
    # Try querying without session
    print("\n→ Testing query without session...")
    try:
        client.session_id = None
        client.query("Test query")
    except ValueError as e:
        print(f"  ✓ Caught expected error: {e}")
    
    # Try accessing non-existent session
    print("\n→ Testing non-existent session...")
    try:
        client.get_session("non-existent-session-id")
    except requests.HTTPError as e:
        error_data = e.response.json()
        print(f"  ✓ Caught expected error: {error_data['error']['code']}")


def example_agriculture_workflow():
    """Demonstrate agriculture tool set workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE: Agriculture Workflow")
    print("=" * 60)
    
    client = AgenticLoopClient()
    
    # Create agriculture session
    session_id = client.create_session(
        tool_set="agriculture",
        user_id="farmer_john"
    )
    print(f"\n✓ Agriculture session created: {session_id}")
    
    # Agriculture-specific queries
    queries = [
        "What's the weather forecast for the next week?",
        "Based on the weather, should I plant corn or wheat?",
        "Check the soil conditions for my north field",
        "Create an irrigation schedule for this week"
    ]
    
    for query in queries:
        print(f"\n→ {query}")
        result = client.query(query)
        print(f"  ✓ {result['answer'][:100]}...")
    
    # Get metrics
    metrics = client.get_metrics()
    print(f"\n✓ Total queries processed: {metrics['total_queries']}")
    
    # Clean up
    client.delete_session()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" " * 20 + "AGENTIC LOOP API CLIENT EXAMPLES")
    print("=" * 70)
    print("\nMake sure the API server is running at http://localhost:8000")
    print("Start it with: ./run_api.sh")
    
    try:
        # Check if server is available
        client = AgenticLoopClient()
        client.check_health()
    except Exception as e:
        print(f"\n✗ Cannot connect to API server: {e}")
        print("  Please start the server first.")
        return
    
    # Run examples
    example_basic_workflow()
    example_conversation_flow()
    example_error_handling()
    example_agriculture_workflow()
    
    print("\n" + "=" * 70)
    print(" " * 25 + "ALL EXAMPLES COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()