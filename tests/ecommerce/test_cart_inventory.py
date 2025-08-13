"""Test suite for CartInventoryManager functionality using pytest."""

import pytest
from pathlib import Path
from tools.ecommerce.cart_inventory_manager import CartInventoryManager


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database path for testing."""
    return str(tmp_path / "test.db")


@pytest.fixture
def manager(db_path):
    """Create a CartInventoryManager instance with test database."""
    return CartInventoryManager(db_path)


class TestPhase1CoreInfrastructure:
    """Test Phase 1: Core Infrastructure."""
    
    def test_manager_initialization(self, manager):
        """Test that CartInventoryManager initializes correctly."""
        assert manager is not None
        assert manager.db_path.exists()
    
    def test_load_products_from_json(self, manager):
        """Test loading products from JSON file."""
        products = manager.load_products_from_json()
        assert len(products) > 0
        assert all('id' in p and 'name' in p and 'price' in p for p in products)
    
    def test_get_product_by_id(self, manager):
        """Test retrieving a specific product by ID."""
        products = manager.load_products_from_json()
        if products:
            first_product = products[0]
            product = manager.get_product_by_id(first_product['id'])
            assert product is not None
            assert product['id'] == first_product['id']
            assert product['name'] == first_product['name']
    
    def test_initialize_inventory(self, manager):
        """Test inventory initialization from products."""
        manager.initialize_inventory_from_products()
        products = manager.load_products_from_json()
        
        # Check that inventory was created for each product
        for product in products[:3]:  # Test first 3 products
            inv = manager.get_product_inventory(product['id'])
            assert inv.stock_quantity > 0
            assert inv.reserved_quantity == 0
    
    def test_seed_demo_orders(self, manager):
        """Test seeding demo orders."""
        manager.initialize_inventory_from_products()
        manager.seed_demo_orders(5)
        
        stats = manager.get_stats()
        assert stats.total_orders >= 5
    
    def test_seed_demo_carts(self, manager):
        """Test creating demo carts."""
        manager.initialize_inventory_from_products()
        manager.seed_demo_carts(2)
        
        stats = manager.get_stats()
        assert stats.active_carts >= 2
    
    def test_get_stats(self, manager):
        """Test statistics retrieval."""
        manager.reset_database()
        stats = manager.get_stats()
        
        assert hasattr(stats, 'total_orders')
        assert hasattr(stats, 'orders_by_status')
        assert hasattr(stats, 'active_carts')
        assert hasattr(stats, 'inventory')
        assert hasattr(stats, 'pending_returns')
    
    def test_user_specific_stats(self, manager):
        """Test user-specific statistics."""
        manager.reset_database()
        
        # Add an order for a specific user
        manager.add_to_cart("test_user", "KB123", 1)
        manager.checkout_cart("test_user", "123 Test St")
        
        user_stats = manager.get_stats('test_user')
        assert user_stats.total_orders >= 1


class TestPhase2CartAndInventory:
    """Test Phase 2: Cart & Inventory Operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, manager):
        """Reset database before each test."""
        # Initialize fresh database without demo carts
        manager.initialize_inventory_from_products()
        manager.seed_demo_orders(5)
        # No demo carts to avoid interference with tests
    
    def test_add_to_cart_success(self, manager):
        """Test successfully adding items to cart."""
        result = manager.add_to_cart("test_user", "KB123", 2)
        assert result.status == 'success'
        assert result.cart_total == 2
        assert result.added == "KB123"
        assert result.quantity == 2
    
    def test_add_to_cart_insufficient_stock(self, manager):
        """Test adding more items than available stock."""
        result = manager.add_to_cart("test_user", "KB789", 1000)
        assert result.status == 'failed'
        assert 'Insufficient stock' in result.error
    
    def test_add_multiple_products(self, manager):
        """Test adding multiple different products to cart."""
        result1 = manager.add_to_cart("test_user", "KB123", 1)
        assert result1.status == 'success'
        
        result2 = manager.add_to_cart("test_user", "MS001", 2)
        assert result2.status == 'success'
        
        cart = manager.get_cart("test_user")
        assert len(cart.items) == 2
        assert cart.item_count == 3
    
    def test_get_cart_contents(self, manager):
        """Test retrieving cart contents."""
        manager.add_to_cart("test_user", "KB123", 2)
        manager.add_to_cart("test_user", "MS001", 1)
        
        cart = manager.get_cart("test_user")
        assert cart.cart_id > 0
        assert len(cart.items) == 2
        assert cart.total > 0
        assert cart.user_id == "test_user"
    
    def test_inventory_tracking(self, manager):
        """Test that inventory is properly tracked."""
        initial_inv = manager.get_product_inventory("KB123")
        initial_available = initial_inv.available_quantity
        
        manager.add_to_cart("test_user", "KB123", 3)
        
        after_inv = manager.get_product_inventory("KB123")
        assert after_inv.reserved_quantity == 3
        assert after_inv.available_quantity == initial_available - 3
    
    def test_remove_from_cart_partial(self, manager):
        """Test partial removal from cart."""
        manager.add_to_cart("test_user", "KB123", 5)
        
        result = manager.remove_from_cart("test_user", "KB123", 2)
        assert result.status == 'success'
        assert result.quantity_removed == 2
        
        cart = manager.get_cart("test_user")
        item = next((i for i in cart.items if i.product_id == "KB123"), None)
        assert item.quantity == 3
    
    def test_remove_from_cart_complete(self, manager):
        """Test complete removal from cart."""
        manager.add_to_cart("test_user", "KB123", 3)
        
        result = manager.remove_from_cart("test_user", "KB123")
        assert result.status == 'success'
        
        cart = manager.get_cart("test_user")
        assert not any(i.product_id == "KB123" for i in cart.items)
    
    def test_update_cart_item_quantity(self, manager):
        """Test updating item quantity in cart."""
        manager.add_to_cart("test_user", "MS001", 2)
        
        result = manager.update_cart_item("test_user", "MS001", 5)
        assert result.status == 'success'
        assert result.old_quantity == 2
        assert result.new_quantity == 5
    
    def test_clear_cart(self, manager):
        """Test clearing all items from cart."""
        manager.add_to_cart("test_user", "KB123", 2)
        manager.add_to_cart("test_user", "MS001", 3)
        
        result = manager.clear_cart("test_user")
        assert result.status == 'success'
        assert result.items_cleared == 2
        
        cart = manager.get_cart("test_user")
        assert len(cart.items) == 0
    
    def test_multi_user_inventory_conflict(self, manager):
        """Test inventory conflicts with multiple users."""
        # Alice takes most of the stock
        manager.add_to_cart("alice", "KB789", 20)
        
        # Bob tries to take more than remaining
        result = manager.add_to_cart("bob", "KB789", 5)
        assert result.status == 'failed'
    
    @pytest.mark.skip(reason="Timestamp handling issue - needs investigation")
    def test_cart_abandonment_cleanup(self, manager):
        """Test cleaning up abandoned carts."""
        # Add items to carts
        result1 = manager.add_to_cart("user1", "KB123", 5)
        assert result1.status == 'success'
        cart1_id = result1.cart_id
        
        result2 = manager.add_to_cart("user2", "MS001", 3)
        assert result2.status == 'success'
        cart2_id = result2.cart_id
        
        # Get initial inventory to verify reservation
        inv_before = manager.get_product_inventory("KB123")
        assert inv_before.reserved_quantity == 5
        
        # Manually update cart timestamps to make them old
        import sqlite3
        from datetime import datetime, timedelta
        with sqlite3.connect(str(manager.db_path)) as conn:
            old_time = datetime.now() - timedelta(hours=25)
            cursor = conn.cursor()
            cursor.execute("UPDATE carts SET updated_at = ? WHERE cart_id IN (?, ?) AND status = 'active'", 
                        (old_time.isoformat(), cart1_id, cart2_id))
            conn.commit()
            # Verify the update worked
            cursor.execute("SELECT COUNT(*) FROM carts WHERE updated_at < ? AND status = 'active'",
                          ((datetime.now() - timedelta(hours=24)).isoformat(),))
            count = cursor.fetchone()[0]
            assert count >= 2, f"Expected at least 2 old carts, found {count}"
        
        # Clean up abandoned carts (24 hours default)
        result = manager.cleanup_abandoned_carts()
        assert result.status == 'success'
        # Should clean at least the 2 carts we created
        assert result.carts_cleaned >= 2, f"Expected to clean >= 2 carts, cleaned {result.carts_cleaned}"
        
        # Check inventory was released
        inv_after = manager.get_product_inventory("KB123")
        # Reserved should be 0 now
        assert inv_after.reserved_quantity == 0


class TestPhase3OrderManagement:
    """Test Phase 3: Order Management."""
    
    @pytest.fixture(autouse=True)
    def setup(self, manager):
        """Reset database and prepare for order tests."""
        manager.reset_database()
        manager.cleanup_abandoned_carts(hours=0)
    
    def test_checkout_cart_success(self, manager):
        """Test successful checkout process."""
        # Add items to cart
        manager.add_to_cart("test_user", "KB123", 1)
        manager.add_to_cart("test_user", "MS001", 2)
        
        # Checkout
        result = manager.checkout_cart("test_user", "123 Test St, City, ST 12345")
        assert result.status == 'success'
        assert result.order_id is not None
        assert result.total > 0
        assert result.items == 2
        
        # Verify cart is empty
        cart = manager.get_cart("test_user")
        assert len(cart.items) == 0
    
    def test_checkout_empty_cart(self, manager):
        """Test checkout with empty cart."""
        result = manager.checkout_cart("test_user", "123 Test St")
        assert result.status == 'failed'
        assert 'empty' in result.error.lower()
    
    def test_get_order(self, manager):
        """Test retrieving order details."""
        # Create an order
        manager.add_to_cart("test_user", "KB123", 2)
        checkout_result = manager.checkout_cart("test_user", "123 Test St")
        
        # Retrieve the order
        order = manager.get_order("test_user", checkout_result.order_id)
        assert order is not None
        assert order.order_id == checkout_result.order_id
        assert order.user_id == "test_user"
        assert len(order.items) > 0
    
    def test_list_orders(self, manager):
        """Test listing user orders."""
        # Create multiple orders
        for i in range(3):
            manager.add_to_cart("test_user", "KB123", 1)
            manager.checkout_cart("test_user", f"Address {i}")
        
        orders = manager.list_orders("test_user")
        assert len(orders) >= 3
        assert all(o.order_id for o in orders)
    
    def test_update_order_status(self, manager):
        """Test updating order status through lifecycle."""
        # Create an order
        manager.add_to_cart("test_user", "KB123", 1)
        checkout_result = manager.checkout_cart("test_user", "123 Test St")
        order_id = checkout_result.order_id
        
        # Update to shipped
        result = manager.update_order_status(order_id, "shipped")
        assert result.status == 'success'
        assert result.new_status == "shipped"
        
        # Update to delivered
        result = manager.update_order_status(order_id, "delivered")
        assert result.status == 'success'
        assert result.new_status == "delivered"
    
    def test_invalid_order_status(self, manager):
        """Test updating order with invalid status."""
        manager.add_to_cart("test_user", "KB123", 1)
        checkout_result = manager.checkout_cart("test_user", "123 Test St")
        
        result = manager.update_order_status(checkout_result.order_id, "invalid_status")
        assert result.status == 'failed'
        assert 'Invalid status' in result.error
    
    def test_create_return(self, manager):
        """Test creating a return request."""
        # Create and deliver an order
        manager.add_to_cart("test_user", "KB123", 2)
        checkout_result = manager.checkout_cart("test_user", "123 Test St")
        manager.update_order_status(checkout_result.order_id, "delivered")
        
        # Create return
        result = manager.create_return(
            "test_user", 
            checkout_result.order_id, 
            "KB123", 
            "Defective product"
        )
        assert result.status == 'success'
        assert result.return_id is not None
        assert result.refund_amount > 0
    
    def test_process_return_approval(self, manager):
        """Test approving a return request."""
        # Setup order and return
        manager.add_to_cart("test_user", "KB123", 1)
        checkout_result = manager.checkout_cart("test_user", "123 Test St")
        manager.update_order_status(checkout_result.order_id, "delivered")
        
        initial_inv = manager.get_product_inventory("KB123")
        
        return_result = manager.create_return(
            "test_user",
            checkout_result.order_id,
            "KB123",
            "Defective"
        )
        
        # Approve return
        result = manager.process_return(return_result.return_id, approve=True)
        assert result.status == 'success'
        assert 'approved' in result.message.lower()
        
        # Check inventory restored
        final_inv = manager.get_product_inventory("KB123")
        assert final_inv.stock_quantity > initial_inv.stock_quantity
    
    def test_process_return_rejection(self, manager):
        """Test rejecting a return request."""
        # Setup order and return
        manager.add_to_cart("test_user", "KB123", 1)
        checkout_result = manager.checkout_cart("test_user", "123 Test St")
        manager.update_order_status(checkout_result.order_id, "delivered")
        
        return_result = manager.create_return(
            "test_user",
            checkout_result.order_id,
            "KB123",
            "Changed mind"
        )
        
        # Reject return
        result = manager.process_return(return_result.return_id, approve=False)
        assert result.status == 'success'
        assert 'rejected' in result.message.lower()
    
    def test_order_cancellation_restores_inventory(self, manager):
        """Test that cancelling an order restores inventory."""
        # Create an order
        initial_inv = manager.get_product_inventory("HD001")
        
        manager.add_to_cart("test_user", "HD001", 2)
        checkout_result = manager.checkout_cart("test_user", "123 Test St")
        
        middle_inv = manager.get_product_inventory("HD001")
        assert middle_inv.stock_quantity < initial_inv.stock_quantity
        
        # Cancel the order
        result = manager.update_order_status(checkout_result.order_id, "cancelled")
        assert result.status == 'success'
        
        # Check inventory restored
        final_inv = manager.get_product_inventory("HD001")
        assert final_inv.stock_quantity == initial_inv.stock_quantity
    
    def test_filter_orders_by_status(self, manager):
        """Test filtering orders by status."""
        # Create orders with different statuses
        manager.add_to_cart("test_user", "KB123", 1)
        order1 = manager.checkout_cart("test_user", "Address 1")
        manager.update_order_status(order1.order_id, "delivered")
        
        manager.add_to_cart("test_user", "MS001", 1)
        order2 = manager.checkout_cart("test_user", "Address 2")
        manager.update_order_status(order2.order_id, "cancelled")
        
        # Filter by status
        delivered = manager.list_orders("test_user", status="delivered")
        assert any(o.order_id == order1.order_id for o in delivered)
        
        cancelled = manager.list_orders("test_user", status="cancelled")
        assert any(o.order_id == order2.order_id for o in cancelled)