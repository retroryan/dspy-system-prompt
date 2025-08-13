"""Database operations tests for CartInventoryManager."""

import pytest
import sqlite3
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tools.ecommerce.cart_inventory_manager import CartInventoryManager
from tests.ecommerce.test_utils import (
    TestDatabaseManager, TestDataFactory, DatabaseAssertions, validate_database_state
)


class TestDatabaseOperations:
    """Test database operations and integrity."""
    
    def setup_method(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager()
        self.db_path = self.db_manager.setup_test_db("test_db_ops")
        
        # Create products.json in temp directory
        self.products_file = os.path.join(self.db_manager.test_dir, "data", "products.json")
        products = TestDataFactory.create_test_products(5)
        TestDataFactory.create_products_json(products, self.products_file)
        
        # Initialize manager with test database
        self.manager = CartInventoryManager(self.db_path)
        self.manager.products_file = Path(self.products_file)
        self.manager.initialize_inventory_from_products()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db_manager.cleanup_all()
    
    def test_database_creation(self):
        """Test that all tables are created correctly."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check all tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['cart_items', 'carts', 'inventory', 
                          'order_items', 'orders', 'returns']
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"
        
        conn.close()
    
    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are enforced."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Try to insert cart item for non-existent cart
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO cart_items (cart_id, product_id, quantity, price_at_time)
                VALUES (9999, 'TEST001', 1, 10.00)
            """)
        
        # Try to insert order item for non-existent order
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                VALUES ('NONEXISTENT', 'TEST001', 1, 10.00, 10.00)
            """)
        
        conn.close()
    
    def test_unique_constraints(self):
        """Test unique constraints work correctly."""
        user_id = "test_user"
        
        # Add item to cart
        self.manager.add_to_cart(user_id, "TEST001", 1)
        
        # Try to add same item again - should update quantity, not duplicate
        result = self.manager.add_to_cart(user_id, "TEST001", 2)
        assert result.status == 'success'
        
        # Check there's only one row for this product in cart
        cart = self.manager.get_cart(user_id)
        product_counts = {}
        for item in cart.items:
            product_counts[item.product_id] = product_counts.get(item.product_id, 0) + 1
        
        assert product_counts.get("TEST001", 0) == 1, "Duplicate cart items found"
        
        # Verify quantity was updated
        for item in cart.items:
            if item.product_id == "TEST001":
                assert item.quantity == 3, f"Expected quantity 3, got {item.quantity}"
    
    def test_transaction_rollback(self):
        """Test that transactions rollback on error."""
        user_id = "test_user"
        
        # Add items to cart
        self.manager.add_to_cart(user_id, "TEST001", 1)
        
        # Get initial inventory
        initial_inv = self.manager.get_product_inventory("TEST001")
        
        # Try to checkout with an invalid operation that will fail
        # We'll simulate failure by reducing stock to 0 after reservation
        with self.manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inventory SET stock_quantity = 0 WHERE product_id = 'TEST001'
            """)
        
        result = self.manager.checkout_cart(user_id, "123 Test St")
        
        # Restore stock
        with self.manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inventory SET stock_quantity = 50 WHERE product_id = 'TEST001'
            """)
        
        # Checkout should have failed
        assert result.status == 'failed'
        
        # Verify inventory wasn't changed
        final_inv = self.manager.get_product_inventory("TEST001")
        assert final_inv['reserved_quantity'] == initial_inv['reserved_quantity']
        
        # Verify order wasn't created
        orders = self.manager.list_orders(user_id)
        assert len(orders) == 0
    
    def test_concurrent_connections(self):
        """Test handling of concurrent database connections."""
        user1 = "user1"
        user2 = "user2"
        
        # TEST001 has 90 stock (100 - 1*10)
        # Both users try to add 50 items each (total 100, but only 90 available)
        result1 = self.manager.add_to_cart(user1, "TEST001", 50)
        result2 = self.manager.add_to_cart(user2, "TEST001", 50)
        
        # First should succeed, second should fail (only 90 in stock)
        assert result1.status == 'success'
        assert result2.status == 'failed'  # Not enough stock
        
        # Check inventory is correctly reserved
        inv = self.manager.get_product_inventory("TEST001")
        assert inv['reserved_quantity'] == 50  # Only first user's reservation
    
    def test_index_usage(self):
        """Test that indexes are created and can be used."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_inventory_stock',
            'idx_carts_user_id',
            'idx_carts_status',
            'idx_cart_items_cart_id',
            'idx_orders_user_id',
            'idx_orders_status',
            'idx_order_items_order_id',
            'idx_returns_user_id',
            'idx_returns_order_id'
        ]
        
        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} not found"
        
        conn.close()
    
    def test_database_integrity_check(self):
        """Test database integrity validation."""
        # Add some data
        user_id = "test_user"
        self.manager.add_to_cart(user_id, "TEST001", 1)
        result = self.manager.checkout_cart(user_id, "123 Test St")
        
        # Validate database state
        validation = validate_database_state(self.db_path)
        
        assert validation.valid, f"Database validation failed: {validation['issues']}"
        assert validation['stats']['total_orders'] == 1
        assert validation['stats']['active_carts'] == 0  # Cart was checked out
    
    def test_cascade_deletes(self):
        """Test that cascade deletes work correctly."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create a cart with items
        user_id = "test_user"
        self.manager.add_to_cart(user_id, "TEST001", 1)
        self.manager.add_to_cart(user_id, "TEST002", 2)
        
        # Get cart ID
        cart = self.manager.get_cart(user_id)
        cart_id = cart.cart_id
        
        # Verify items exist
        cursor.execute("SELECT COUNT(*) FROM cart_items WHERE cart_id = ?", (cart_id,))
        assert cursor.fetchone()[0] == 2
        
        # Delete the cart
        cursor.execute("DELETE FROM carts WHERE cart_id = ?", (cart_id,))
        conn.commit()
        
        # Verify items were cascade deleted
        cursor.execute("SELECT COUNT(*) FROM cart_items WHERE cart_id = ?", (cart_id,))
        assert cursor.fetchone()[0] == 0
        
        conn.close()