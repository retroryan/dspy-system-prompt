"""Integration tests for complete e-commerce scenarios."""

import pytest
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tools.ecommerce.cart_inventory_manager import CartInventoryManager
from tools.ecommerce.tests.test_utils import (
    TestDatabaseManager, TestDataFactory, DatabaseAssertions, validate_database_state
)


class TestIntegrationScenarios:
    """Test complete e-commerce workflows."""
    
    def setup_method(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager()
        self.db_path = self.db_manager.setup_test_db("test_integration")
        
        # Create products with varying stock levels
        self.products_file = os.path.join(self.db_manager.test_dir, "data", "products.json")
        products = [
            {"id": "LAPTOP", "name": "Gaming Laptop", "price": 1299.99, "stock": 10},
            {"id": "MOUSE", "name": "Gaming Mouse", "price": 79.99, "stock": 50},
            {"id": "KEYBOARD", "name": "Mechanical Keyboard", "price": 149.99, "stock": 25},
            {"id": "MONITOR", "name": "4K Monitor", "price": 599.99, "stock": 5},
            {"id": "HEADSET", "name": "Gaming Headset", "price": 129.99, "stock": 30},
            {"id": "LIMITED", "name": "Limited Edition Item", "price": 999.99, "stock": 1},
        ]
        TestDataFactory.create_products_json(products, self.products_file)
        
        # Initialize manager
        self.manager = CartInventoryManager(self.db_path)
        self.manager.products_file = Path(self.products_file)
        self.manager.initialize_inventory_from_products()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db_manager.cleanup_all()
    
    def test_complete_purchase_flow(self):
        """Test complete flow: Browse → Add to Cart → Checkout → Ship → Deliver."""
        user_id = "customer1"
        
        # Step 1: Browse (check product availability)
        laptop_inv = self.manager.get_product_inventory("LAPTOP")
        assert laptop_inv['available_quantity'] > 0
        
        # Step 2: Add multiple items to cart
        cart_items = [
            ("LAPTOP", 1),
            ("MOUSE", 2),
            ("KEYBOARD", 1)
        ]
        
        for product_id, quantity in cart_items:
            result = self.manager.add_to_cart(user_id, product_id, quantity)
            assert result['status'] == 'success', f"Failed to add {product_id}"
        
        # Step 3: Review cart
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 3
        expected_total = 1299.99 + (79.99 * 2) + 149.99
        assert abs(cart.total - expected_total) < 0.01
        
        # Verify cart total is correct
        DatabaseAssertions.assert_cart_total_correct(self.manager, user_id)
        
        # Step 4: Checkout
        shipping_address = "123 Main St, Tech City, TC 12345"
        checkout_result = self.manager.checkout_cart(user_id, shipping_address)
        assert checkout_result['status'] == 'success'
        order_id = checkout_result['order_id']
        
        # Verify order created
        DatabaseAssertions.assert_order_complete(self.manager, user_id, order_id)
        
        # Step 5: Process order (ship)
        ship_result = self.manager.update_order_status(order_id, 'shipped')
        assert ship_result['status'] == 'success'
        
        # Step 6: Deliver order
        deliver_result = self.manager.update_order_status(order_id, 'delivered')
        assert deliver_result['status'] == 'success'
        
        # Verify final order state
        order = self.manager.get_order(user_id, order_id)
        assert order['status'] == 'delivered'
        assert order['shipping_address'] == shipping_address
        
        # Verify inventory was properly reduced
        laptop_inv_after = self.manager.get_product_inventory("LAPTOP")
        assert laptop_inv_after['stock_quantity'] == laptop_inv['stock_quantity'] - 1
        
        # Validate database integrity
        validation = validate_database_state(self.db_path)
        assert validation['valid'], f"Database validation failed: {validation['issues']}"
    
    def test_concurrent_users_limited_stock(self):
        """Test multiple users competing for limited stock item."""
        limited_product = "LIMITED"  # Only 1 in stock
        users = ["user_a", "user_b", "user_c"]
        
        # All users try to add the limited item
        results = []
        for user in users:
            result = self.manager.add_to_cart(user, limited_product, 1)
            results.append((user, result['status']))
        
        # Only one should succeed
        success_count = sum(1 for _, status in results if status == 'success')
        assert success_count == 1, f"Expected 1 success, got {success_count}"
        
        # Find the successful user
        successful_user = None
        for user, status in results:
            if status == 'success':
                successful_user = user
                break
        
        assert successful_user is not None
        
        # Successful user checks out
        checkout = self.manager.checkout_cart(successful_user, "Winner's Address")
        assert checkout['status'] == 'success'
        
        # Verify item is now completely out of stock
        inv = self.manager.get_product_inventory(limited_product)
        assert inv['stock_quantity'] == 0
        assert inv['available_quantity'] == 0
    
    def test_system_recovery_after_crash(self):
        """Test data consistency after simulated crash during checkout."""
        user_id = "crash_test_user"
        
        # Add items to cart
        self.manager.add_to_cart(user_id, "LAPTOP", 1)
        self.manager.add_to_cart(user_id, "MOUSE", 2)
        
        # Get initial state
        initial_laptop_inv = self.manager.get_product_inventory("LAPTOP")
        initial_mouse_inv = self.manager.get_product_inventory("MOUSE")
        
        # Simulate crash by making stock insufficient during checkout
        # This will cause checkout to fail with rollback
        with self.manager.get_connection() as conn:
            cursor = conn.cursor()
            # Set LAPTOP stock to 0 to cause failure
            cursor.execute("""
                UPDATE inventory SET stock_quantity = 0 WHERE product_id = 'LAPTOP'
            """)
        
        # Attempt checkout (will fail due to insufficient stock)
        result = self.manager.checkout_cart(user_id, "123 Test St")
        assert result['status'] == 'failed'
        
        # Restore stock levels
        with self.manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inventory SET stock_quantity = 10 WHERE product_id = 'LAPTOP'
            """)
        
        # Verify inventory wasn't changed (transaction rolled back)
        laptop_inv = self.manager.get_product_inventory("LAPTOP")
        mouse_inv = self.manager.get_product_inventory("MOUSE")
        
        assert laptop_inv['reserved_quantity'] == initial_laptop_inv['reserved_quantity']
        assert mouse_inv['reserved_quantity'] == initial_mouse_inv['reserved_quantity']
        
        # Verify no order was created
        orders = self.manager.list_orders(user_id)
        assert len(orders) == 0
        
        # System should be able to continue normally
        retry_result = self.manager.checkout_cart(user_id, "123 Test St")
        assert retry_result['status'] == 'success'
    
    def test_full_return_flow(self):
        """Test complete return flow: Order → Deliver → Return → Refund."""
        user_id = "return_customer"
        
        # Create order
        self.manager.add_to_cart(user_id, "HEADSET", 1)
        self.manager.add_to_cart(user_id, "MOUSE", 1)
        
        checkout = self.manager.checkout_cart(user_id, "Return Address")
        order_id = checkout['order_id']
        
        # Deliver order
        self.manager.update_order_status(order_id, 'shipped')
        self.manager.update_order_status(order_id, 'delivered')
        
        # Customer returns headset
        return_result = self.manager.create_return(
            user_id, order_id, "HEADSET", "Audio quality issues"
        )
        return_id = return_result['return_id']
        
        # Process return
        process_result = self.manager.process_return(return_id, approve=True)
        assert process_result['status'] == 'success'
        
        # Verify inventory restored
        headset_inv = self.manager.get_product_inventory("HEADSET")
        assert headset_inv['stock_quantity'] == 30  # Back to original
    
    def test_abandoned_cart_recovery(self):
        """Test cart abandonment and recovery flow."""
        user_id = "abandon_user"
        
        # User adds items to cart
        self.manager.add_to_cart(user_id, "MONITOR", 1)
        self.manager.add_to_cart(user_id, "KEYBOARD", 1)
        
        # Verify items are reserved
        monitor_inv = self.manager.get_product_inventory("MONITOR")
        assert monitor_inv['reserved_quantity'] == 1
        
        # Make cart old to simulate abandonment
        from datetime import datetime, timedelta
        with self.manager.get_connection() as conn:
            cursor = conn.cursor()
            old_time = datetime.now() - timedelta(hours=2)
            cursor.execute("""
                UPDATE carts 
                SET updated_at = ? 
                WHERE user_id = ? AND status = 'active'
            """, (old_time, user_id))
        
        # Cleanup carts older than 1 hour
        cleanup_result = self.manager.cleanup_abandoned_carts(hours=1)
        assert cleanup_result['carts_cleaned'] >= 1
        
        # Verify inventory released
        monitor_inv_after = self.manager.get_product_inventory("MONITOR")
        assert monitor_inv_after['reserved_quantity'] == 0
        
        # Another user can now purchase the item
        other_user = "new_customer"
        result = self.manager.add_to_cart(other_user, "MONITOR", 1)
        assert result['status'] == 'success'
    
    def test_multi_user_shopping_scenario(self):
        """Test realistic multi-user shopping scenario."""
        users_and_carts = [
            ("alice", [("LAPTOP", 1), ("MOUSE", 1)]),
            ("bob", [("KEYBOARD", 2), ("HEADSET", 1)]),
            ("charlie", [("MONITOR", 1), ("MOUSE", 2)]),
        ]
        
        # All users add to carts
        for user, items in users_and_carts:
            for product_id, quantity in items:
                result = self.manager.add_to_cart(user, product_id, quantity)
                assert result['status'] == 'success', \
                    f"Failed to add {product_id} for {user}"
        
        # Verify total reservations
        mouse_inv = self.manager.get_product_inventory("MOUSE")
        assert mouse_inv['reserved_quantity'] == 3  # alice:1 + charlie:2
        
        # Alice checks out
        alice_checkout = self.manager.checkout_cart("alice", "Alice Address")
        assert alice_checkout['status'] == 'success'
        
        # Bob abandons cart
        self.manager.clear_cart("bob")
        
        # Charlie checks out
        charlie_checkout = self.manager.checkout_cart("charlie", "Charlie Address")
        assert charlie_checkout['status'] == 'success'
        
        # Verify final inventory state
        keyboard_inv = self.manager.get_product_inventory("KEYBOARD")
        assert keyboard_inv['reserved_quantity'] == 0  # Bob's reservation cleared
        
        # Verify orders
        alice_orders = self.manager.list_orders("alice")
        assert len(alice_orders) == 1
        
        bob_orders = self.manager.list_orders("bob")
        assert len(bob_orders) == 0  # No order due to cart abandonment
        
        charlie_orders = self.manager.list_orders("charlie")
        assert len(charlie_orders) == 1
    
    def test_order_cancellation_and_reorder(self):
        """Test cancelling an order and reordering same items."""
        user_id = "cancel_user"
        product_id = "LAPTOP"
        
        # First order
        self.manager.add_to_cart(user_id, product_id, 1)
        first_checkout = self.manager.checkout_cart(user_id, "First Address")
        first_order_id = first_checkout['order_id']
        
        # Check stock after first order
        inv_after_first = self.manager.get_product_inventory(product_id)
        stock_after_first = inv_after_first['stock_quantity']
        
        # Cancel first order
        self.manager.update_order_status(first_order_id, 'cancelled')
        
        # Stock should be restored
        inv_after_cancel = self.manager.get_product_inventory(product_id)
        assert inv_after_cancel['stock_quantity'] == stock_after_first + 1
        
        # Reorder same item
        self.manager.add_to_cart(user_id, product_id, 1)
        second_checkout = self.manager.checkout_cart(user_id, "Second Address")
        assert second_checkout['status'] == 'success'
        
        # Verify both orders exist
        orders = self.manager.list_orders(user_id)
        assert len(orders) == 2
        
        # Verify statuses
        for order in orders:
            if order['order_id'] == first_order_id:
                assert order['status'] == 'cancelled'
            else:
                assert order['status'] == 'processing'
    
    def test_database_integrity_after_operations(self):
        """Test database integrity after complex operations."""
        # Perform various operations
        users = ["user1", "user2", "user3"]
        
        # Create carts
        for user in users:
            self.manager.add_to_cart(user, "MOUSE", 1)
        
        # Some checkout
        self.manager.checkout_cart(users[0], "Address 1")
        
        # Some clear cart
        self.manager.clear_cart(users[1])
        
        # Create and cancel an order
        self.manager.add_to_cart(users[2], "KEYBOARD", 1)
        result = self.manager.checkout_cart(users[2], "Address 2")
        self.manager.update_order_status(result['order_id'], 'cancelled')
        
        # Validate database state
        validation = validate_database_state(self.db_path)
        assert validation['valid'], f"Database integrity check failed: {validation['issues']}"
        
        # Verify no orphaned records
        assert len(validation['issues']) == 0
        
        # Verify inventory consistency
        for product_id in ["MOUSE", "KEYBOARD"]:
            DatabaseAssertions.assert_inventory_consistent(self.manager, product_id)