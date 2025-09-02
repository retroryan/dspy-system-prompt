"""
Pytest configuration for API tests.

Provides fixtures and setup for testing.
"""

import pytest
import requests
import time
import subprocess
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture(scope="session")
def api_server():
    """
    Start API server for testing if not already running.
    
    Note: For CI/CD, the server should be started externally.
    This fixture checks if the server is running and provides info.
    """
    api_url = "http://localhost:8000"
    
    # Check if server is already running
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code == 200:
            print("\n✓ API server already running")
            yield api_url
            return
    except requests.exceptions.RequestException:
        pass
    
    # Server not running - inform user
    print("\n⚠️  API server not running")
    print("   Please start the server in another terminal:")
    print("   ./run_api.sh")
    pytest.skip("API server not available")


@pytest.fixture(autouse=True)
def cleanup_sessions(api_url):
    """
    Clean up any test sessions after each test.
    
    This ensures tests don't interfere with each other.
    """
    yield
    
    # Clean up any sessions created by test user
    try:
        response = requests.get(f"{api_url}/sessions/user/test_user")
        if response.status_code == 200:
            sessions = response.json()
            for session in sessions:
                requests.delete(f"{api_url}/sessions/{session['session_id']}")
    except:
        pass  # Ignore cleanup errors


@pytest.fixture
def api_url():
    """Provide API base URL."""
    return "http://localhost:8000"


@pytest.fixture
def test_session(api_url):
    """
    Create a test session that's automatically cleaned up.
    
    Returns session ID.
    """
    data = {
        "tool_set": "ecommerce",
        "user_id": "test_user"
    }
    
    response = requests.post(f"{api_url}/sessions", json=data)
    session_id = response.json()["session_id"]
    
    yield session_id
    
    # Cleanup
    try:
        requests.delete(f"{api_url}/sessions/{session_id}")
    except:
        pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add integration marker to workflow tests
        if "workflow" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to certain tests
        if "workflow" in item.nodeid.lower() or "timeout" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)