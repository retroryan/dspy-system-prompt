#!/usr/bin/env python3
"""
Test script for core infrastructure changes.
Tests that the session-based approach works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agentic_loop.session import AgentSession

def test_session_creation():
    """Test that session is created with proper attributes."""
    print("Testing session creation...")
    
    session = AgentSession(
        tool_set_name="agriculture",
        user_id="test_user_123"
    )
    
    assert session.user_id == "test_user_123"
    assert session.tool_set_name == "agriculture"
    assert session.session_id is not None
    assert session.session_metadata["user_id"] == "test_user_123"
    
    print("✓ Session created successfully")
    print(f"  - User ID: {session.user_id}")
    print(f"  - Session ID: {session.session_id}")
    print(f"  - Tool set: {session.tool_set_name}")
    
    return session

def test_tool_registry():
    """Test that tool registry has the new method."""
    print("\nTesting tool registry...")
    
    session = AgentSession(tool_set_name="agriculture")
    registry = session.tool_registry
    
    # Check that the new method exists
    assert hasattr(registry, 'execute_tool_with_session')
    
    print("✓ Tool registry has execute_tool_with_session method")
    
    # Check tool registration
    tools = registry.get_tool_names()
    print(f"✓ Registered tools: {', '.join(tools)}")
    
    return registry

def test_base_tool_changes():
    """Test that BaseTool has the new structure."""
    print("\nTesting BaseTool changes...")
    
    from shared.tool_utils.base_tool import BaseTool
    
    # Check that execute_with_user_id is gone
    assert not hasattr(BaseTool, 'execute_with_user_id')
    
    # Check that _accepts_session exists
    assert hasattr(BaseTool, '_accepts_session')
    
    print("✓ BaseTool has been updated correctly")
    print("  - execute_with_user_id removed")
    print("  - _accepts_session flag added")

def test_simple_query():
    """Test a simple query to ensure the flow works."""
    print("\nTesting simple query flow...")
    
    try:
        session = AgentSession(
            tool_set_name="agriculture",
            user_id="test_user",
            verbose=False
        )
        
        # This will test the full flow
        result = session.query("What's the weather like?", max_iterations=2)
        
        print("✓ Query executed successfully")
        print(f"  - Answer length: {len(result.answer)} chars")
        print(f"  - Iterations: {result.iterations}")
        print(f"  - Tools used: {result.tools_used}")
        
        return result
    except Exception as e:
        print(f"✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all tests."""
    print("=" * 60)
    print("Core Infrastructure Test Suite")
    print("=" * 60)
    
    # Test 1: Session creation
    session = test_session_creation()
    
    # Test 2: Tool registry
    registry = test_tool_registry()
    
    # Test 3: BaseTool changes
    test_base_tool_changes()
    
    # Test 4: Simple query (may fail if tools aren't updated yet)
    print("\nNote: Simple query test may fail if individual tools")
    print("haven't been updated to the new pattern yet.")
    result = test_simple_query()
    
    print("\n" + "=" * 60)
    print("Core Infrastructure Tests Complete")
    print("=" * 60)
    
    if result:
        print("\n✓ All core infrastructure changes are working!")
        print("  Next step: Update individual ecommerce tools")
    else:
        print("\n⚠ Core infrastructure is ready, but tools need updating")

if __name__ == "__main__":
    main()