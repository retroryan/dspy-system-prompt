"""
Pytest configuration for integration tests.

Provides fixtures and utilities for integration testing.
"""

import pytest
import requests
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def api_server():
    """
    Verify API server is running.
    
    Integration tests require a running server.
    """
    max_retries = 5
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"\n✓ API server is running at {BASE_URL}")
                return BASE_URL
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                print(f"\n⏳ Waiting for API server... ({i+1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                pytest.fail(
                    f"\n❌ API server not available at {BASE_URL}\n"
                    "   Please start the server with: ./run_api.sh"
                )


@pytest.fixture
def create_session(api_server):
    """
    Factory fixture to create test sessions.
    
    Returns a function that creates sessions and tracks them for cleanup.
    """
    sessions = []
    
    def _create_session(tool_set="ecommerce", user_id=None, config=None):
        """Create a session and track it for cleanup."""
        if user_id is None:
            user_id = f"integration_test_{time.time()}"
        
        data = {
            "tool_set": tool_set,
            "user_id": user_id
        }
        if config:
            data["config"] = config
        
        response = requests.post(f"{BASE_URL}/sessions", json=data)
        assert response.status_code == 201
        session_id = response.json()["session_id"]
        sessions.append(session_id)
        return session_id
    
    yield _create_session
    
    # Cleanup all created sessions
    for session_id in sessions:
        try:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")
        except:
            pass


@pytest.fixture
def execute_query():
    """
    Factory fixture to execute queries.
    
    Returns a function that executes queries and returns results.
    """
    def _execute_query(session_id, query, max_iterations=None):
        """Execute a query and return the result."""
        data = {"query": query}
        if max_iterations:
            data["max_iterations"] = max_iterations
        
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/query",
            json=data
        )
        assert response.status_code == 200
        return response.json()
    
    return _execute_query


@pytest.fixture(autouse=True)
def cleanup_test_sessions():
    """
    Clean up any lingering test sessions after each test.
    
    This helps prevent test pollution.
    """
    yield
    
    # Clean up sessions created by integration tests
    try:
        # Get all sessions for test users
        test_user_prefixes = ["integration_test_", "test_"]
        
        # Note: This would require an endpoint to list all sessions
        # For now, we rely on individual test cleanup
        pass
    except:
        pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers", "workflow: marks tests as workflow tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )