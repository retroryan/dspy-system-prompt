"""Returns processing tests for CartInventoryManager."""

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


class TestReturns:
    """Test return processing operations."""
    
    def setup_method(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager()
        self.db_path = self.db_manager.setup_test_db("test_returns")
        
        # Create products
        self.products_file = os.path.join(self.db_manager.test_dir, "data", "products.json")
        products = TestDataFactory.create_test_products(5)
        TestDataFactory.create_products_json(products, self.products_file)
        
        # Initialize manager
        self.manager = CartInventoryManager(self.db_path)
        self.manager.products_file = Path(self.products_file)
        self.manager.initialize_inventory_from_products()
        
        # Create a standard delivered order for testing returns
        self.user_id = "test_user"
        self.order_id = self._create_delivered_order()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db_manager.cleanup_all()
    
    def _create_delivered_order(self) -> str:
        """Helper to create a delivered order for testing returns."""
        # Add items to cart
        self.manager.add_to_cart(self.user_id, "TEST001", 2)
        self.manager.add_to_cart(self.user_id, "TEST002", 1)
        
        # Checkout
        result = self.manager.checkout_cart(self.user_id, "123 Test St")
        order_id = result.order_id
        
        # Mark as delivered
        self.manager.update_order_status(order_id, 'shipped')
        self.manager.update_order_status(order_id, 'delivered')
        
        return order_id
    
    def test_create_return_request(self):
        """Test creating a return request."""
        result = self.manager.create_return(
            self.user_id, self.order_id, "TEST001", "Defective product"
        )
        
        assert result.status == 'success'
        assert 'return_id' in result
        assert result.refund_amount > 0
        assert result.item_id == "TEST001"
        assert result.reason == "Defective product"
    
    def test_cannot_return_non_delivered_order(self):
        """Test that returns are only allowed for delivered/shipped orders."""
        # Create a processing order
        self.manager.add_to_cart(self.user_id, "TEST003", 1)
        result = self.manager.checkout_cart(self.user_id, "456 Test Ave")
        processing_order_id = result.order_id
        
        # Try to return from processing order
        result = self.manager.create_return(
            self.user_id, processing_order_id, "TEST003", "Changed mind"
        )
        
        assert result.status == 'failed'
        assert 'cannot return' in result.error.lower()
    
    def test_cannot_return_non_existent_item(self):
        """Test that we can't return an item not in the order."""
        result = self.manager.create_return(
            self.user_id, self.order_id, "TEST999", "Wrong item"
        )
        
        assert result.status == 'failed'
        assert 'not found in order' in result.error.lower()
    
    def test_approve_return(self):
        """Test approving a return request."""
        # Create return request
        return_result = self.manager.create_return(
            self.user_id, self.order_id, "TEST001", "Defective"
        )
        return_id = return_result.return_id
        
        # Get initial inventory
        initial_inv = self.manager.get_product_inventory("TEST001")
        initial_stock = initial_inv['stock_quantity']
        
        # Approve return
        result = self.manager.process_return(return_id, approve=True)
        
        assert result.status == 'success'
        assert result.return_status == 'approved'
        assert 'refunded' in result.message.lower()
        
        # Verify inventory was restored
        final_inv = self.manager.get_product_inventory("TEST001")
        assert final_inv['stock_quantity'] == initial_stock + 2  # 2 items were returned
    
    def test_reject_return(self):
        """Test rejecting a return request."""
        # Create return request
        return_result = self.manager.create_return(
            self.user_id, self.order_id, "TEST001", "Changed mind"
        )
        return_id = return_result.return_id
        
        # Get initial inventory
        initial_inv = self.manager.get_product_inventory("TEST001")
        initial_stock = initial_inv['stock_quantity']
        
        # Reject return
        result = self.manager.process_return(return_id, approve=False)
        
        assert result.status == 'success'
        assert result.return_status == 'rejected'
        assert 'rejected' in result.message.lower()
        
        # Verify inventory was NOT restored
        final_inv = self.manager.get_product_inventory("TEST001")
        assert final_inv['stock_quantity'] == initial_stock  # No change
    
    def test_cannot_process_return_twice(self):
        """Test that a return can't be processed twice."""
        # Create and approve a return
        return_result = self.manager.create_return(
            self.user_id, self.order_id, "TEST001", "Defective"
        )
        return_id = return_result.return_id
        
        # Process once
        self.manager.process_return(return_id, approve=True)
        
        # Try to process again
        result = self.manager.process_return(return_id, approve=True)
        
        assert result.status == 'failed'
        assert 'already processed' in result.error.lower()
    
    def test_return_wrong_user(self):
        """Test that users can't return other users' orders."""
        # Try to return with wrong user
        result = self.manager.create_return(
            "wrong_user", self.order_id, "TEST001", "Not mine"
        )
        
        assert result.status == 'failed'
        assert 'not found' in result.error.lower()
    
    def test_multiple_returns_same_order(self):
        """Test multiple return requests for same order."""
        # Return first item
        result1 = self.manager.create_return(
            self.user_id, self.order_id, "TEST001", "Defective"
        )
        assert result1.status == 'success'
        
        # Return second item
        result2 = self.manager.create_return(
            self.user_id, self.order_id, "TEST002", "Wrong item"
        )
        assert result2.status == 'success'
        
        # Verify both returns exist with different IDs
        assert result1.return_id != result2.return_id
    
    def test_return_refund_amount(self):
        """Test that refund amount matches item price."""
        # Get order details
        order = self.manager.get_order(self.user_id, self.order_id)
        
        # Find TEST001 item details
        test001_item = None
        for item in order['items']:
            if item['product_id'] == "TEST001":
                test001_item = item
                break
        
        assert test001_item is not None
        expected_refund = test001_item['subtotal']
        
        # Create return
        result = self.manager.create_return(
            self.user_id, self.order_id, "TEST001", "Defective"
        )
        
        assert abs(result.refund_amount - expected_refund) < 0.01
    
    def test_return_shipped_order(self):
        """Test that shipped (not yet delivered) orders can be returned."""
        # Create a shipped order
        self.manager.add_to_cart(self.user_id, "TEST003", 1)
        result = self.manager.checkout_cart(self.user_id, "789 Test Blvd")
        shipped_order_id = result.order_id
        self.manager.update_order_status(shipped_order_id, 'shipped')
        
        # Should be able to create return
        result = self.manager.create_return(
            self.user_id, shipped_order_id, "TEST003", "In transit return"
        )
        
        assert result.status == 'success'
    
    def test_inventory_restoration_calculation(self):
        """Test that inventory restoration is calculated correctly."""
        # Track exact inventory changes
        product_id = "TEST001"
        
        # Get stock after delivered order
        before_return = self.manager.get_product_inventory(product_id)
        stock_before = before_return['stock_quantity']
        
        # The order had 2 units of TEST001
        expected_restoration = 2
        
        # Create and approve return
        return_result = self.manager.create_return(
            self.user_id, self.order_id, product_id, "Defective"
        )
        self.manager.process_return(return_result.return_id, approve=True)
        
        # Check stock after return
        after_return = self.manager.get_product_inventory(product_id)
        stock_after = after_return['stock_quantity']
        
        assert stock_after == stock_before + expected_restoration
    
    def test_partial_return_scenario(self):
        """Test returning only some items from an order."""
        # Order has TEST001 (qty 2) and TEST002 (qty 1)
        order = self.manager.get_order(self.user_id, self.order_id)
        initial_item_count = len(order['items'])
        
        # Return only TEST002
        result = self.manager.create_return(
            self.user_id, self.order_id, "TEST002", "Wrong item"
        )
        assert result.status == 'success'
        
        # Approve return
        self.manager.process_return(result.return_id, approve=True)
        
        # Order still exists with all items (returns don't modify order history)
        order = self.manager.get_order(self.user_id, self.order_id)
        assert len(order['items']) == initial_item_count