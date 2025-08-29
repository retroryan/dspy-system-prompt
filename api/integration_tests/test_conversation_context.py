"""
Test conversation context and memory management.

These tests verify that the API correctly maintains conversation context
across multiple queries within a session.
"""

import pytest
import requests
import time
from typing import List, Dict, Any


BASE_URL = "http://localhost:8000"


class TestConversationContext:
    """Test conversation context preservation."""
    
    def test_context_building(self):
        """Test that context builds across queries."""
        # Create session
        session_data = {
            "tool_set": "ecommerce",
            "user_id": "integration_test_context"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # First query - no context
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Show me laptops"}
            )
            assert response.status_code == 200
            result1 = response.json()
            assert result1["had_context"] is False
            assert result1["conversation_turn"] == 1
            
            # Second query - should have context
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "What about gaming ones?"}
            )
            assert response.status_code == 200
            result2 = response.json()
            assert result2["had_context"] is True
            assert result2["conversation_turn"] == 2
            
            # Third query - referencing earlier context
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Show me the cheapest option from the gaming laptops"}
            )
            assert response.status_code == 200
            result3 = response.json()
            assert result3["had_context"] is True
            assert result3["conversation_turn"] == 3
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")
    
    def test_pronoun_resolution(self):
        """Test that pronouns are resolved using context."""
        session_data = {
            "tool_set": "ecommerce",
            "user_id": "integration_test_pronouns"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # Establish context with specific product
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Find the best gaming keyboard"}
            )
            assert response.status_code == 200
            
            # Use pronoun to reference it
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Add it to my cart"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is True
            assert "AddToCart" in result["tools_used"] or "cart" in result["answer"].lower()
            
            # Continue referencing
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "What's the price of that item?"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is True
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")
    
    def test_session_reset_clears_context(self):
        """Test that resetting session clears conversation context."""
        session_data = {
            "tool_set": "agriculture",
            "user_id": "integration_test_reset"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # Build some context
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "What's the weather like?"}
            )
            assert response.status_code == 200
            
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Should I plant based on that weather?"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is True
            assert result["conversation_turn"] == 2
            
            # Reset session
            response = requests.post(f"{BASE_URL}/sessions/{session_id}/reset")
            assert response.status_code == 200
            
            # Next query should have no context
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "What crops grow well here?"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is False
            assert result["conversation_turn"] == 1
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")


class TestMemoryManagement:
    """Test conversation memory management."""
    
    def test_long_conversation(self):
        """Test handling of long conversations."""
        session_data = {
            "tool_set": "ecommerce",
            "user_id": "integration_test_long_conv",
            "config": {
                "max_messages": 10,  # Small limit to test summarization
                "summarize_removed": True
            }
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # Execute many queries to exceed max_messages
            queries = [
                "Show me all orders",
                "Filter for delivered ones",
                "What products did I buy most?",
                "Show me electronics",
                "Filter for laptops",
                "Show gaming laptops",
                "What's the price range?",
                "Show under $1000",
                "Add the cheapest to cart",
                "What's in my cart?",
                "Remove that item",
                "Add a different laptop",
                "Show cart total",
                "Apply discount code",
                "Proceed to checkout"
            ]
            
            for i, query in enumerate(queries):
                response = requests.post(
                    f"{BASE_URL}/sessions/{session_id}/query",
                    json={"query": query}
                )
                assert response.status_code == 200
                result = response.json()
                assert result["conversation_turn"] == i + 1
                
                # After first query, should have context
                if i > 0:
                    assert result["had_context"] is True
            
            # Verify session still works after many queries
            response = requests.get(f"{BASE_URL}/sessions/{session_id}")
            assert response.status_code == 200
            session = response.json()
            assert session["conversation_turns"] == len(queries)
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")
    
    def test_context_relevance(self):
        """Test that context helps with ambiguous queries."""
        session_data = {
            "tool_set": "events",
            "user_id": "integration_test_relevance"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # Set context about location
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "What tech events are in San Francisco?"}
            )
            assert response.status_code == 200
            
            # Ambiguous query that should use location context
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "What about next month?"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is True
            # Answer should still relate to San Francisco events
            
            # Another ambiguous query
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Register me for the first one"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is True
            assert "RegisterForEvent" in result["tools_used"] or "register" in result["answer"].lower()
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")


class TestCrossQueryState:
    """Test state management across queries."""
    
    def test_cart_state_persistence(self):
        """Test that cart state persists across queries."""
        session_data = {
            "tool_set": "ecommerce",
            "user_id": "integration_test_cart_state"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # Add item to cart
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Add a gaming mouse to my cart"}
            )
            assert response.status_code == 200
            
            # Check cart in new query
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "What's in my shopping cart?"}
            )
            assert response.status_code == 200
            result = response.json()
            assert "GetCart" in result["tools_used"] or "cart" in result["answer"].lower()
            
            # Add another item
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Also add a keyboard"}
            )
            assert response.status_code == 200
            
            # Check updated cart
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Show my cart total"}
            )
            assert response.status_code == 200
            result = response.json()
            # Should mention both items or total
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")
    
    def test_multi_step_workflow_state(self):
        """Test state across multi-step workflows."""
        session_data = {
            "tool_set": "agriculture",
            "user_id": "integration_test_workflow_state"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        session_id = response.json()["session_id"]
        
        try:
            # Step 1: Establish field context
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Analyze conditions for my 50-acre wheat field"}
            )
            assert response.status_code == 200
            
            # Step 2: Reference the field
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "What's the optimal planting density for that field?"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is True
            
            # Step 3: Continue with same field context
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "Create an irrigation schedule for it"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is True
            
            # Step 4: Calculate requirements
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/query",
                json={"query": "How much seed will I need total?"}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["had_context"] is True
            # Should reference the 50-acre field from earlier
            
        finally:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")