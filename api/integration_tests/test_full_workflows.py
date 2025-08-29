"""
Full workflow integration tests against running API server.

These tests verify complete end-to-end scenarios with the actual API.
"""

import pytest
import requests
import time
import json
from typing import Dict, Any, List
from datetime import datetime


BASE_URL = "http://localhost:8000"


class TestEcommerceWorkflow:
    """Test complete e-commerce shopping workflows."""
    
    def test_shopping_journey(self):
        """Test a complete shopping journey from browsing to checkout."""
        # Create session
        session_data = {
            "tool_set": "ecommerce",
            "user_id": "integration_test_shopper"
        }
        
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        assert response.status_code == 201
        session = response.json()
        session_id = session["session_id"]
        
        try:
            # Step 1: Browse orders
            query_data = {"query": "Show me all my delivered orders"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["conversation_turn"] == 1
            assert not result["had_context"]
            assert "GetOrders" in result["tools_used"] or len(result["tools_used"]) > 0
            
            # Step 2: Search for products
            query_data = {"query": "Find gaming keyboards under $150 with good reviews"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["conversation_turn"] == 2
            assert result["had_context"]
            
            # Step 3: Add to cart (references previous search)
            query_data = {"query": "Add the cheapest one to my cart"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["conversation_turn"] == 3
            assert result["had_context"]
            
            # Step 4: Review cart
            query_data = {"query": "What's in my cart and what's the total?"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["conversation_turn"] == 4
            
            # Step 5: Checkout
            query_data = {"query": "Complete checkout with standard shipping"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["conversation_turn"] == 5
            assert "Checkout" in result["tools_used"] or "checkout" in result["answer"].lower()
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/sessions/{session_id}")
    
    def test_return_process_workflow(self):
        """Test product return workflow."""
        # Create session
        session_data = {
            "tool_set": "ecommerce",
            "user_id": "integration_test_returner"
        }
        
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        assert response.status_code == 201
        session_id = response.json()["session_id"]
        
        try:
            # Step 1: Check order history
            query_data = {"query": "Show me my recent orders from the last month"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            
            # Step 2: Inquire about return
            query_data = {"query": "Can I return items from my most recent order?"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"]
            
            # Step 3: Process return
            query_data = {"query": "Process a return for the most expensive item"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert "ProcessReturn" in result["tools_used"] or "return" in result["answer"].lower()
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")


class TestAgricultureWorkflow:
    """Test agriculture decision-making workflows."""
    
    def test_planting_decision_workflow(self):
        """Test complete planting decision workflow."""
        # Create session
        session_data = {
            "tool_set": "agriculture",
            "user_id": "integration_test_farmer"
        }
        
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        assert response.status_code == 201
        session_id = response.json()["session_id"]
        
        try:
            # Step 1: Check weather
            query_data = {"query": "What's the weather forecast for the next 10 days?"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert "GetWeather" in result["tools_used"] or "weather" in result["answer"].lower()
            
            # Step 2: Check soil conditions
            query_data = {"query": "What are the soil conditions in my north field?"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"]
            
            # Step 3: Get planting recommendations
            query_data = {"query": "Based on the weather and soil, should I plant corn or wheat?"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"]
            assert "GetCropRecommendations" in result["tools_used"] or "recommendation" in result["answer"].lower()
            
            # Step 4: Create irrigation schedule
            query_data = {"query": "Create an irrigation schedule for the crop you recommended"}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"]
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")


class TestSessionManagement:
    """Test session lifecycle and management."""
    
    def test_session_lifecycle(self):
        """Test complete session lifecycle."""
        # Create session
        session_data = {
            "tool_set": "events",
            "user_id": "integration_test_lifecycle",
            "config": {
                "max_messages": 20,
                "summarize_removed": True
            }
        }
        
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        assert response.status_code == 201
        session = response.json()
        session_id = session["session_id"]
        assert session["status"] == "active"
        assert session["conversation_turns"] == 0
        
        # Execute query
        query_data = {"query": "What events are happening this weekend?"}
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/query",
            json=query_data
        )
        assert response.status_code == 200
        
        # Get session info
        response = requests.get(f"{BASE_URL}/sessions/{session_id}")
        assert response.status_code == 200
        session = response.json()
        assert session["conversation_turns"] == 1
        
        # Reset session
        response = requests.post(f"{BASE_URL}/sessions/{session_id}/reset")
        assert response.status_code == 200
        session = response.json()
        assert session["conversation_turns"] == 0
        
        # Delete session
        response = requests.delete(f"{BASE_URL}/sessions/{session_id}")
        assert response.status_code == 204
        
        # Verify deleted
        response = requests.get(f"{BASE_URL}/sessions/{session_id}")
        assert response.status_code == 404
    
    def test_concurrent_sessions(self):
        """Test multiple concurrent sessions."""
        session_ids = []
        
        try:
            # Create multiple sessions
            for i in range(3):
                session_data = {
                    "tool_set": "ecommerce",
                    "user_id": f"integration_test_concurrent_{i}"
                }
                response = requests.post(f"{BASE_URL}/sessions", json=session_data)
                assert response.status_code == 201
                session_ids.append(response.json()["session_id"])
            
            # Execute queries on all sessions
            for i, session_id in enumerate(session_ids):
                query_data = {"query": f"Show me product {i}"}
                response = requests.post(
                    f"{BASE_URL}/sessions/{session_id}/query",
                    json=query_data
                )
                assert response.status_code == 200
            
            # Verify all sessions are active
            for session_id in session_ids:
                response = requests.get(f"{BASE_URL}/sessions/{session_id}")
                assert response.status_code == 200
                assert response.json()["status"] == "active"
            
        finally:
            # Cleanup all sessions
            for session_id in session_ids:
                requests.delete(f"{BASE_URL}/sessions/{session_id}")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_tool_set(self):
        """Test error handling for invalid tool set."""
        session_data = {
            "tool_set": "invalid_toolset",
            "user_id": "integration_test_error"
        }
        
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        assert response.status_code == 404
        error = response.json()
        assert error["error"]["code"] == "TOOL_SET_NOT_FOUND"
    
    def test_query_without_session(self):
        """Test querying with non-existent session."""
        query_data = {"query": "Test query"}
        response = requests.post(
            f"{BASE_URL}/sessions/non-existent-session/query",
            json=query_data
        )
        assert response.status_code == 404
        error = response.json()
        assert error["error"]["code"] == "SESSION_NOT_FOUND"
    
    def test_invalid_query_parameters(self):
        """Test validation of query parameters."""
        # Create valid session first
        session_data = {
            "tool_set": "ecommerce",
            "user_id": "integration_test_validation"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # Empty query
            query_data = {"query": ""}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 400
            
            # Query too long
            query_data = {"query": "x" * 3000}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 400
            
            # Invalid max_iterations
            query_data = {
                "query": "Test",
                "max_iterations": 100
            }
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            assert response.status_code == 400
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")


class TestAPIEndpoints:
    """Test various API endpoints."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = requests.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "total_queries" in data
        assert "active_sessions" in data
        assert "average_query_time" in data
        assert "uptime_seconds" in data
    
    def test_tool_sets_endpoint(self):
        """Test tool sets discovery."""
        response = requests.get(f"{BASE_URL}/tool-sets")
        assert response.status_code == 200
        tool_sets = response.json()
        assert len(tool_sets) == 3
        
        names = [ts["name"] for ts in tool_sets]
        assert "agriculture" in names
        assert "ecommerce" in names
        assert "events" in names
        
        # Test specific tool set
        for name in names:
            response = requests.get(f"{BASE_URL}/tool-sets/{name}")
            assert response.status_code == 200
            tool_set = response.json()
            assert tool_set["name"] == name
            assert len(tool_set["tools"]) > 0
            assert len(tool_set["example_queries"]) > 0
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
        assert "quick_start" in data


class TestPerformance:
    """Test performance and response times."""
    
    def test_query_response_time(self):
        """Test that queries complete within reasonable time."""
        # Create session
        session_data = {
            "tool_set": "ecommerce",
            "user_id": "integration_test_performance"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # Simple query should complete quickly
            start_time = time.time()
            query_data = {"query": "Show me my orders", "max_iterations": 3}
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json=query_data
            )
            elapsed = time.time() - start_time
            
            assert response.status_code == 200
            assert elapsed < 10  # Should complete within 10 seconds
            
            result = response.json()
            assert result["execution_time"] < 10
            assert result["iterations"] <= 3
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")
    
    def test_session_creation_performance(self):
        """Test session creation is fast."""
        start_time = time.time()
        
        session_data = {
            "tool_set": "agriculture",
            "user_id": "integration_test_perf_create"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        elapsed = time.time() - start_time
        
        assert response.status_code == 201
        assert elapsed < 2  # Session creation should be under 2 seconds
        
        # Cleanup
        session_id = response.json()["session_id"]
        requests.delete(f"{BASE_URL}/sessions/{session_id}")