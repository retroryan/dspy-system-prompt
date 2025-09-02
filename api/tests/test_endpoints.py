"""
Comprehensive tests for API endpoints.

Tests all endpoints for correct behavior, error handling, and response formats.
"""

import pytest
import requests
import json
import time
from typing import Dict, Any
from datetime import datetime


class TestHealthEndpoints:
    """Test health and metrics endpoints."""
    
    def test_health_endpoint(self, api_url):
        """Test health check returns correct format."""
        response = requests.get(f"{api_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "active_sessions" in data
        assert data["status"] == "healthy"
    
    def test_metrics_endpoint(self, api_url):
        """Test metrics endpoint returns correct format."""
        response = requests.get(f"{api_url}/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_requests" in data
        assert "total_queries" in data
        assert "active_sessions" in data
        assert "average_query_time" in data
        assert "uptime_seconds" in data
    
    def test_root_endpoint(self, api_url):
        """Test root endpoint provides navigation info."""
        response = requests.get(f"{api_url}/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
        assert "quick_start" in data


class TestToolSetEndpoints:
    """Test tool set discovery endpoints."""
    
    def test_list_tool_sets(self, api_url):
        """Test listing all tool sets."""
        response = requests.get(f"{api_url}/tool-sets")
        assert response.status_code == 200
        
        tool_sets = response.json()
        assert isinstance(tool_sets, list)
        assert len(tool_sets) == 3
        
        names = [ts["name"] for ts in tool_sets]
        assert "agriculture" in names
        assert "ecommerce" in names
        assert "events" in names
    
    def test_get_specific_tool_set(self, api_url):
        """Test getting specific tool set details."""
        for tool_set_name in ["agriculture", "ecommerce", "events"]:
            response = requests.get(f"{api_url}/tool-sets/{tool_set_name}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["name"] == tool_set_name
            assert "description" in data
            assert "tools" in data
            assert "example_queries" in data
            assert isinstance(data["tools"], list)
            assert len(data["tools"]) > 0
    
    def test_invalid_tool_set(self, api_url):
        """Test error for invalid tool set."""
        response = requests.get(f"{api_url}/tool-sets/invalid")
        assert response.status_code == 404
        
        error = response.json()
        assert "error" in error
        assert error["error"]["code"] == "TOOL_SET_NOT_FOUND"


class TestSessionEndpoints:
    """Test session management endpoints."""
    
    def test_create_session(self, api_url):
        """Test session creation."""
        data = {
            "tool_set": "ecommerce",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{api_url}/sessions", json=data)
        assert response.status_code == 201
        
        session = response.json()
        assert "session_id" in session
        assert session["tool_set"] == "ecommerce"
        assert session["user_id"] == "test_user"
        assert session["status"] == "active"
        assert "created_at" in session
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session['session_id']}")
    
    def test_create_session_with_config(self, api_url):
        """Test session creation with custom config."""
        data = {
            "tool_set": "agriculture",
            "user_id": "test_user",
            "config": {
                "max_messages": 100,
                "summarize_removed": False
            }
        }
        
        response = requests.post(f"{api_url}/sessions", json=data)
        assert response.status_code == 201
        
        session = response.json()
        assert session["tool_set"] == "agriculture"
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session['session_id']}")
    
    def test_get_session(self, api_url):
        """Test getting session information."""
        # Create session
        session_id = create_test_session(api_url)
        
        # Get session
        response = requests.get(f"{api_url}/sessions/{session_id}")
        assert response.status_code == 200
        
        session = response.json()
        assert session["session_id"] == session_id
        assert session["status"] == "active"
        assert session["conversation_turns"] == 0
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")
    
    def test_delete_session(self, api_url):
        """Test session deletion."""
        # Create session
        session_id = create_test_session(api_url)
        
        # Delete session
        response = requests.delete(f"{api_url}/sessions/{session_id}")
        assert response.status_code == 204
        
        # Verify deleted
        response = requests.get(f"{api_url}/sessions/{session_id}")
        assert response.status_code == 404
    
    def test_reset_session(self, api_url):
        """Test session reset."""
        # Create session and execute query
        session_id = create_test_session(api_url)
        execute_test_query(api_url, session_id, "Test query")
        
        # Reset session
        response = requests.post(f"{api_url}/sessions/{session_id}/reset")
        assert response.status_code == 200
        
        session = response.json()
        assert session["conversation_turns"] == 0
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")
    
    def test_session_not_found(self, api_url):
        """Test error for non-existent session."""
        response = requests.get(f"{api_url}/sessions/non-existent-id")
        assert response.status_code == 404
        
        error = response.json()
        assert error["error"]["code"] == "SESSION_NOT_FOUND"
    
    def test_invalid_tool_set_creation(self, api_url):
        """Test error for invalid tool set in session creation."""
        data = {
            "tool_set": "invalid",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{api_url}/sessions", json=data)
        assert response.status_code == 404
        
        error = response.json()
        assert error["error"]["code"] == "TOOL_SET_NOT_FOUND"


class TestQueryEndpoints:
    """Test query execution endpoints."""
    
    def test_execute_query(self, api_url):
        """Test basic query execution."""
        # Create session
        session_id = create_test_session(api_url, "ecommerce")
        
        # Execute query
        data = {
            "query": "Show me my orders"
        }
        
        response = requests.post(
            f"{api_url}/sessions/{session_id}/query",
            json=data
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "answer" in result
        assert "execution_time" in result
        assert "iterations" in result
        assert "tools_used" in result
        assert "conversation_turn" in result
        assert "had_context" in result
        assert result["session_id"] == session_id
        assert result["conversation_turn"] == 1
        assert result["had_context"] is False
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")
    
    def test_query_with_context(self, api_url):
        """Test query execution with conversation context."""
        # Create session
        session_id = create_test_session(api_url, "ecommerce")
        
        # First query
        data = {"query": "Show me gaming keyboards"}
        response = requests.post(
            f"{api_url}/sessions/{session_id}/query",
            json=data
        )
        assert response.status_code == 200
        first_result = response.json()
        assert first_result["had_context"] is False
        
        # Second query (should have context)
        data = {"query": "Show me the cheapest one"}
        response = requests.post(
            f"{api_url}/sessions/{session_id}/query",
            json=data
        )
        assert response.status_code == 200
        second_result = response.json()
        assert second_result["had_context"] is True
        assert second_result["conversation_turn"] == 2
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")
    
    def test_query_with_max_iterations(self, api_url):
        """Test query with custom max iterations."""
        # Create session
        session_id = create_test_session(api_url)
        
        # Execute query with custom iterations
        data = {
            "query": "Test query",
            "max_iterations": 3
        }
        
        response = requests.post(
            f"{api_url}/sessions/{session_id}/query",
            json=data
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["iterations"] <= 3
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")
    
    def test_empty_query(self, api_url):
        """Test error for empty query."""
        session_id = create_test_session(api_url)
        
        data = {"query": ""}
        response = requests.post(
            f"{api_url}/sessions/{session_id}/query",
            json=data
        )
        assert response.status_code == 400
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")
    
    def test_query_session_not_found(self, api_url):
        """Test error for query with non-existent session."""
        data = {"query": "Test query"}
        response = requests.post(
            f"{api_url}/sessions/non-existent/query",
            json=data
        )
        assert response.status_code == 404


class TestValidation:
    """Test request validation."""
    
    def test_session_creation_validation(self, api_url):
        """Test validation for session creation."""
        # Missing required field
        data = {"user_id": "test"}
        response = requests.post(f"{api_url}/sessions", json=data)
        assert response.status_code == 400
        
        # Invalid config type
        data = {
            "tool_set": "ecommerce",
            "user_id": "test",
            "config": "invalid"
        }
        response = requests.post(f"{api_url}/sessions", json=data)
        assert response.status_code == 400
    
    def test_query_validation(self, api_url):
        """Test validation for query requests."""
        session_id = create_test_session(api_url)
        
        # Query too long
        data = {"query": "x" * 3000}
        response = requests.post(
            f"{api_url}/sessions/{session_id}/query",
            json=data
        )
        assert response.status_code == 400
        
        # Invalid max_iterations
        data = {
            "query": "Test",
            "max_iterations": 100
        }
        response = requests.post(
            f"{api_url}/sessions/{session_id}/query",
            json=data
        )
        assert response.status_code == 400
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")


class TestWorkflows:
    """Test complete workflows."""
    
    def test_ecommerce_workflow(self, api_url):
        """Test complete e-commerce workflow."""
        # Create session
        session_id = create_test_session(api_url, "ecommerce")
        
        # Execute series of queries
        queries = [
            "Show me all orders",
            "Find gaming keyboards",
            "Add the cheapest to cart"
        ]
        
        for i, query in enumerate(queries, 1):
            response = execute_test_query(api_url, session_id, query)
            assert response["conversation_turn"] == i
            if i > 1:
                assert response["had_context"] is True
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")
    
    def test_agriculture_workflow(self, api_url):
        """Test agriculture workflow."""
        # Create session
        session_id = create_test_session(api_url, "agriculture")
        
        # Execute agriculture queries
        queries = [
            "What's the weather forecast?",
            "Should I plant corn?",
            "Check soil conditions"
        ]
        
        for query in queries:
            response = execute_test_query(api_url, session_id, query)
            assert response["answer"] is not None
        
        # Clean up
        requests.delete(f"{api_url}/sessions/{session_id}")


# Helper functions
def create_test_session(api_url: str, tool_set: str = "ecommerce") -> str:
    """Create a test session and return its ID."""
    data = {
        "tool_set": tool_set,
        "user_id": "test_user"
    }
    response = requests.post(f"{api_url}/sessions", json=data)
    return response.json()["session_id"]


def execute_test_query(api_url: str, session_id: str, query: str) -> Dict[str, Any]:
    """Execute a test query and return the result."""
    data = {"query": query}
    response = requests.post(
        f"{api_url}/sessions/{session_id}/query",
        json=data
    )
    return response.json()


# Pytest fixtures
@pytest.fixture
def api_url():
    """Provide API base URL."""
    return "http://localhost:8000"