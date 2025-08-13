"""Inventory management tests for CartInventoryManager."""

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


class TestInventoryManagement:
    """Test inventory management operations."""
    
    def setup_method(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager()
        self.db_path = self.db_manager.setup_test_db("test_inventory")
        
        # Create products.json with specific stock levels
        self.products_file = os.path.join(self.db_manager.test_dir, "data", "products.json")
        products = [
            {"id": "HIGH_STOCK", "name": "High Stock Item", "price": 10.00, "stock": 1000},
            {"id": "LOW_STOCK", "name": "Low Stock Item", "price": 20.00, "stock": 5},
            {"id": "NO_STOCK", "name": "Out of Stock Item", "price": 30.00, "stock": 0},
            {"id": "SINGLE_STOCK", "name": "Single Item", "price": 40.00, "stock": 1},
        ]
        TestDataFactory.create_products_json(products, self.products_file)
        
        # Initialize manager
        self.manager = CartInventoryManager(self.db_path)
        self.manager.products_file = Path(self.products_file)
        self.manager.initialize_inventory_from_products()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db_manager.cleanup_all()
    
    def test_atomic_reservation(self):
        """Test that inventory reservations are atomic."""
        product_id = "LOW_STOCK"
        
        # Check initial state
        inv = self.manager.get_product_inventory(product_id)
        assert inv['stock_quantity'] == 5
        assert inv['reserved_quantity'] == 0
        assert inv['available_quantity'] == 5
        
        # Reserve some inventory
        success = self.manager.reserve_inventory(product_id, 3)
        assert success
        
        # Check updated state
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 3
        assert inv['available_quantity'] == 2
        
        DatabaseAssertions.assert_inventory_consistent(self.manager, product_id)
    
    def test_cannot_reserve_more_than_available(self):
        """Test that we can't reserve more than available stock."""
        product_id = "LOW_STOCK"
        
        # Try to reserve more than available
        success = self.manager.reserve_inventory(product_id, 10)
        assert not success
        
        # Verify nothing was reserved
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 0
    
    def test_stock_cannot_go_negative(self):
        """Test that stock cannot go negative."""
        product_id = "NO_STOCK"
        
        # Try to reserve from zero stock
        success = self.manager.reserve_inventory(product_id, 1)
        assert not success
        
        # Try to add to cart
        result = self.manager.add_to_cart("user1", product_id, 1)
        assert result.status == 'failed'
        assert 'insufficient stock' in result.error.lower()
    
    def test_reservation_release(self):
        """Test releasing reserved inventory."""
        product_id = "LOW_STOCK"
        user_id = "test_user"
        
        # Add to cart (reserves inventory)
        self.manager.add_to_cart(user_id, product_id, 3)
        
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 3
        
        # Remove from cart (releases inventory)
        self.manager.remove_from_cart(user_id, product_id)
        
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 0
        assert inv['available_quantity'] == 5
    
    def test_partial_release(self):
        """Test partial release of reserved inventory."""
        product_id = "HIGH_STOCK"
        user_id = "test_user"
        
        # Add 10 items to cart
        self.manager.add_to_cart(user_id, product_id, 10)
        
        # Remove 3 items
        self.manager.remove_from_cart(user_id, product_id, 3)
        
        # Check that 7 are still reserved
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 7
        
        # Check cart has 7 items
        cart = self.manager.get_cart(user_id)
        for item in cart.items:
            if item.product_id == product_id:
                assert item.quantity == 7
    
    def test_concurrent_reservations(self):
        """Test multiple users trying to reserve limited stock."""
        product_id = "LOW_STOCK"  # Has 5 stock
        
        # User 1 reserves 3
        result1 = self.manager.add_to_cart("user1", product_id, 3)
        assert result1.status == 'success'
        
        # User 2 tries to reserve 3 (only 2 available)
        result2 = self.manager.add_to_cart("user2", product_id, 3)
        assert result2.status == 'failed'
        
        # User 2 reserves 2 (should work)
        result3 = self.manager.add_to_cart("user2", product_id, 2)
        assert result3.status == 'success'
        
        # Verify all stock is reserved
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 5
        assert inv['available_quantity'] == 0
    
    def test_inventory_commit_on_checkout(self):
        """Test that inventory is committed (reduced) on checkout."""
        product_id = "LOW_STOCK"
        user_id = "test_user"
        
        initial_stock = 5
        
        # Add to cart
        self.manager.add_to_cart(user_id, product_id, 2)
        
        # Check reserved
        inv = self.manager.get_product_inventory(product_id)
        assert inv['stock_quantity'] == initial_stock
        assert inv['reserved_quantity'] == 2
        
        # Checkout
        result = self.manager.checkout_cart(user_id, "123 Test St")
        assert result.status == 'success'
        
        # Check inventory was committed
        inv = self.manager.get_product_inventory(product_id)
        assert inv['stock_quantity'] == initial_stock - 2
        assert inv['reserved_quantity'] == 0
    
    def test_inventory_restoration_on_cancellation(self):
        """Test that inventory is restored when order is cancelled."""
        product_id = "LOW_STOCK"
        user_id = "test_user"
        
        # Create and checkout order
        self.manager.add_to_cart(user_id, product_id, 2)
        result = self.manager.checkout_cart(user_id, "123 Test St")
        order_id = result.order_id
        
        # Check stock was reduced
        inv = self.manager.get_product_inventory(product_id)
        initial_stock_after_order = inv['stock_quantity']
        assert initial_stock_after_order == 3  # 5 - 2
        
        # Cancel order
        self.manager.update_order_status(order_id, "cancelled")
        
        # Check stock was restored
        inv = self.manager.get_product_inventory(product_id)
        assert inv['stock_quantity'] == 5  # Back to original
    
    def test_update_stock_levels(self):
        """Test updating stock levels."""
        product_id = "LOW_STOCK"
        
        # Update stock
        result = self.manager.update_stock(product_id, 100)
        assert result.status == 'success'
        
        # Verify update
        inv = self.manager.get_product_inventory(product_id)
        assert inv['stock_quantity'] == 100
    
    def test_bulk_inventory_operations(self):
        """Test handling multiple inventory operations."""
        user_id = "test_user"
        
        # Add multiple items to cart
        products = ["HIGH_STOCK", "LOW_STOCK", "SINGLE_STOCK"]
        for product_id in products:
            result = self.manager.add_to_cart(user_id, product_id, 1)
            assert result.status == 'success'
        
        # Verify all are reserved
        for product_id in products:
            inv = self.manager.get_product_inventory(product_id)
            assert inv['reserved_quantity'] >= 1
            DatabaseAssertions.assert_inventory_consistent(self.manager, product_id)
        
        # Clear cart
        self.manager.clear_cart(user_id)
        
        # Verify all reservations released
        for product_id in products:
            inv = self.manager.get_product_inventory(product_id)
            assert inv['reserved_quantity'] == 0
            DatabaseAssertions.assert_inventory_consistent(self.manager, product_id)
    
    def test_edge_case_release_more_than_reserved(self):
        """Test releasing more inventory than reserved."""
        product_id = "HIGH_STOCK"
        
        # Reserve 5
        self.manager.reserve_inventory(product_id, 5)
        
        # Try to release 10 (should only release 5)
        self.manager.release_inventory(product_id, 10)
        
        # Check that reserved is 0, not negative
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 0
        assert inv['reserved_quantity'] >= 0  # Never negative
    
    def test_edge_case_commit_without_reservation(self):
        """Test committing inventory without prior reservation."""
        product_id = "HIGH_STOCK"
        
        initial = self.manager.get_product_inventory(product_id)
        
        # Try to commit without reservation
        success = self.manager.commit_inventory(product_id, 5)
        
        # Should fail since nothing was reserved
        assert not success
        
        # Stock should be unchanged
        final = self.manager.get_product_inventory(product_id)
        assert final['stock_quantity'] == initial['stock_quantity']
    
    def test_single_item_competition(self):
        """Test multiple users competing for a single item."""
        product_id = "SINGLE_STOCK"
        
        # First user gets it
        result1 = self.manager.add_to_cart("user1", product_id, 1)
        assert result1.status == 'success'
        
        # Second user can't get it
        result2 = self.manager.add_to_cart("user2", product_id, 1)
        assert result2.status == 'failed'
        
        # First user removes it
        self.manager.remove_from_cart("user1", product_id)
        
        # Now second user can get it
        result3 = self.manager.add_to_cart("user2", product_id, 1)
        assert result3.status == 'success'