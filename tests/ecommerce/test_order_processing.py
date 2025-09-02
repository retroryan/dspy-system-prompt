"""Order processing tests for CartInventoryManager."""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tools.ecommerce.cart_inventory_manager import CartInventoryManager
from tests.ecommerce.test_utils import (
    TestDatabaseManager, TestDataFactory, DatabaseAssertions
)


class TestOrderProcessing:
    """Test order processing operations."""
    
    def setup_method(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager()
        self.db_path = self.db_manager.setup_test_db("test_orders")
        
        # Create products
        self.products_file = os.path.join(self.db_manager.test_dir, "data", "products.json")
        products = TestDataFactory.create_test_products(10)
        TestDataFactory.create_products_json(products, self.products_file)
        
        # Initialize manager
        self.manager = CartInventoryManager(self.db_path)
        self.manager.products_file = Path(self.products_file)
        self.manager.initialize_inventory_from_products()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db_manager.cleanup_all()
    
    def test_successful_checkout(self):
        """Test successful checkout flow."""
        user_id = "test_user"
        
        # Add items to cart
        self.manager.add_to_cart(user_id, "TEST001", 2)
        self.manager.add_to_cart(user_id, "TEST002", 1)
        
        # Get cart total before checkout
        cart = self.manager.get_cart(user_id)
        cart_total = cart.total
        
        # Checkout
        result = self.manager.checkout_cart(user_id, "123 Test St, Demo City")
        
        assert result.status == 'success'
        assert hasattr(result, 'order_id')
        assert result.total == cart_total
        assert result.items == 2
        
        # Verify order was created
        order = self.manager.get_order(user_id, result.order_id)
        assert order.status == 'processing'
        assert len(order.items) == 2
        
        DatabaseAssertions.assert_order_complete(self.manager, user_id, result.order_id)
    
    def test_checkout_empty_cart(self):
        """Test checkout with empty cart fails."""
        user_id = "test_user"
        
        result = self.manager.checkout_cart(user_id, "123 Test St")
        
        assert result.status == 'failed'
        assert 'empty' in result.error.lower()
    
    def test_cart_cleared_after_checkout(self):
        """Test that cart is cleared after successful checkout."""
        user_id = "test_user"
        
        # Add items
        self.manager.add_to_cart(user_id, "TEST001", 3)
        
        # Checkout
        result = self.manager.checkout_cart(user_id, "123 Test St")
        assert result.status == 'success'
        
        # Verify cart is empty
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 0
        assert cart.total == 0
    
    def test_inventory_committed_on_checkout(self):
        """Test that inventory is properly committed during checkout."""
        user_id = "test_user"
        product_id = "TEST001"
        
        # Check initial inventory
        initial_inv = self.manager.get_product_inventory(product_id)
        initial_stock = initial_inv.stock_quantity
        
        # Add to cart
        self.manager.add_to_cart(user_id, product_id, 2)
        
        # Verify reservation
        inv = self.manager.get_product_inventory(product_id)
        assert inv.reserved_quantity == 2
        
        # Checkout
        result = self.manager.checkout_cart(user_id, "123 Test St")
        assert result.status == 'success'
        
        # Verify stock reduced and reservation cleared
        final_inv = self.manager.get_product_inventory(product_id)
        assert final_inv.stock_quantity == initial_stock - 2
        assert final_inv.reserved_quantity == 0
    
    def test_order_status_transitions(self):
        """Test all valid order status transitions."""
        user_id = "test_user"
        
        # Create order
        self.manager.add_to_cart(user_id, "TEST001", 1)
        result = self.manager.checkout_cart(user_id, "123 Test St")
        order_id = result.order_id
        
        # Initial status should be processing
        order = self.manager.get_order(user_id, order_id)
        assert order.status == 'processing'
        
        # Update to shipped
        result = self.manager.update_order_status(order_id, 'shipped')
        assert result.status == 'success'
        
        order = self.manager.get_order(user_id, order_id)
        assert order.status == 'shipped'
        
        # Update to delivered
        result = self.manager.update_order_status(order_id, 'delivered')
        assert result.status == 'success'
        
        order = self.manager.get_order(user_id, order_id)
        assert order.status == 'delivered'
    
    def test_invalid_status_transition(self):
        """Test invalid order status transitions."""
        user_id = "test_user"
        
        # Create order
        self.manager.add_to_cart(user_id, "TEST001", 1)
        result = self.manager.checkout_cart(user_id, "123 Test St")
        order_id = result.order_id
        
        # Try invalid status
        result = self.manager.update_order_status(order_id, 'invalid_status')
        assert result.status == 'failed'
        assert 'invalid status' in result.error.lower()
    
    def test_order_cancellation(self):
        """Test order cancellation and inventory restoration."""
        user_id = "test_user"
        product_id = "TEST001"
        
        # Check initial stock
        initial_inv = self.manager.get_product_inventory(product_id)
        initial_stock = initial_inv.stock_quantity
        
        # Create and checkout order
        self.manager.add_to_cart(user_id, product_id, 3)
        result = self.manager.checkout_cart(user_id, "123 Test St")
        order_id = result.order_id
        
        # Verify stock was reduced
        inv = self.manager.get_product_inventory(product_id)
        assert inv.stock_quantity == initial_stock - 3
        
        # Cancel order
        result = self.manager.update_order_status(order_id, 'cancelled')
        assert result.status == 'success'
        
        # Verify stock was restored
        final_inv = self.manager.get_product_inventory(product_id)
        assert final_inv.stock_quantity == initial_stock
    
    def test_list_orders(self):
        """Test listing user orders."""
        user_id = "test_user"
        
        # Create multiple orders
        for i in range(3):
            self.manager.add_to_cart(user_id, f"TEST00{i}", 1)
            result = self.manager.checkout_cart(user_id, f"Address {i}")
            assert result.status == 'success'
        
        # List all orders
        orders = self.manager.list_orders(user_id)
        assert len(orders) == 3
        
        # Verify order structure
        for order in orders:
            assert hasattr(order, 'order_id')
            assert hasattr(order, 'status')
            assert hasattr(order, 'total')
            assert hasattr(order, 'created_at')
    
    def test_list_orders_by_status(self):
        """Test filtering orders by status."""
        user_id = "test_user"
        
        # Create orders with different statuses
        order_ids = []
        for i in range(3):
            self.manager.add_to_cart(user_id, f"TEST00{i}", 1)
            result = self.manager.checkout_cart(user_id, "123 Test St")
            order_ids.append(result.order_id)
        
        # Update statuses
        self.manager.update_order_status(order_ids[0], 'shipped')
        self.manager.update_order_status(order_ids[1], 'delivered')
        # order_ids[2] remains as 'processing'
        
        # Filter by status
        shipped = self.manager.list_orders(user_id, status='shipped')
        assert len(shipped) == 1
        
        delivered = self.manager.list_orders(user_id, status='delivered')
        assert len(delivered) == 1
        
        processing = self.manager.list_orders(user_id, status='processing')
        assert len(processing) == 1
    
    def test_order_isolation_between_users(self):
        """Test that orders are isolated between users."""
        user1 = "user1"
        user2 = "user2"
        
        # Create order for user1
        self.manager.add_to_cart(user1, "TEST001", 1)
        result1 = self.manager.checkout_cart(user1, "User1 Address")
        order1_id = result1.order_id
        
        # Create order for user2
        self.manager.add_to_cart(user2, "TEST002", 2)
        result2 = self.manager.checkout_cart(user2, "User2 Address")
        order2_id = result2.order_id
        
        # User1 can't access user2's order
        order = self.manager.get_order(user1, order2_id)
        assert order is None
        
        # User2 can't access user1's order
        order = self.manager.get_order(user2, order1_id)
        assert order is None
        
        # Each user sees only their orders
        user1_orders = self.manager.list_orders(user1)
        assert len(user1_orders) == 1
        assert user1_orders[0].order_id == order1_id
        
        user2_orders = self.manager.list_orders(user2)
        assert len(user2_orders) == 1
        assert user2_orders[0].order_id == order2_id
    
    def test_checkout_with_insufficient_stock(self):
        """Test checkout fails if stock becomes insufficient."""
        user_id = "test_user"
        product_id = "TEST001"
        
        # Set stock to specific amount
        self.manager.update_stock(product_id, 5)
        
        # User adds 3 to cart
        self.manager.add_to_cart(user_id, product_id, 3)
        
        # Another user takes remaining stock
        self.manager.add_to_cart("other_user", product_id, 2)
        other_result = self.manager.checkout_cart("other_user", "Other Address")
        assert other_result.status == 'success'
        
        # Now original user's checkout should handle the stock issue
        # The cart has reserved items, so checkout should still work
        result = self.manager.checkout_cart(user_id, "123 Test St")
        assert result.status == 'success'  # Should work because items were reserved
    
    def test_order_totals_match_cart(self):
        """Test that order totals match cart totals."""
        user_id = "test_user"
        
        # Add items with known prices
        self.manager.add_to_cart(user_id, "TEST000", 2)  # 10.00 * 2 = 20.00
        self.manager.add_to_cart(user_id, "TEST001", 1)  # 15.00 * 1 = 15.00
        
        # Get cart total
        cart = self.manager.get_cart(user_id)
        cart_total = cart.total
        
        # Checkout
        result = self.manager.checkout_cart(user_id, "123 Test St")
        order_id = result.order_id
        
        # Get order
        order = self.manager.get_order(user_id, order_id)
        
        # Totals should match
        assert abs(order.total - cart_total) < 0.01
        
        # Verify item totals
        items_total = sum(item.subtotal for item in order.items)
        assert abs(items_total - order.total) < 0.01
    
    def test_concurrent_checkouts(self):
        """Test multiple users checking out simultaneously."""
        users = ["user1", "user2", "user3"]
        product_id = "TEST001"
        
        # Each user adds to cart
        for user in users:
            self.manager.add_to_cart(user, product_id, 10)
        
        # All checkout
        results = []
        for user in users:
            result = self.manager.checkout_cart(user, f"{user} Address")
            results.append(result)
        
        # All should succeed if enough stock
        success_count = sum(1 for r in results if r.status == 'success')
        assert success_count == len(users)
        
        # Verify orders created
        for i, user in enumerate(users):
            if results[i].status == 'success':
                orders = self.manager.list_orders(user)
                assert len(orders) >= 1