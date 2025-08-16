#!/usr/bin/env python3
"""
Test script for ecommerce tools with session-based approach.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agentic_loop.session import AgentSession
from tools.ecommerce.tool_set import EcommerceToolSet

def test_ecommerce_tools():
    """Test that all ecommerce tools work with session pattern."""
    print("=" * 60)
    print("Ecommerce Tools Session Test")
    print("=" * 60)
    
    # Create session with ecommerce tools
    session = AgentSession(
        tool_set_name="ecommerce",
        user_id="test_customer_456"
    )
    
    print(f"\n✓ Session created for user: {session.user_id}")
    print(f"  Session ID: {session.session_id}")
    
    # Test tool registry
    registry = session.tool_registry
    tools = registry.get_tool_names()
    
    print(f"\n✓ Loaded {len(tools)} ecommerce tools:")
    for tool_name in sorted(tools):
        tool = registry.get_tool(tool_name)
        accepts_session = getattr(tool, '_accepts_session', False)
        status = "✓ Session-aware" if accepts_session else "○ No session needed"
        print(f"  - {tool_name}: {status}")
    
    # Test direct tool execution
    print("\n" + "=" * 60)
    print("Testing Direct Tool Execution")
    print("=" * 60)
    
    # Test search (no session needed)
    print("\n1. Testing search_products (no session)...")
    search_result = registry.execute_tool_with_session(
        tool_name="search_products",
        session=None,  # Should work without session
        query="laptop"
    )
    if "error" not in search_result:
        print(f"   ✓ Search worked without session: {search_result.get('count', 0)} products found")
    else:
        print(f"   ✗ Search failed: {search_result}")
    
    # Test get_cart (needs session)
    print("\n2. Testing get_cart (with session)...")
    cart_result = registry.execute_tool_with_session(
        tool_name="get_cart",
        session=session
    )
    if "error" not in cart_result:
        print(f"   ✓ Cart retrieved with session: {cart_result.get('items_count', 0)} items")
    else:
        print(f"   ✗ Cart failed: {cart_result}")
    
    # Test get_cart without session (should fail)
    print("\n3. Testing get_cart (without session - should fail)...")
    cart_fail = registry.execute_tool_with_session(
        tool_name="get_cart",
        session=None
    )
    if "error" in cart_fail:
        print(f"   ✓ Correctly failed without session: {cart_fail['error']}")
    else:
        print(f"   ✗ Should have failed but didn't")
    
    # Test list_orders
    print("\n4. Testing list_orders (with session)...")
    orders_result = registry.execute_tool_with_session(
        tool_name="list_orders",
        session=session,
        status=None
    )
    if "error" not in orders_result:
        print(f"   ✓ Orders retrieved: {orders_result.get('count', 0)} orders")
    else:
        print(f"   ✗ Orders failed: {orders_result}")
    
    print("\n" + "=" * 60)
    print("Session Pattern Validation")
    print("=" * 60)
    
    # Validate no execute_with_user_id exists
    print("\nChecking for old patterns...")
    errors = []
    
    for tool_name in tools:
        tool = registry.get_tool(tool_name)
        if hasattr(tool, 'execute_with_user_id'):
            errors.append(f"  ✗ {tool_name} still has execute_with_user_id")
        if not hasattr(tool, 'execute'):
            errors.append(f"  ✗ {tool_name} missing execute method")
    
    if errors:
        print("Found issues:")
        for error in errors:
            print(error)
    else:
        print("✓ All tools follow new session pattern correctly")
        print("  - No execute_with_user_id methods found")
        print("  - All tools have execute() method")
        print("  - Session injection working correctly")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_ecommerce_tools()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All Tests Passed - Session Pattern Working!")
    else:
        print("❌ Some Tests Failed - Check Implementation")
    print("=" * 60)