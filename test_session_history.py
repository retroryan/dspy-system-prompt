#!/usr/bin/env python3
"""
Test that session history is properly maintained with new pattern.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agentic_loop.session import AgentSession
from shared import setup_llm

def test_session_history():
    """Test that conversation history is maintained across queries."""
    print("=" * 60)
    print("Testing Session History Maintenance")
    print("=" * 60)
    
    # Setup LLM
    setup_llm()
    
    # Create session
    session = AgentSession(
        tool_set_name="ecommerce",
        user_id="test_history_user"
    )
    
    print(f"\n✓ Session created")
    print(f"  User ID: {session.user_id}")
    print(f"  Session ID: {session.session_id}")
    
    # Query 1
    print("\n" + "-" * 60)
    print("Query 1: Searching for products")
    result1 = session.query("Find laptops under $1000", max_iterations=3)
    print(f"✓ Query 1 completed")
    print(f"  Tools used: {result1.tools_used}")
    print(f"  Had context: {result1.had_context}")
    print(f"  Conversation turn: {result1.conversation_turn}")
    
    # Check history
    print(f"\n✓ History after Query 1:")
    print(f"  Total trajectories: {session.history.total_trajectories_processed}")
    print(f"  Current window size: {len(session.history.trajectories)}")
    
    # Query 2 (should have context from Query 1)
    print("\n" + "-" * 60)
    print("Query 2: Follow-up question")
    result2 = session.query("Add the cheapest one to my cart", max_iterations=3)
    print(f"✓ Query 2 completed")
    print(f"  Tools used: {result2.tools_used}")
    print(f"  Had context: {result2.had_context}")
    print(f"  Conversation turn: {result2.conversation_turn}")
    
    # Check history again
    print(f"\n✓ History after Query 2:")
    print(f"  Total trajectories: {session.history.total_trajectories_processed}")
    print(f"  Current window size: {len(session.history.trajectories)}")
    
    # Query 3 (should have context from both previous queries)
    print("\n" + "-" * 60)
    print("Query 3: Another follow-up")
    result3 = session.query("What's in my cart now?", max_iterations=3)
    print(f"✓ Query 3 completed")
    print(f"  Tools used: {result3.tools_used}")
    print(f"  Had context: {result3.had_context}")
    print(f"  Conversation turn: {result3.conversation_turn}")
    
    # Final history check
    print(f"\n✓ Final History State:")
    print(f"  Total trajectories: {session.history.total_trajectories_processed}")
    print(f"  Current window size: {len(session.history.trajectories)}")
    
    # Verify session consistency
    print("\n" + "=" * 60)
    print("Session History Validation")
    print("=" * 60)
    
    # Check that conversation turns match expectations
    assert result1.conversation_turn == 1, "First query should be turn 1"
    assert result2.conversation_turn == 2, "Second query should be turn 2"
    assert result3.conversation_turn == 3, "Third query should be turn 3"
    
    # Check that context builds up
    assert not result1.had_context, "First query should have no context"
    assert result2.had_context, "Second query should have context"
    assert result3.had_context, "Third query should have context"
    
    # Check that session remains consistent
    assert session.user_id == "test_history_user", "User ID should remain consistent"
    assert session.history.total_trajectories_processed == 3, "Should have 3 trajectories"
    
    print("✅ All validations passed!")
    print("  - Conversation turns increment correctly")
    print("  - Context builds up across queries")
    print("  - Session maintains user identity")
    print("  - History tracks all trajectories")
    
    return True

if __name__ == "__main__":
    success = test_session_history()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SESSION HISTORY TEST PASSED")
        print("   Session pattern correctly maintains conversation history")
    else:
        print("❌ SESSION HISTORY TEST FAILED")
    print("=" * 60)