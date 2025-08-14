"""Cart operations tests for CartInventoryManager."""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ecommerce.cart_inventory_manager import CartInventoryManager
from tests.ecommerce.test_utils import (
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
        assert result1.status == 'success'
        
        # Add same item again
        result2 = self.manager.add_to_cart(user_id, product_id, 3)
        assert result2.status == 'success'
        
        # Check cart has combined quantity
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5  # 2 + 3
    
    def test_update_cart_item_quantity(self):
        """Test updating quantity of cart item."""
        user_id = "test_user"
        product_id = "TEST001"
        
        # Add item
        self.manager.add_to_cart(user_id, product_id, 2)
        
        # Update to different quantity
        result = self.manager.update_cart_item(user_id, product_id, 5)
        assert result.status == 'success'
        
        # Verify update
        cart = self.manager.get_cart(user_id)
        assert cart.items[0].quantity == 5
        
        # Update to 0 removes item
        result = self.manager.update_cart_item(user_id, product_id, 0)
        assert result.status == 'success'
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
        assert result.status == 'success'
        assert result.items_cleared == 3
        
        # Verify cart is empty
        cart = self.manager.get_cart(user_id)
        assert len(cart.items) == 0
        assert cart.total == 0
        
        # Verify inventory was released
        for product_id in ["TEST001", "TEST002", "TEST003"]:
            inv = self.manager.get_product_inventory(product_id)
            assert inv.reserved_quantity == 0
    
    def test_cart_with_invalid_product(self):
        """Test adding non-existent product to cart."""
        user_id = "test_user"
        
        result = self.manager.add_to_cart(user_id, "INVALID_PRODUCT", 1)
        assert result.status == 'failed'
        assert 'not found' in result.error.lower()
    
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