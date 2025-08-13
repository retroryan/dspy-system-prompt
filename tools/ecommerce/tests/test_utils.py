"""Test utilities for CartInventoryManager unit tests."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import random
import string


class TestDatabaseManager:
    """Manages isolated test databases for each test suite."""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="ecommerce_test_")
        self.test_dbs = []
    
    def setup_test_db(self, test_name: str) -> str:
        """Create isolated test database with unique name.
        
        Args:
            test_name: Name of the test for database naming
            
        Returns:
            Path to test database file
        """
        db_name = f"{test_name}_{self._generate_id()}.db"
        db_path = os.path.join(self.test_dir, db_name)
        self.test_dbs.append(db_path)
        return db_path
    
    def teardown_test_db(self, db_path: str):
        """Clean up test database after tests.
        
        Args:
            db_path: Path to database to remove
        """
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except:
                pass  # Ignore errors during cleanup
            
        if db_path in self.test_dbs:
            self.test_dbs.remove(db_path)
    
    def cleanup_all(self):
        """Clean up all test databases and temp directory."""
        for db_path in self.test_dbs[:]:
            self.teardown_test_db(db_path)
        
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _generate_id(self) -> str:
        """Generate unique ID for test database."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class TestDataFactory:
    """Factory for creating consistent test data."""
    
    @staticmethod
    def create_test_products(count: int = 5) -> List[Dict]:
        """Generate deterministic test products.
        
        Args:
            count: Number of products to generate
            
        Returns:
            List of product dictionaries
        """
        products = []
        categories = ["Electronics", "Clothing", "Books", "Sports", "Home"]
        
        for i in range(count):
            product = {
                "id": f"TEST{i:03d}",
                "name": f"Test Product {i}",
                "description": f"Description for test product {i}",
                "price": 10.00 + (i * 5),
                "category": categories[i % len(categories)],
                "stock": 100 - (i * 10)  # Varying stock levels
            }
            products.append(product)
        
        return products
    
    @staticmethod
    def create_test_user(user_id: Optional[str] = None) -> str:
        """Create test user with predictable ID.
        
        Args:
            user_id: Optional specific user ID
            
        Returns:
            User ID string
        """
        if user_id:
            return user_id
        
        # Generate predictable user ID
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return f"test_user_{random_suffix}"
    
    @staticmethod
    def create_test_cart_items(product_ids: List[str]) -> List[Dict]:
        """Create cart items for testing.
        
        Args:
            product_ids: List of product IDs to add to cart
            
        Returns:
            List of cart item dictionaries
        """
        items = []
        for i, product_id in enumerate(product_ids):
            items.append({
                "product_id": product_id,
                "quantity": (i % 3) + 1,  # 1-3 quantity
                "price": 10.00 + (i * 5)
            })
        return items
    
    @staticmethod
    def create_products_json(products: List[Dict], file_path: str):
        """Create a products.json file for testing.
        
        Args:
            products: List of product dictionaries
            file_path: Path where to save the products.json
        """
        data = {"products": products}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)


class DatabaseAssertions:
    """Assertion helpers for database state validation."""
    
    @staticmethod
    def assert_inventory_consistent(manager, product_id: str):
        """Verify inventory math: available = stock - reserved.
        
        Args:
            manager: CartInventoryManager instance
            product_id: Product to check
            
        Raises:
            AssertionError: If inventory math is incorrect
        """
        inv = manager.get_product_inventory(product_id)
        
        expected_available = inv['stock_quantity'] - inv['reserved_quantity']
        actual_available = inv['available_quantity']
        
        assert expected_available == actual_available, \
            f"Inventory inconsistent for {product_id}: " \
            f"stock={inv['stock_quantity']}, reserved={inv['reserved_quantity']}, " \
            f"available={actual_available} (expected {expected_available})"
    
    @staticmethod
    def assert_cart_total_correct(manager, user_id: str):
        """Verify cart total matches sum of items.
        
        Args:
            manager: CartInventoryManager instance
            user_id: User whose cart to check
            
        Raises:
            AssertionError: If cart total is incorrect
        """
        cart = manager.get_cart(user_id)
        
        calculated_total = sum(item.subtotal for item in cart.items)
        
        # Allow for small floating point differences
        assert abs(calculated_total - cart.total) < 0.01, \
            f"Cart total mismatch for user {user_id}: " \
            f"sum of items={calculated_total:.2f}, cart.total={cart.total:.2f}"
    
    @staticmethod
    def assert_order_complete(manager, user_id: str, order_id: str):
        """Verify order has all required fields.
        
        Args:
            manager: CartInventoryManager instance
            user_id: User who owns the order
            order_id: Order to check
            
        Raises:
            AssertionError: If order is incomplete
        """
        order = manager.get_order(user_id, order_id)
        
        required_fields = ['order_id', 'user_id', 'status', 'total', 
                          'shipping_address', 'items', 'created_at']
        
        for field in required_fields:
            assert field in order, f"Order {order_id} missing required field: {field}"
        
        assert len(order['items']) > 0, f"Order {order_id} has no items"
        
        # Verify each item has required fields
        for item in order['items']:
            item_fields = ['product_id', 'product_name', 'quantity', 
                          'unit_price', 'subtotal']
            for field in item_fields:
                assert field in item, \
                    f"Order item missing field {field} in order {order_id}"
    
    @staticmethod
    def assert_database_empty(manager):
        """Verify database has no data (useful for cleanup tests).
        
        Args:
            manager: CartInventoryManager instance
            
        Raises:
            AssertionError: If database contains data
        """
        stats = manager.get_stats()
        
        assert stats['total_orders'] == 0, f"Database has {stats['total_orders']} orders"
        assert stats['active_carts'] == 0, f"Database has {stats['active_carts']} active carts"
        

def validate_database_state(db_path: str) -> Dict[str, Any]:
    """Run integrity checks on database.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Dict with validation results
    """
    import sqlite3
    
    issues = []
    stats = {}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check foreign key integrity
        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()
        if fk_issues:
            issues.append(f"Foreign key violations: {fk_issues}")
        
        # Check for orphaned cart items
        cursor.execute("""
            SELECT COUNT(*) FROM cart_items ci
            LEFT JOIN carts c ON ci.cart_id = c.cart_id
            WHERE c.cart_id IS NULL
        """)
        orphaned_cart_items = cursor.fetchone()[0]
        if orphaned_cart_items > 0:
            issues.append(f"Orphaned cart items: {orphaned_cart_items}")
        
        # Check for orphaned order items
        cursor.execute("""
            SELECT COUNT(*) FROM order_items oi
            LEFT JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_id IS NULL
        """)
        orphaned_order_items = cursor.fetchone()[0]
        if orphaned_order_items > 0:
            issues.append(f"Orphaned order items: {orphaned_order_items}")
        
        # Validate inventory math
        cursor.execute("""
            SELECT product_id, stock_quantity, reserved_quantity
            FROM inventory
            WHERE reserved_quantity > stock_quantity
        """)
        bad_inventory = cursor.fetchall()
        if bad_inventory:
            issues.append(f"Invalid inventory (reserved > stock): {bad_inventory}")
        
        # Get stats
        cursor.execute("SELECT COUNT(*) FROM orders")
        stats['total_orders'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM carts WHERE status = 'active'")
        stats['active_carts'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM inventory")
        stats['products'] = cursor.fetchone()[0]
        
        conn.close()
        
    except Exception as e:
        issues.append(f"Database validation error: {str(e)}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "stats": stats
    }