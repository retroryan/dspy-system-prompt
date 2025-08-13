"""Cart operations tests for CartInventoryManager."""

import pytest
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tools.ecommerce.cart_inventory_manager import CartInventoryManager
from tools.ecommerce.tests.test_utils import (
    TestDatabaseManager, TestDataFactory, DatabaseAssertions
)


class TestCartOperations:
    """Test cart management operations."""
    
    def setup_method(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager()
        self.db_path = self.db_manager.setup_test_db("test_cart")
        
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
    
    def test_cart_creation(self):
        """Test cart creation for new user."""
        user_id = "new_user"
        
        # Get cart for new user should create one
        cart_id = self.manager.get_or_create_cart(user_id)
        assert cart_id > 0
        
        # Getting again should return same cart
        cart_id2 = self.manager.get_or_create_cart(user_id)
        assert cart_id == cart_id2
    
    def test_cart_isolation(self):
        """Test that carts are isolated between users."""
        user1 = "user1"
        user2 = "user2"
        
        # Add items to user1's cart
        self.manager.add_to_cart(user1, "TEST001", 2)
        self.manager.add_to_cart(user1, "TEST002", 1)
        
        # Add different items to user2's cart
        self.manager.add_to_cart(user2, "TEST003", 3)
        
        # Check user1's cart
        cart1 = self.manager.get_cart(user1)
        assert len(cart1.items) == 2
        assert cart1.item_count == 3  # 2 + 1
        
        # Check user2's cart
        cart2 = self.manager.get_cart(user2)
        assert len(cart2.items) == 1
        assert cart2.item_count == 3
        
        # Ensure carts are different
        assert cart1.cart_id != cart2.cart_id
    
    def test_add_duplicate_items(self):
        """Test adding same item multiple times updates quantity."""
        user_id = "test_user"
        product_id = "TEST001"
        
        # Add item first time
        result1 = self.manager.add_to_cart(user_id, product_id, 2)
        assert result1['status'] == 'success'
        
        # Add same item again
        result2 = self.manager.add_to_cart(user_id, product_id, 3)
        assert result2['status'] == 'success'
        
        # Check cart has combined quantity
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5  # 2 + 3
    
    def test_partial_quantity_removal(self):
        """Test removing partial quantities from cart."""
        user_id = "test_user"
        product_id = "TEST001"
        
        # Add 5 items
        self.manager.add_to_cart(user_id, product_id, 5)
        
        # Remove 2
        result = self.manager.remove_from_cart(user_id, product_id, 2)
        assert result['status'] == 'success'
        
        # Check 3 remain
        cart = self.manager.get_cart(user_id)
        assert cart.items[0].quantity == 3
    
    def test_complete_item_removal(self):
        """Test removing all of an item from cart."""
        user_id = "test_user"
        
        # Add multiple items
        self.manager.add_to_cart(user_id, "TEST001", 2)
        self.manager.add_to_cart(user_id, "TEST002", 3)
        
        # Remove all of TEST001
        self.manager.remove_from_cart(user_id, "TEST001")
        
        # Check only TEST002 remains
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 1
        assert cart.items[0].product_id == "TEST002"
    
    def test_update_cart_item_quantity(self):
        """Test updating quantity of cart item."""
        user_id = "test_user"
        product_id = "TEST001"
        
        # Add item
        self.manager.add_to_cart(user_id, product_id, 2)
        
        # Update to different quantity
        result = self.manager.update_cart_item(user_id, product_id, 5)
        assert result['status'] == 'success'
        
        # Verify update
        cart = self.manager.get_cart(user_id)
        assert cart.items[0].quantity == 5
    
    def test_update_to_zero_removes_item(self):
        """Test that updating quantity to 0 removes item."""
        user_id = "test_user"
        product_id = "TEST001"
        
        # Add item
        self.manager.add_to_cart(user_id, product_id, 3)
        
        # Update to 0
        result = self.manager.update_cart_item(user_id, product_id, 0)
        assert result['status'] == 'success'
        
        # Verify item removed
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 0
    
    def test_cart_totals(self):
        """Test that cart totals are calculated correctly."""
        user_id = "test_user"
        
        # Add items with known prices
        # TEST000: 10.00, TEST001: 15.00, TEST002: 20.00
        self.manager.add_to_cart(user_id, "TEST000", 2)  # 20.00
        self.manager.add_to_cart(user_id, "TEST001", 1)  # 15.00
        self.manager.add_to_cart(user_id, "TEST002", 3)  # 60.00
        
        cart = self.manager.get_cart(user_id)
        
        # Check item count
        assert cart.item_count == 6  # 2 + 1 + 3
        
        # Check total
        expected_total = 20.00 + 15.00 + 60.00
        assert abs(cart.total - expected_total) < 0.01
        
        # Verify with assertion helper
        DatabaseAssertions.assert_cart_total_correct(self.manager, user_id)
    
    def test_clear_cart(self):
        """Test clearing all items from cart."""
        user_id = "test_user"
        
        # Add multiple items
        self.manager.add_to_cart(user_id, "TEST001", 2)
        self.manager.add_to_cart(user_id, "TEST002", 3)
        self.manager.add_to_cart(user_id, "TEST003", 1)
        
        # Clear cart
        result = self.manager.clear_cart(user_id)
        assert result['status'] == 'success'
        assert result['items_cleared'] == 3
        
        # Verify cart is empty
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 0
        assert cart.total == 0
        
        # Verify inventory was released
        for product_id in ["TEST001", "TEST002", "TEST003"]:
            inv = self.manager.get_product_inventory(product_id)
            assert inv['reserved_quantity'] == 0
    
    def test_cart_status_transitions(self):
        """Test cart status changes through lifecycle."""
        user_id = "test_user"
        
        # Create cart (status: active)
        self.manager.add_to_cart(user_id, "TEST001", 1)
        
        # Checkout (status: checked_out)
        result = self.manager.checkout_cart(user_id, "123 Test St")
        assert result['status'] == 'success'
        
        # Old cart should not be returned as active
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 0  # New empty cart
    
    def test_empty_cart_operations(self):
        """Test operations on empty cart."""
        user_id = "test_user"
        
        # Get empty cart
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 0
        assert cart.total == 0
        
        # Try to remove from empty cart
        result = self.manager.remove_from_cart(user_id, "TEST001")
        assert result['status'] == 'failed'
        
        # Try to clear empty cart
        result = self.manager.clear_cart(user_id)
        assert result['status'] == 'success'
        assert result.get('items_cleared', 0) == 0
    
    def test_cart_with_invalid_product(self):
        """Test adding non-existent product to cart."""
        user_id = "test_user"
        
        result = self.manager.add_to_cart(user_id, "INVALID_PRODUCT", 1)
        assert result['status'] == 'failed'
        assert 'not found' in result['error'].lower()
    
    def test_concurrent_cart_modifications(self):
        """Test concurrent modifications to same cart."""
        user_id = "test_user"
        product1 = "TEST001"
        product2 = "TEST002"
        
        # Add two products
        self.manager.add_to_cart(user_id, product1, 5)
        self.manager.add_to_cart(user_id, product2, 3)
        
        # Simulate concurrent operations
        # Remove some of product1
        self.manager.remove_from_cart(user_id, product1, 2)
        
        # Update product2
        self.manager.update_cart_item(user_id, product2, 5)
        
        # Verify final state
        cart = self.manager.get_cart(user_id)
        
        for item in cart.items:
            if item.product_id == product1:
                assert item.quantity == 3
            elif item.product_id == product2:
                assert item.quantity == 5
    
    def test_cart_abandonment_cleanup(self):
        """Test cleanup of abandoned carts."""
        user_id = "test_user"
        
        # Add items to cart
        self.manager.add_to_cart(user_id, "TEST001", 2)
        
        # Manually update the cart timestamp to make it old
        with self.manager.get_connection() as conn:
            cursor = conn.cursor()
            from datetime import datetime, timedelta
            old_time = datetime.now() - timedelta(hours=2)
            cursor.execute("""
                UPDATE carts 
                SET updated_at = ? 
                WHERE user_id = ? AND status = 'active'
            """, (old_time, user_id))
        
        # Clean up carts older than 1 hour
        result = self.manager.cleanup_abandoned_carts(hours=1)
        assert result['status'] == 'success'
        assert result['carts_cleaned'] >= 1
        
        # Verify inventory was released
        inv = self.manager.get_product_inventory("TEST001")
        assert inv['reserved_quantity'] == 0
    
    def test_multiple_carts_same_product(self):
        """Test multiple users with same product in cart."""
        product_id = "TEST001"
        users = ["user1", "user2", "user3"]
        
        # Each user adds same product
        for user in users:
            result = self.manager.add_to_cart(user, product_id, 10)
            assert result['status'] == 'success'
        
        # Check total reservations
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 30  # 3 users * 10 each
        
        # One user clears cart
        self.manager.clear_cart(users[0])
        
        # Check reservations reduced
        inv = self.manager.get_product_inventory(product_id)
        assert inv['reserved_quantity'] == 20  # 2 users * 10 each