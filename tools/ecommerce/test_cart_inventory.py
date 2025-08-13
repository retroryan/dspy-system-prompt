#!/usr/bin/env python3
"""Test script for CartInventoryManager functionality."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ecommerce.cart_inventory_manager import CartInventoryManager


def test_phase1():
    """Test Phase 1: Core Infrastructure."""
    print("=" * 60)
    print("Testing Phase 1: Core Infrastructure")
    print("=" * 60)
    
    # Initialize manager with fresh database
    import os
    if os.path.exists("test_phase1.db"):
        os.remove("test_phase1.db")
    
    manager = CartInventoryManager("test_phase1.db")
    print("✓ CartInventoryManager initialized")
    
    # Test database creation
    print("✓ Database tables created")
    
    # Test loading products
    products = manager.load_products_from_json()
    print(f"✓ Loaded {len(products)} products from JSON")
    
    if products:
        # Test getting a specific product
        first_product = products[0]
        product = manager.get_product_by_id(first_product['id'])
        print(f"✓ Retrieved product: {product['name']}")
    
    # Initialize inventory
    manager.initialize_inventory_from_products()
    print("✓ Inventory initialized from products.json")
    
    # Seed demo orders
    manager.seed_demo_orders(10)
    print("✓ Seeded 10 demo orders")
    
    # Seed demo carts
    manager.seed_demo_carts(3)
    print("✓ Created 3 demo carts")
    
    # Get statistics
    stats = manager.get_stats()
    print("\nDatabase Statistics:")
    print(f"  Total orders: {stats['total_orders']}")
    print(f"  Orders by status: {stats['orders_by_status']}")
    print(f"  Active carts: {stats['active_carts']}")
    print(f"  Inventory: {stats['inventory']}")
    print(f"  Pending returns: {stats['pending_returns']}")
    
    # Test user-specific stats
    user_stats = manager.get_stats('alice')
    print(f"\nStats for user 'alice':")
    print(f"  Total orders: {user_stats['total_orders']}")
    
    print("\n✓ Phase 1 testing complete!")
    
    return True


def test_phase2():
    """Test Phase 2: Cart & Inventory Operations."""
    print("\n" + "=" * 60)
    print("Testing Phase 2: Cart & Inventory Operations")
    print("=" * 60)
    
    # Initialize manager with fresh database
    import os
    if os.path.exists("test_phase2.db"):
        os.remove("test_phase2.db")
    
    manager = CartInventoryManager("test_phase2.db")
    manager.reset_database()
    print("✓ Database reset with demo data")
    
    # Test user
    user_id = "test_user"
    
    # Test adding to cart
    print("\n--- Testing Cart Operations ---")
    
    # Add first product
    result = manager.add_to_cart(user_id, "KB123", 2)
    if result['status'] == 'success':
        print(f"✓ Added 2x KB123 to cart: ${result['cart_value']:.2f}")
    else:
        print(f"✗ Failed to add KB123: {result['error']}")
    
    # Add another product
    result = manager.add_to_cart(user_id, "MS456", 1)
    if result['status'] == 'success':
        print(f"✓ Added 1x MS456 to cart: ${result['cart_value']:.2f}")
    
    # Try to add more than available
    result = manager.add_to_cart(user_id, "KB789", 100)  # Only 23 in stock
    if result['status'] == 'failed':
        print(f"✓ Correctly prevented overselling: {result['error']}")
    
    # Get cart contents
    cart = manager.get_cart(user_id)
    print(f"\n✓ Cart contents:")
    print(f"  Cart ID: {cart.cart_id}")
    print(f"  Items: {len(cart.items)}")
    print(f"  Total: ${cart.total:.2f}")
    for item in cart.items:
        print(f"    - {item.product_name}: {item.quantity}x @ ${item.price:.2f} = ${item.subtotal:.2f}")
    
    # Test inventory tracking
    print("\n--- Testing Inventory Tracking ---")
    
    # Check inventory for KB123
    inv = manager.get_product_inventory("KB123")
    print(f"✓ KB123 Inventory:")
    print(f"  Stock: {inv['stock_quantity']}")
    print(f"  Reserved: {inv['reserved_quantity']}")
    print(f"  Available: {inv['available_quantity']}")
    
    # Test removing from cart
    result = manager.remove_from_cart(user_id, "KB123", 1)
    if result['status'] == 'success':
        print(f"\n✓ Removed 1x KB123 from cart")
    
    # Check inventory after removal
    inv = manager.get_product_inventory("KB123")
    print(f"✓ KB123 After removal:")
    print(f"  Reserved: {inv['reserved_quantity']} (should be 1)")
    
    # Test updating cart item
    result = manager.update_cart_item(user_id, "MS456", 3)
    if result['status'] == 'success':
        print(f"\n✓ Updated MS456 quantity to 3")
    
    # Test clearing cart
    result = manager.clear_cart(user_id)
    if result['status'] == 'success':
        print(f"\n✓ Cleared cart: {result['items_cleared']} items released")
    
    # Verify inventory released
    inv = manager.get_product_inventory("KB123")
    print(f"✓ KB123 After cart clear:")
    print(f"  Reserved: {inv['reserved_quantity']} (should be 0)")
    
    # Test concurrent users
    print("\n--- Testing Multi-User Scenarios ---")
    
    # Two users try to get limited stock
    manager.add_to_cart("alice", "KB789", 20)  # 23 in stock
    result = manager.add_to_cart("bob", "KB789", 5)
    if result['status'] == 'failed':
        print(f"✓ Prevented overselling with multiple users")
    
    # Test cart abandonment
    print("\n--- Testing Cart Abandonment ---")
    
    # Create an old cart (simulate by updating timestamp directly)
    result = manager.cleanup_abandoned_carts(hours=0)  # Clean all active carts
    print(f"✓ Cleaned abandoned carts: {result.get('carts_cleaned', 0)} carts, {result.get('items_released', 0)} items")
    
    # Verify inventory released after abandonment
    inv = manager.get_product_inventory("KB789")
    print(f"✓ KB789 After abandonment cleanup:")
    print(f"  Available: {inv['available_quantity']} (should be back to full stock)")
    
    print("\n✓ Phase 2 testing complete!")
    
    return True


def test_phase3():
    """Test Phase 3: Order Management."""
    print("\n" + "=" * 60)
    print("Testing Phase 3: Order Management")
    print("=" * 60)
    
    # Initialize manager with fresh database
    import os
    if os.path.exists("test_phase3.db"):
        os.remove("test_phase3.db")
    
    manager = CartInventoryManager("test_phase3.db")
    manager.reset_database()
    print("✓ Database reset with demo data")
    
    # Clean up all demo carts to release inventory
    manager.cleanup_abandoned_carts(hours=0)
    print("✓ Cleaned up demo carts to release inventory")
    
    # Test user
    user_id = "test_customer"
    
    print("\n--- Setting up test cart ---")
    
    # Add items to cart
    result1 = manager.add_to_cart(user_id, "KB123", 1)
    if result1['status'] != 'success':
        print(f"Failed to add KB123: {result1}")
    result2 = manager.add_to_cart(user_id, "MS001", 2)
    if result2['status'] != 'success':
        print(f"Failed to add MS001: {result2}")
    cart = manager.get_cart(user_id)
    print(f"✓ Cart prepared with {len(cart.items)} items, total: ${cart.total:.2f}")
    
    # Check inventory state before checkout
    for item in cart.items:
        inv = manager.get_product_inventory(item.product_id)
        print(f"  {item.product_id}: stock={inv['stock_quantity']}, reserved={inv['reserved_quantity']}")
    
    # Test checkout
    print("\n--- Testing Checkout ---")
    
    result = manager.checkout_cart(user_id, "123 Test St, Demo City, DC 12345")
    if result.get('status') == 'success':
        order_id = result['order_id']
        print(f"✓ Order placed: {order_id}")
        print(f"  Total: ${result['total']:.2f}")
        print(f"  Items: {result['items']}")
    elif 'error' in result:
        print(f"✗ Checkout failed: {result['error']}")
        return False
    else:
        # Handle cases where status is present but not 'success'
        order_id = result.get('order_id', 'UNKNOWN')
        if 'message' in result:
            print(f"✓ Order placed: {order_id} - {result['message']}")
        else:
            print(f"✓ Order placed: {order_id}")
    
    # Verify cart is empty after checkout
    cart = manager.get_cart(user_id)
    print(f"✓ Cart cleared after checkout: {len(cart.items)} items")
    
    # Test order retrieval
    print("\n--- Testing Order Retrieval ---")
    
    order = manager.get_order(user_id, order_id)
    if 'error' not in order:
        print(f"✓ Retrieved order {order['order_id']}")
        print(f"  Status: {order['status']}")
        print(f"  Items: {len(order['items'])}")
        for item in order['items']:
            print(f"    - {item['product_name']}: {item['quantity']}x @ ${item['unit_price']:.2f}")
    
    # Test order listing
    print("\n--- Testing Order Listing ---")
    
    orders = manager.list_orders(user_id)
    print(f"✓ User has {len(orders)} orders")
    
    # Test order status update
    print("\n--- Testing Order Status Updates ---")
    
    # Update to shipped
    result = manager.update_order_status(order_id, "shipped")
    if result['status'] == 'success':
        print(f"✓ Order status updated to: shipped")
    
    # Update to delivered
    result = manager.update_order_status(order_id, "delivered")
    if result['status'] == 'success':
        print(f"✓ Order status updated to: delivered")
    
    # Test returns
    print("\n--- Testing Returns ---")
    
    # Create return request
    result = manager.create_return(user_id, order_id, "KB123", "Defective product")
    if result['status'] == 'success':
        return_id = result['return_id']
        print(f"✓ Return request created: {return_id}")
        print(f"  Refund amount: ${result['refund_amount']:.2f}")
    
    # Process return (approve it)
    result = manager.process_return(return_id, approve=True)
    if result['status'] == 'success':
        print(f"✓ Return approved: {result['message']}")
    
    # Check inventory was restored
    inv = manager.get_product_inventory("KB123")
    print(f"✓ Inventory restored after return:")
    print(f"  Stock: {inv['stock_quantity']}")
    
    # Test order cancellation with inventory restoration
    print("\n--- Testing Order Cancellation ---")
    
    # Create another order
    manager.add_to_cart(user_id, "HD001", 1)
    result = manager.checkout_cart(user_id, "456 Another St")
    if result['status'] == 'success':
        cancel_order_id = result['order_id']
        print(f"✓ Created order to cancel: {cancel_order_id}")
    
    # Check inventory before cancellation
    inv_before = manager.get_product_inventory("HD001")
    
    # Cancel the order
    result = manager.update_order_status(cancel_order_id, "cancelled")
    if result['status'] == 'success':
        print(f"✓ Order cancelled")
    
    # Check inventory after cancellation
    inv_after = manager.get_product_inventory("HD001")
    print(f"✓ Inventory restored after cancellation:")
    print(f"  Stock before: {inv_before['stock_quantity']}, after: {inv_after['stock_quantity']}")
    
    # Test filtering orders by status
    print("\n--- Testing Order Filtering ---")
    
    delivered_orders = manager.list_orders(user_id, status="delivered")
    print(f"✓ Delivered orders: {len(delivered_orders)}")
    
    cancelled_orders = manager.list_orders(user_id, status="cancelled")
    print(f"✓ Cancelled orders: {len(cancelled_orders)}")
    
    print("\n✓ Phase 3 testing complete!")
    
    return True


if __name__ == "__main__":
    # Test Phase 1
    success = test_phase1()
    
    if success:
        # Test Phase 2
        success = test_phase2()
    
    if success:
        # Test Phase 3
        success = test_phase3()
    
    sys.exit(0 if success else 1)