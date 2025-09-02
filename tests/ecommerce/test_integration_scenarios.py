"""Integration tests for complete e-commerce scenarios."""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ecommerce.cart_inventory_manager import CartInventoryManager
from tests.ecommerce.test_utils import (
    TestDatabaseManager, TestDataFactory, DatabaseAssertions, validate_database_state
)


class TestIntegrationScenarios:
    """Test complete e-commerce workflows."""
    
    def setup_method(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager()
        self.db_path = self.db_manager.setup_test_db("test_integration")
        
        # Create comprehensive product catalog
        self.products_file = os.path.join(self.db_manager.test_dir, "data", "products.json")
        products = [
            {"id": "LAPTOP", "name": "Gaming Laptop", "price": 1299.99, "stock": 10},
            {"id": "MOUSE", "name": "Wireless Mouse", "price": 79.99, "stock": 50},
            {"id": "KEYBOARD", "name": "Mechanical Keyboard", "price": 149.99, "stock": 30},
            {"id": "MONITOR", "name": "4K Monitor", "price": 599.99, "stock": 15},
            {"id": "HEADSET", "name": "Gaming Headset", "price": 199.99, "stock": 25},
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
        """Test a complete purchase from browsing to delivery."""
        user_id = "john_doe"
        
        # Step 1: User browses products
        inventory_before = {}
        for product in ["LAPTOP", "MOUSE", "KEYBOARD"]:
            inv = self.manager.get_product_inventory(product)
            inventory_before[product] = inv.stock_quantity
        
        # Step 2: Add items to cart
        cart_items = [
            ("LAPTOP", 1),
            ("MOUSE", 2),
            ("KEYBOARD", 1)
        ]
        
        for product_id, quantity in cart_items:
            result = self.manager.add_to_cart(user_id, product_id, quantity)
            assert result.status == 'success', f"Failed to add {product_id}"
        
        # Step 3: Review cart
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 3
        expected_total = 1299.99 + (79.99 * 2) + 149.99
        assert abs(cart.total - expected_total) < 0.01
        
        # Step 4: Checkout
        shipping_address = "123 Main St, Tech City, TC 12345"
        checkout_result = self.manager.checkout_cart(user_id, shipping_address)
        assert checkout_result.status == 'success'
        order_id = checkout_result.order_id
        
        # Step 5: Process order (ship and deliver)
        self.manager.update_order_status(order_id, 'shipped')
        deliver_result = self.manager.update_order_status(order_id, 'delivered')
        assert deliver_result.status == 'success'
        
        # Verify final order state
        order = self.manager.get_order(user_id, order_id)
        assert order.status == 'delivered'
        
        # Verify inventory was properly reduced
        for product, original_stock in inventory_before.items():
            inv_after = self.manager.get_product_inventory(product)
            if product == "LAPTOP":
                assert inv_after.stock_quantity == original_stock - 1
            elif product == "MOUSE":
                assert inv_after.stock_quantity == original_stock - 2
            elif product == "KEYBOARD":
                assert inv_after.stock_quantity == original_stock - 1
    
    def test_concurrent_users_limited_stock(self):
        """Test multiple users competing for limited stock item."""
        limited_product = "LIMITED"  # Only 1 in stock
        users = ["user_a", "user_b", "user_c"]
        
        # All users try to add the limited item
        results = []
        for user in users:
            result = self.manager.add_to_cart(user, limited_product, 1)
            results.append((user, result.status))
        
        # Only one should succeed
        success_count = sum(1 for _, status in results if status == 'success')
        assert success_count == 1, f"Expected 1 success, got {success_count}"
        
        # Find the successful user
        successful_user = None
        for user, status in results:
            if status == 'success':
                successful_user = user
                break
        
        # Successful user checks out
        checkout = self.manager.checkout_cart(successful_user, "Winner's Address")
        assert checkout.status == 'success'
        
        # Verify item is now completely out of stock
        inv = self.manager.get_product_inventory(limited_product)
        assert inv.stock_quantity == 0
    
    def test_full_return_flow(self):
        """Test complete return flow: Order → Deliver → Return → Refund."""
        user_id = "return_customer"
        
        # Create order
        self.manager.add_to_cart(user_id, "HEADSET", 1)
        self.manager.add_to_cart(user_id, "MOUSE", 1)
        checkout = self.manager.checkout_cart(user_id, "456 Return Ave")
        order_id = checkout.order_id
        
        # Deliver order
        self.manager.update_order_status(order_id, 'shipped')
        self.manager.update_order_status(order_id, 'delivered')
        
        # Customer returns headset
        return_result = self.manager.create_return(
            user_id, order_id, "HEADSET", "Audio quality issues"
        )
        return_id = return_result.return_id
        
        # Process return
        process_result = self.manager.process_return(return_id, approve=True)
        assert process_result.status == 'success'
        
        # Verify inventory restored
        headset_inv = self.manager.get_product_inventory("HEADSET")
        assert headset_inv.stock_quantity == 25  # Back to original
    
    def test_database_integrity_comprehensive(self):
        """Test that database maintains integrity through complex operations."""
        users = ["user1", "user2", "user3"]
        
        # Create various cart states
        self.manager.add_to_cart(users[0], "LAPTOP", 1)
        self.manager.add_to_cart(users[0], "MOUSE", 2)
        self.manager.checkout_cart(users[0], "Address 1")
        
        # Some clear cart
        self.manager.add_to_cart(users[1], "KEYBOARD", 1)
        self.manager.clear_cart(users[1])
        
        # Create and cancel an order
        self.manager.add_to_cart(users[2], "MONITOR", 1)
        result = self.manager.checkout_cart(users[2], "Address 2")
        self.manager.update_order_status(result.order_id, 'cancelled')
        
        # Validate database state
        validation = validate_database_state(self.db_path)
        assert validation['valid'], f"Database integrity check failed: {validation['issues']}"
        
        # Verify no orphaned records
        assert len(validation['issues']) == 0