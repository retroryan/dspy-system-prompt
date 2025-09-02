"""Cart and Inventory Management System for E-commerce Demo.

This module provides persistent storage for carts, orders, and inventory using SQLite.
Products remain in products.json for easy editing while all stateful data is in SQLite.
"""

import sqlite3
import json
import random
import string
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from .models import (
    Cart, CartItem, 
    AddToCartOutput, RemoveFromCartOutput, UpdateCartItemOutput,
    ClearCartOutput, CheckoutOutput, Order, OrderItem, OrderSummary,
    UpdateOrderStatusOutput, CreateReturnOutput, ProcessReturnOutput,
    InventoryStatus, UpdateStockOutput, StatsOutput, CleanupCartsOutput
)


class CartInventoryManager:
    """Manages cart and inventory operations with SQLite persistence."""
    
    def __init__(self, db_path: str = None):
        """Initialize the manager with a database connection.
        
        Args:
            db_path: Path to SQLite database file (defaults to tools/db_files/ecommerce_demo.db)
        """
        if db_path is None:
            # Default to tools/db_files directory
            db_dir = Path(__file__).parent.parent / "db_files"
            db_dir.mkdir(exist_ok=True)
            self.db_path = db_dir / "ecommerce_demo.db"
        else:
            self.db_path = Path(db_path)
        self.products_file = Path(__file__).parent.parent / "data" / "products.json"
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic rollback on error."""
        conn = sqlite3.connect(self.db_path, isolation_level='IMMEDIATE')
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Inventory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    product_id TEXT PRIMARY KEY,
                    stock_quantity INTEGER NOT NULL DEFAULT 0,
                    reserved_quantity INTEGER NOT NULL DEFAULT 0,
                    last_restocked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_stock 
                ON inventory(stock_quantity)
            """)
            
            # Carts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS carts (
                    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_carts_user_id 
                ON carts(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_carts_status 
                ON carts(status)
            """)
            
            # Cart items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cart_items (
                    cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cart_id INTEGER NOT NULL,
                    product_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price_at_time DECIMAL(10, 2) NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cart_id) REFERENCES carts(cart_id) ON DELETE CASCADE,
                    UNIQUE(cart_id, product_id)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cart_items_cart_id 
                ON cart_items(cart_id)
            """)
            
            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    cart_id INTEGER,
                    total_amount DECIMAL(10, 2) NOT NULL,
                    status TEXT DEFAULT 'pending',
                    shipping_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_user_id 
                ON orders(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_status 
                ON orders(status)
            """)
            
            # Order items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    subtotal DECIMAL(10, 2) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_items_order_id 
                ON order_items(order_id)
            """)
            
            # Returns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS returns (
                    return_id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    refund_amount DECIMAL(10, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_returns_user_id 
                ON returns(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_returns_order_id 
                ON returns(order_id)
            """)
    
    def load_products_from_json(self) -> List[Dict[str, Any]]:
        """Load products from products.json file.
        
        Returns:
            List of product dictionaries
        """
        if not self.products_file.exists():
            return []
        
        with open(self.products_file, 'r') as f:
            data = json.load(f)
            return data.get('products', [])
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details from products.json.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product dictionary or None if not found
        """
        products = self.load_products_from_json()
        for product in products:
            if product['id'] == product_id:
                return product
        return None
    
    def initialize_inventory_from_products(self):
        """Initialize inventory table from products.json.
        
        Reads product stock from products.json and creates/updates inventory records.
        """
        products = self.load_products_from_json()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for product in products:
                stock = product.get('stock', 100)  # Default to 100 if no stock specified
                
                cursor.execute("""
                    INSERT OR REPLACE INTO inventory 
                    (product_id, stock_quantity, reserved_quantity, last_restocked, updated_at)
                    VALUES (?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (product['id'], stock))
    
    def seed_demo_orders(self, num_orders: int = 20):
        """Seed database with demo orders.
        
        First loads orders from orders.json if available, then creates
        additional random orders if needed to reach num_orders.
        
        Args:
            num_orders: Minimum number of demo orders to create
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, load orders from orders.json if it exists
            orders_file = Path(__file__).parent.parent / "data" / "orders.json"
            orders_loaded = 0
            
            if orders_file.exists():
                try:
                    with open(orders_file, 'r') as f:
                        orders_data = json.load(f)
                        
                    for order in orders_data.get('orders', []):
                        # Insert order
                        order_date = datetime.strptime(order['order_date'], '%Y-%m-%d') if isinstance(order['order_date'], str) else order['order_date']
                        cursor.execute("""
                            INSERT INTO orders 
                            (order_id, user_id, total_amount, status, shipping_address, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            order['order_id'],
                            order.get('user_id', 'demo_user'),  # Use user_id field
                            order['total'],
                            order['status'],
                            order['shipping_address'],
                            order_date,
                            order_date
                        ))
                        
                        # Insert order items
                        for item in order['items']:
                            cursor.execute("""
                                INSERT INTO order_items 
                                (order_id, product_id, quantity, unit_price, subtotal)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                order['order_id'],
                                item['item_id'],
                                item['quantity'],
                                item['price'],
                                item['price'] * item['quantity']
                            ))
                        
                        orders_loaded += 1
                        
                except Exception as e:
                    print(f"Warning: Could not load orders from orders.json: {e}")
            
            # Then create additional random orders if needed
            demo_users = ['demo_user', 'alice', 'bob', 'charlie', 'diana', 'eve', 'frank', 
                          'grace', 'henry', 'isabella', 'jack', 'kate', 'liam']
            statuses = ['pending', 'processing', 'shipped', 'delivered']
            status_weights = [0.1, 0.2, 0.3, 0.4]  # More delivered orders
            
            products = self.load_products_from_json()
            if not products:
                print("No products found in products.json")
                return
            
            # Only create additional random orders if we need more
            for i in range(orders_loaded, num_orders):
                # Generate order details
                user_id = random.choice(demo_users)
                order_id = f"ORD{1000 + i:04d}"
                order_date = datetime.now() - timedelta(days=random.randint(1, 30))
                status = random.choices(statuses, weights=status_weights)[0]
                
                # Random selection of 1-4 products
                num_items = random.randint(1, min(4, len(products)))
                order_items = random.sample(products, k=num_items)
                
                # Calculate total
                total = 0
                items_data = []
                for item in order_items:
                    quantity = random.randint(1, 3)
                    price = item['price']
                    subtotal = price * quantity
                    total += subtotal
                    items_data.append({
                        'product_id': item['id'],
                        'quantity': quantity,
                        'unit_price': price,
                        'subtotal': subtotal
                    })
                
                # Random shipping address
                addresses = [
                    "123 Main St, Boston, MA 02101",
                    "456 Oak Ave, New York, NY 10001",
                    "789 Pine Rd, San Francisco, CA 94102",
                    "321 Elm St, Chicago, IL 60601",
                    "654 Maple Dr, Austin, TX 78701",
                    "987 Cedar Ln, Seattle, WA 98101"
                ]
                shipping_address = random.choice(addresses)
                
                # Insert order
                cursor.execute("""
                    INSERT INTO orders 
                    (order_id, user_id, total_amount, status, shipping_address, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (order_id, user_id, total, status, shipping_address, order_date, order_date))
                
                # Insert order items
                for item in items_data:
                    cursor.execute("""
                        INSERT INTO order_items 
                        (order_id, product_id, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (order_id, item['product_id'], item['quantity'], 
                          item['unit_price'], item['subtotal']))
            
            # Add specific high-value orders for demo_user for testing
            # Find laptop and monitor products
            laptop_products = [p for p in products if 'laptop' in p['name'].lower()]
            monitor_products = [p for p in products if 'monitor' in p['name'].lower()]
            
            # Create a delivered order with laptop for demo_user (over $300)
            if laptop_products:
                laptop = laptop_products[0]
                order_id = f"ORD2020"
                order_date = datetime.now() - timedelta(days=5)  # Recent order
                
                cursor.execute("""
                    INSERT INTO orders 
                    (order_id, user_id, total_amount, status, shipping_address, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (order_id, 'demo_user', laptop['price'], 'delivered', 
                      '789 Tech Ave, Demo City, CA 90210', order_date, order_date))
                
                cursor.execute("""
                    INSERT INTO order_items 
                    (order_id, product_id, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, laptop['id'], 1, laptop['price'], laptop['price']))
            
            # Create another high-value order with monitor for demo_user
            if monitor_products:
                monitor = monitor_products[0]
                order_id = f"ORD2021"
                order_date = datetime.now() - timedelta(days=10)  # Within past month
                
                cursor.execute("""
                    INSERT INTO orders 
                    (order_id, user_id, total_amount, status, shipping_address, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (order_id, 'demo_user', monitor['price'], 'delivered',
                      '789 Tech Ave, Demo City, CA 90210', order_date, order_date))
                
                cursor.execute("""
                    INSERT INTO order_items 
                    (order_id, product_id, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, monitor['id'], 1, monitor['price'], monitor['price']))
            
            conn.commit()
    
    def seed_demo_carts(self, num_carts: int = 5):
        """Create some active carts for demo users.
        
        Args:
            num_carts: Number of demo carts to create
        """
        demo_users = ['demo_user_1', 'demo_user_2', 'demo_user_3', 'shopper_1', 'shopper_2']
        products = self.load_products_from_json()
        
        if not products:
            print("No products found in products.json")
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for i in range(min(num_carts, len(demo_users))):
                user_id = demo_users[i]
                
                # Create cart
                cursor.execute("""
                    INSERT INTO carts (user_id, status)
                    VALUES (?, 'active')
                """, (user_id,))
                cart_id = cursor.lastrowid
                
                # Add 1-3 random items
                num_items = random.randint(1, min(3, len(products)))
                cart_products = random.sample(products, k=num_items)
                
                for product in cart_products:
                    quantity = random.randint(1, 2)
                    
                    # Reserve inventory
                    cursor.execute("""
                        UPDATE inventory 
                        SET reserved_quantity = reserved_quantity + ?
                        WHERE product_id = ? 
                        AND stock_quantity >= reserved_quantity + ?
                    """, (quantity, product['id'], quantity))
                    
                    # Add to cart
                    cursor.execute("""
                        INSERT INTO cart_items 
                        (cart_id, product_id, quantity, price_at_time)
                        VALUES (?, ?, ?, ?)
                    """, (cart_id, product['id'], quantity, product['price']))
    
    def reset_database(self):
        """Reset database to initial state with demo data.
        
        1. Clear all tables
        2. Initialize inventory from products.json
        3. Seed demo orders
        4. Create some active carts for demo users
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear all tables in correct order (respecting foreign keys)
            cursor.execute("DELETE FROM returns")
            cursor.execute("DELETE FROM order_items")
            cursor.execute("DELETE FROM orders")
            cursor.execute("DELETE FROM cart_items")
            cursor.execute("DELETE FROM carts")
            cursor.execute("DELETE FROM inventory")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='carts'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='cart_items'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='order_items'")
        
        # Reinitialize with demo data
        self.initialize_inventory_from_products()
        self.seed_demo_orders(20)
        self.seed_demo_carts(5)
        
        print("Database reset complete with demo data")
    
    def get_stats(self, user_id: Optional[str] = None) -> StatsOutput:
        """Get statistics about carts and orders.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            StatsOutput with various statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total orders
            if user_id:
                cursor.execute("SELECT COUNT(*) as count FROM orders WHERE user_id = ?", (user_id,))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM orders")
            stats['total_orders'] = cursor.fetchone()['count']
            
            # Orders by status
            if user_id:
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM orders 
                    WHERE user_id = ?
                    GROUP BY status
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM orders 
                    GROUP BY status
                """)
            stats['orders_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Active carts
            if user_id:
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM carts 
                    WHERE status = 'active' AND user_id = ?
                """, (user_id,))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM carts WHERE status = 'active'")
            stats['active_carts'] = cursor.fetchone()['count']
            
            # Inventory summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_products,
                    SUM(stock_quantity) as total_stock,
                    SUM(reserved_quantity) as total_reserved
                FROM inventory
            """)
            inv = cursor.fetchone()
            stats['inventory'] = {
                'total_products': inv['total_products'],
                'total_stock': inv['total_stock'] or 0,
                'total_reserved': inv['total_reserved'] or 0,
                'available_stock': (inv['total_stock'] or 0) - (inv['total_reserved'] or 0)
            }
            
            # Pending returns
            if user_id:
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM returns 
                    WHERE status = 'pending' AND user_id = ?
                """, (user_id,))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM returns WHERE status = 'pending'")
            stats['pending_returns'] = cursor.fetchone()['count']
            
            return StatsOutput(**stats)
    
    # =============================================================================
    # Phase 2: Cart Management Methods
    # =============================================================================
    
    def get_or_create_cart(self, user_id: str) -> int:
        """Get active cart for user or create new one.
        
        Args:
            user_id: User identifier
            
        Returns:
            cart_id: ID of the active cart
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check for existing active cart
            cursor.execute("""
                SELECT cart_id FROM carts 
                WHERE user_id = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                return result['cart_id']
            
            # Create new cart
            cursor.execute("""
                INSERT INTO carts (user_id, status)
                VALUES (?, 'active')
            """, (user_id,))
            
            return cursor.lastrowid
    
    def add_to_cart(self, user_id: str, product_id: str, quantity: int) -> AddToCartOutput:
        """Add product to user's cart with inventory validation.
        
        Args:
            user_id: User identifier
            product_id: Product to add
            quantity: Quantity to add
            
        Returns:
            AddToCartOutput with cart status and any errors
        """
        # Get product details
        product = self.get_product_by_id(product_id)
        if not product:
            return AddToCartOutput(
                error=f"Product {product_id} not found", 
                status="failed"
            )
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check inventory availability
                if not self.check_availability(product_id, quantity):
                    cursor.execute("""
                        SELECT stock_quantity, reserved_quantity
                        FROM inventory WHERE product_id = ?
                    """, (product_id,))
                    inv = cursor.fetchone()
                    available = (inv['stock_quantity'] - inv['reserved_quantity']) if inv else 0
                    return AddToCartOutput(
                        error=f"Insufficient stock. Only {available} items available.",
                        product_id=product_id,
                        requested_quantity=quantity,
                        available_stock=available,
                        status="failed"
                    )
                
                # Get or create cart
                cart_id = self.get_or_create_cart(user_id)
                
                # Check if item already in cart
                cursor.execute("""
                    SELECT quantity FROM cart_items
                    WHERE cart_id = ? AND product_id = ?
                """, (cart_id, product_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update quantity
                    new_quantity = existing['quantity'] + quantity
                    
                    # Check total availability
                    if not self.check_availability(product_id, new_quantity):
                        return AddToCartOutput(
                            error="Cannot add more - insufficient stock",
                            product_id=product_id,
                            current_in_cart=existing['quantity'],
                            requested_additional=quantity,
                            status="failed"
                        )
                    
                    # Release old reservation
                    self.release_inventory(product_id, existing['quantity'])
                    
                    # Reserve new total
                    self.reserve_inventory(product_id, new_quantity)
                    
                    # Update cart item
                    cursor.execute("""
                        UPDATE cart_items 
                        SET quantity = ?, price_at_time = ?
                        WHERE cart_id = ? AND product_id = ?
                    """, (new_quantity, product['price'], cart_id, product_id))
                else:
                    # Reserve inventory
                    if not self.reserve_inventory(product_id, quantity):
                        return AddToCartOutput(
                            error="Failed to reserve inventory",
                            product_id=product_id,
                            status="failed"
                        )
                    
                    # Add new item to cart
                    cursor.execute("""
                        INSERT INTO cart_items (cart_id, product_id, quantity, price_at_time)
                        VALUES (?, ?, ?, ?)
                    """, (cart_id, product_id, quantity, product['price']))
                
                # Update cart timestamp
                cursor.execute("""
                    UPDATE carts SET updated_at = CURRENT_TIMESTAMP
                    WHERE cart_id = ?
                """, (cart_id,))
                
                # Get updated cart totals
                cursor.execute("""
                    SELECT COUNT(DISTINCT product_id) as item_count,
                           SUM(quantity) as total_items,
                           SUM(quantity * price_at_time) as total
                    FROM cart_items
                    WHERE cart_id = ?
                """, (cart_id,))
                
                totals = cursor.fetchone()
                
                return AddToCartOutput(
                    cart_id=cart_id,
                    cart_total=totals['total_items'] or 0,
                    cart_value=float(totals['total'] or 0),
                    added=product_id,
                    product_name=product['name'],
                    price=product['price'],
                    quantity=quantity,
                    status="success"
                )
                
        except Exception as e:
            return AddToCartOutput(error=str(e), status="failed")
    
    def remove_from_cart(self, user_id: str, product_id: str, quantity: Optional[int] = None) -> RemoveFromCartOutput:
        """Remove product from cart (partial or complete).
        
        Args:
            user_id: User identifier
            product_id: Product to remove
            quantity: Optional quantity to remove (None = remove all)
            
        Returns:
            RemoveFromCartOutput with updated cart status
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get active cart
                cursor.execute("""
                    SELECT cart_id FROM carts 
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id,))
                
                cart_result = cursor.fetchone()
                if not cart_result:
                    return RemoveFromCartOutput(error="No active cart found", status="failed")
                
                cart_id = cart_result['cart_id']
                
                # Get current item in cart
                cursor.execute("""
                    SELECT quantity FROM cart_items
                    WHERE cart_id = ? AND product_id = ?
                """, (cart_id, product_id))
                
                item = cursor.fetchone()
                if not item:
                    return RemoveFromCartOutput(error=f"Product {product_id} not in cart", status="failed")
                
                current_quantity = item['quantity']
                
                if quantity is None or quantity >= current_quantity:
                    # Remove entirely
                    cursor.execute("""
                        DELETE FROM cart_items
                        WHERE cart_id = ? AND product_id = ?
                    """, (cart_id, product_id))
                    
                    # Release all reserved inventory in same transaction
                    cursor.execute("""
                        UPDATE inventory 
                        SET reserved_quantity = MAX(0, reserved_quantity - ?),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = ?
                    """, (current_quantity, product_id))
                    
                    removed_quantity = current_quantity
                else:
                    # Partial removal
                    new_quantity = current_quantity - quantity
                    cursor.execute("""
                        UPDATE cart_items SET quantity = ?
                        WHERE cart_id = ? AND product_id = ?
                    """, (new_quantity, cart_id, product_id))
                    
                    # Release partial inventory in same transaction
                    cursor.execute("""
                        UPDATE inventory 
                        SET reserved_quantity = MAX(0, reserved_quantity - ?),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = ?
                    """, (quantity, product_id))
                    
                    removed_quantity = quantity
                
                # Update cart timestamp
                cursor.execute("""
                    UPDATE carts SET updated_at = CURRENT_TIMESTAMP
                    WHERE cart_id = ?
                """, (cart_id,))
                
                return RemoveFromCartOutput(
                    cart_id=cart_id,
                    removed=product_id,
                    quantity_removed=removed_quantity,
                    status="success"
                )
                
        except Exception as e:
            return RemoveFromCartOutput(error=str(e), status="failed")
    
    def update_cart_item(self, user_id: str, product_id: str, new_quantity: int) -> UpdateCartItemOutput:
        """Update quantity of item in cart.
        
        Args:
            user_id: User identifier
            product_id: Product to update
            new_quantity: New quantity (0 removes item)
            
        Returns:
            UpdateCartItemOutput with updated cart status
        """
        if new_quantity == 0:
            return self.remove_from_cart(user_id, product_id)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get active cart
                cart_id = self.get_or_create_cart(user_id)
                
                # Get current quantity
                cursor.execute("""
                    SELECT quantity FROM cart_items
                    WHERE cart_id = ? AND product_id = ?
                """, (cart_id, product_id))
                
                current = cursor.fetchone()
                if not current:
                    # Item not in cart, add it
                    return self.add_to_cart(user_id, product_id, new_quantity)
                
                current_quantity = current['quantity']
                
                # Check availability for new quantity
                if not self.check_availability(product_id, new_quantity):
                    return UpdateCartItemOutput(
                        error="Insufficient stock for requested quantity",
                        product_id=product_id,
                        requested=new_quantity,
                        status="failed"
                    )
                
                # Update inventory reservations
                self.release_inventory(product_id, current_quantity)
                self.reserve_inventory(product_id, new_quantity)
                
                # Update cart item
                cursor.execute("""
                    UPDATE cart_items SET quantity = ?
                    WHERE cart_id = ? AND product_id = ?
                """, (new_quantity, cart_id, product_id))
                
                # Update cart timestamp
                cursor.execute("""
                    UPDATE carts SET updated_at = CURRENT_TIMESTAMP
                    WHERE cart_id = ?
                """, (cart_id,))
                
                return UpdateCartItemOutput(
                    cart_id=cart_id,
                    product_id=product_id,
                    old_quantity=current_quantity,
                    new_quantity=new_quantity,
                    status="success"
                )
                
        except Exception as e:
            return UpdateCartItemOutput(error=str(e), status="failed")
    
    def get_cart(self, user_id: str) -> Cart:
        """Get current cart contents for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Cart object with items and totals
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get active cart
            cursor.execute("""
                SELECT cart_id, created_at, updated_at
                FROM carts 
                WHERE user_id = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            cart_data = cursor.fetchone()
            
            if not cart_data:
                # Return empty cart
                return Cart(
                    cart_id=0,
                    user_id=user_id,
                    items=[],
                    total=0.0,
                    item_count=0,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            
            # Get cart items
            cursor.execute("""
                SELECT ci.product_id, ci.quantity, ci.price_at_time
                FROM cart_items ci
                WHERE ci.cart_id = ?
            """, (cart_data['cart_id'],))
            
            items = []
            total = 0.0
            item_count = 0
            
            for row in cursor.fetchall():
                # Get product details
                product = self.get_product_by_id(row['product_id'])
                if product:
                    subtotal = row['quantity'] * row['price_at_time']
                    items.append(CartItem(
                        product_id=row['product_id'],
                        quantity=row['quantity'],
                        price=row['price_at_time'],
                        product_name=product['name'],
                        subtotal=subtotal
                    ))
                    total += subtotal
                    item_count += row['quantity']
            
            return Cart(
                cart_id=cart_data['cart_id'],
                user_id=user_id,
                items=items,
                total=total,
                item_count=item_count,
                created_at=datetime.fromisoformat(cart_data['created_at']),
                updated_at=datetime.fromisoformat(cart_data['updated_at'])
            )
    
    def clear_cart(self, user_id: str) -> ClearCartOutput:
        """Clear all items from user's cart.
        
        Args:
            user_id: User identifier
            
        Returns:
            ClearCartOutput confirming cart cleared
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get active cart
                cursor.execute("""
                    SELECT cart_id FROM carts 
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id,))
                
                cart_result = cursor.fetchone()
                if not cart_result:
                    return ClearCartOutput(message="No active cart to clear", status="success")
                
                cart_id = cart_result['cart_id']
                
                # Get all items to release inventory
                cursor.execute("""
                    SELECT product_id, quantity
                    FROM cart_items
                    WHERE cart_id = ?
                """, (cart_id,))
                
                items = cursor.fetchall()
                
                # Release all inventory in same transaction
                for item in items:
                    cursor.execute("""
                        UPDATE inventory 
                        SET reserved_quantity = MAX(0, reserved_quantity - ?),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = ?
                    """, (item['quantity'], item['product_id']))
                
                # Delete all cart items
                cursor.execute("""
                    DELETE FROM cart_items WHERE cart_id = ?
                """, (cart_id,))
                
                # Update cart status
                cursor.execute("""
                    UPDATE carts 
                    SET status = 'cleared', updated_at = CURRENT_TIMESTAMP
                    WHERE cart_id = ?
                """, (cart_id,))
                
                return ClearCartOutput(
                    cart_id=cart_id,
                    items_cleared=len(items),
                    status="success"
                )
                
        except Exception as e:
            return ClearCartOutput(error=str(e), status="failed")
    
    # =============================================================================
    # Phase 2: Inventory Management Methods
    # =============================================================================
    
    def check_availability(self, product_id: str, quantity: int) -> bool:
        """Check if product quantity is available.
        
        Args:
            product_id: Product to check
            quantity: Quantity needed
            
        Returns:
            True if available, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT stock_quantity, reserved_quantity
                FROM inventory
                WHERE product_id = ?
            """, (product_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            available = result['stock_quantity'] - result['reserved_quantity']
            return available >= quantity
    
    def reserve_inventory(self, product_id: str, quantity: int) -> bool:
        """Reserve inventory for cart (moves from available to reserved).
        
        Args:
            product_id: Product to reserve
            quantity: Quantity to reserve
            
        Returns:
            True if successfully reserved
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Atomic update with availability check
                cursor.execute("""
                    UPDATE inventory 
                    SET reserved_quantity = reserved_quantity + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ? 
                    AND (stock_quantity - reserved_quantity) >= ?
                """, (quantity, product_id, quantity))
                
                return cursor.rowcount > 0
        except:
            return False
    
    def release_inventory(self, product_id: str, quantity: int) -> bool:
        """Release reserved inventory back to available.
        
        Args:
            product_id: Product to release
            quantity: Quantity to release
            
        Returns:
            True if successfully released
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE inventory 
                    SET reserved_quantity = MAX(0, reserved_quantity - ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                """, (quantity, product_id))
                
                return cursor.rowcount > 0
        except:
            return False
    
    def commit_inventory(self, product_id: str, quantity: int) -> bool:
        """Commit reserved inventory (for completed orders).
        
        Args:
            product_id: Product to commit
            quantity: Quantity to commit
            
        Returns:
            True if successfully committed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check current inventory state for debugging
                cursor.execute("""
                    SELECT stock_quantity, reserved_quantity 
                    FROM inventory 
                    WHERE product_id = ?
                """, (product_id,))
                current = cursor.fetchone()
                
                if not current:
                    return False
                
                # Reduce both stock and reserved
                cursor.execute("""
                    UPDATE inventory 
                    SET stock_quantity = stock_quantity - ?,
                        reserved_quantity = MAX(0, reserved_quantity - ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ? 
                    AND stock_quantity >= ?
                    AND reserved_quantity >= ?
                """, (quantity, quantity, product_id, quantity, quantity))
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Commit inventory error: {e}")
            return False
    
    def update_stock(self, product_id: str, new_stock: int) -> UpdateStockOutput:
        """Update total stock for a product.
        
        Args:
            product_id: Product to update
            new_stock: New stock level
            
        Returns:
            UpdateStockOutput with updated stock info
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE inventory 
                    SET stock_quantity = ?,
                        last_restocked = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                """, (new_stock, product_id))
                
                if cursor.rowcount == 0:
                    # Product not in inventory, add it
                    cursor.execute("""
                        INSERT INTO inventory (product_id, stock_quantity, reserved_quantity)
                        VALUES (?, ?, 0)
                    """, (product_id, new_stock))
                
                return UpdateStockOutput(
                    product_id=product_id,
                    new_stock=new_stock,
                    status="success"
                )
        except Exception as e:
            return UpdateStockOutput(error=str(e), status="failed")
    
    def get_product_inventory(self, product_id: str) -> InventoryStatus:
        """Get current inventory status for a product.
        
        Args:
            product_id: Product to check
            
        Returns:
            InventoryStatus with stock quantities
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT stock_quantity, reserved_quantity, last_restocked
                FROM inventory
                WHERE product_id = ?
            """, (product_id,))
            
            result = cursor.fetchone()
            if not result:
                return InventoryStatus(
                    product_id=product_id,
                    stock_quantity=0,
                    reserved_quantity=0,
                    available_quantity=0,
                    last_restocked=None
                )
            
            return InventoryStatus(
                product_id=product_id,
                stock_quantity=result['stock_quantity'],
                reserved_quantity=result['reserved_quantity'],
                available_quantity=result['stock_quantity'] - result['reserved_quantity'],
                last_restocked=result['last_restocked']
            )
    
    def cleanup_abandoned_carts(self, hours: int = 24) -> CleanupCartsOutput:
        """Clean up carts that have been abandoned.
        
        Args:
            hours: Number of hours before cart considered abandoned
            
        Returns:
            CleanupCartsOutput with cleanup results
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find abandoned carts
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                cursor.execute("""
                    SELECT c.cart_id, ci.product_id, ci.quantity
                    FROM carts c
                    JOIN cart_items ci ON c.cart_id = ci.cart_id
                    WHERE c.status = 'active' 
                    AND c.updated_at < ?
                """, (cutoff_time,))
                
                abandoned_items = cursor.fetchall()
                
                # Release inventory for abandoned items in same transaction
                for item in abandoned_items:
                    cursor.execute("""
                        UPDATE inventory 
                        SET reserved_quantity = MAX(0, reserved_quantity - ?),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = ?
                    """, (item['quantity'], item['product_id']))
                
                # Mark carts as abandoned
                cursor.execute("""
                    UPDATE carts 
                    SET status = 'abandoned'
                    WHERE status = 'active' 
                    AND updated_at < ?
                """, (cutoff_time,))
                
                return CleanupCartsOutput(
                    carts_cleaned=cursor.rowcount,
                    items_released=len(abandoned_items),
                    status="success"
                )
                
        except Exception as e:
            return CleanupCartsOutput(error=str(e), status="failed")
    
    # =============================================================================
    # Phase 3: Order Management Methods
    # =============================================================================
    
    def checkout_cart(self, user_id: str, shipping_address: str) -> CheckoutOutput:
        """Convert cart to order and commit inventory.
        
        Args:
            user_id: User identifier
            shipping_address: Shipping address for order
            
        Returns:
            CheckoutOutput with order details or error
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get active cart
                cart = self.get_cart(user_id)
                if not cart.items:
                    return CheckoutOutput(error="Cart is empty", status="failed")
                
                # Generate order ID
                cursor.execute("SELECT COUNT(*) as count FROM orders")
                order_count = cursor.fetchone()['count']
                order_id = f"ORD{2000 + order_count:04d}"
                
                # Create order
                cursor.execute("""
                    INSERT INTO orders 
                    (order_id, user_id, cart_id, total_amount, status, shipping_address)
                    VALUES (?, ?, ?, ?, 'processing', ?)
                """, (order_id, user_id, cart.cart_id, cart.total, shipping_address))
                
                # Add order items and commit inventory
                for item in cart.items:
                    # Add to order items
                    cursor.execute("""
                        INSERT INTO order_items 
                        (order_id, product_id, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (order_id, item.product_id, item.quantity, item.price, item.subtotal))
                    
                    # Commit inventory directly in this transaction
                    cursor.execute("""
                        UPDATE inventory 
                        SET stock_quantity = stock_quantity - ?,
                            reserved_quantity = MAX(0, reserved_quantity - ?),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = ? 
                        AND stock_quantity >= ?
                        AND reserved_quantity >= ?
                    """, (item.quantity, item.quantity, item.product_id, item.quantity, item.quantity))
                    
                    if cursor.rowcount == 0:
                        raise Exception(f"Failed to commit inventory for {item.product_id}")
                
                # Mark cart as checked out
                cursor.execute("""
                    UPDATE carts 
                    SET status = 'checked_out', updated_at = CURRENT_TIMESTAMP
                    WHERE cart_id = ?
                """, (cart.cart_id,))
                
                # Clear cart items (already committed to order)
                cursor.execute("""
                    DELETE FROM cart_items WHERE cart_id = ?
                """, (cart.cart_id,))
                
                return CheckoutOutput(
                    order_id=order_id,
                    user_id=user_id,
                    total=float(cart.total),
                    items=len(cart.items),
                    status="success",
                    shipping_address=shipping_address,
                    message="Order placed successfully"
                )
                
        except Exception as e:
            return CheckoutOutput(error=str(e), status="failed")
    
    def get_order(self, user_id: str, order_id: str) -> Optional[Order]:
        """Get order details.
        
        Args:
            user_id: User identifier
            order_id: Order to retrieve
            
        Returns:
            Order object or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get order
            cursor.execute("""
                SELECT o.*, 
                       COUNT(DISTINCT oi.product_id) as item_count,
                       SUM(oi.quantity) as total_items
                FROM orders o
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                WHERE o.order_id = ? AND o.user_id = ?
                GROUP BY o.order_id
            """, (order_id, user_id))
            
            order = cursor.fetchone()
            if not order:
                return None
            
            # Get order items
            cursor.execute("""
                SELECT oi.product_id, oi.quantity, oi.unit_price, oi.subtotal
                FROM order_items oi
                WHERE oi.order_id = ?
            """, (order_id,))
            
            items = []
            for row in cursor.fetchall():
                product = self.get_product_by_id(row['product_id'])
                items.append(OrderItem(
                    product_id=row['product_id'],
                    product_name=product['name'] if product else "Unknown",
                    quantity=row['quantity'],
                    unit_price=float(row['unit_price']),
                    subtotal=float(row['subtotal'])
                ))
            
            return Order(
                order_id=order['order_id'],
                user_id=order['user_id'],
                status=order['status'],
                total=float(order['total_amount']),
                shipping_address=order['shipping_address'],
                created_at=order['created_at'],
                items=items,
                item_count=order['item_count'],
                total_items=order['total_items']
            )
    
    def list_orders(self, user_id: str, status: Optional[str] = None) -> List[OrderSummary]:
        """List orders for user.
        
        Args:
            user_id: User identifier
            status: Optional status filter
            
        Returns:
            List of OrderSummary objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT o.order_id, o.status, o.total_amount, o.created_at, o.shipping_address,
                           COUNT(oi.order_item_id) as item_count
                    FROM orders o
                    LEFT JOIN order_items oi ON o.order_id = oi.order_id
                    WHERE o.user_id = ? AND o.status = ?
                    GROUP BY o.order_id
                    ORDER BY o.created_at DESC
                """, (user_id, status))
            else:
                cursor.execute("""
                    SELECT o.order_id, o.status, o.total_amount, o.created_at, o.shipping_address,
                           COUNT(oi.order_item_id) as item_count
                    FROM orders o
                    LEFT JOIN order_items oi ON o.order_id = oi.order_id
                    WHERE o.user_id = ?
                    GROUP BY o.order_id
                    ORDER BY o.created_at DESC
                """, (user_id,))
            
            orders = []
            for row in cursor.fetchall():
                orders.append(OrderSummary(
                    order_id=row['order_id'],
                    status=row['status'],
                    total=float(row['total_amount']),
                    created_at=row['created_at'],
                    shipping_address=row['shipping_address'],
                    item_count=row['item_count']
                ))
            
            return orders
    
    def update_order_status(self, order_id: str, new_status: str) -> UpdateOrderStatusOutput:
        """Update order status (for tracking simulation).
        
        Args:
            order_id: Order to update
            new_status: New status value
            
        Returns:
            UpdateOrderStatusOutput with updated order info
        """
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return UpdateOrderStatusOutput(error=f"Invalid status. Must be one of: {valid_statuses}", status="failed")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update status
                cursor.execute("""
                    UPDATE orders 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """, (new_status, order_id))
                
                if cursor.rowcount == 0:
                    return UpdateOrderStatusOutput(error=f"Order {order_id} not found", status="failed")
                
                # If cancelled, release/restore inventory
                if new_status == 'cancelled':
                    # Get order items
                    cursor.execute("""
                        SELECT product_id, quantity 
                        FROM order_items 
                        WHERE order_id = ?
                    """, (order_id,))
                    
                    items = cursor.fetchall()
                    for item in items:
                        # Restore stock
                        cursor.execute("""
                            UPDATE inventory 
                            SET stock_quantity = stock_quantity + ?
                            WHERE product_id = ?
                        """, (item['quantity'], item['product_id']))
                
                return UpdateOrderStatusOutput(
                    order_id=order_id,
                    new_status=new_status,
                    status="success"
                )
                
        except Exception as e:
            return UpdateOrderStatusOutput(error=str(e), status="failed")
    
    def create_return(self, user_id: str, order_id: str, item_id: str, reason: str) -> CreateReturnOutput:
        """Process return request.
        
        Args:
            user_id: User identifier
            order_id: Order containing the item
            item_id: Product ID to return
            reason: Return reason
            
        Returns:
            CreateReturnOutput with return details
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verify order belongs to user and is delivered
                cursor.execute("""
                    SELECT status FROM orders 
                    WHERE order_id = ? AND user_id = ?
                """, (order_id, user_id))
                
                order = cursor.fetchone()
                if not order:
                    return CreateReturnOutput(error="Order not found", status="failed")
                
                if order['status'] not in ['delivered', 'shipped']:
                    return CreateReturnOutput(error=f"Cannot return order with status: {order['status']}", status="failed")
                
                # Verify item exists in order
                cursor.execute("""
                    SELECT quantity, unit_price, subtotal 
                    FROM order_items 
                    WHERE order_id = ? AND product_id = ?
                """, (order_id, item_id))
                
                item = cursor.fetchone()
                if not item:
                    return CreateReturnOutput(error=f"Item {item_id} not found in order", status="failed")
                
                # Generate return ID
                cursor.execute("SELECT COUNT(*) as count FROM returns")
                return_count = cursor.fetchone()['count']
                return_id = f"RET{1000 + return_count:03d}"
                
                # Create return request
                cursor.execute("""
                    INSERT INTO returns 
                    (return_id, order_id, user_id, item_id, reason, status, refund_amount)
                    VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """, (return_id, order_id, user_id, item_id, reason, item['subtotal']))
                
                return CreateReturnOutput(
                    return_id=return_id,
                    order_id=order_id,
                    item_id=item_id,
                    reason=reason,
                    refund_amount=float(item['subtotal']),
                    message="Return request created",
                    status="success"
                )
                
        except Exception as e:
            return CreateReturnOutput(error=str(e), status="failed")
    
    def process_return(self, return_id: str, approve: bool = True) -> ProcessReturnOutput:
        """Process a return request (approve or reject).
        
        Args:
            return_id: Return request ID
            approve: Whether to approve the return
            
        Returns:
            ProcessReturnOutput with processing outcome
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get return details
                cursor.execute("""
                    SELECT r.*, oi.quantity 
                    FROM returns r
                    JOIN order_items oi ON r.order_id = oi.order_id AND r.item_id = oi.product_id
                    WHERE r.return_id = ? AND r.status = 'pending'
                """, (return_id,))
                
                ret = cursor.fetchone()
                if not ret:
                    return ProcessReturnOutput(error="Return request not found or already processed", status="failed")
                
                if approve:
                    # Approve return and restore inventory
                    cursor.execute("""
                        UPDATE returns 
                        SET status = 'approved', processed_at = CURRENT_TIMESTAMP
                        WHERE return_id = ?
                    """, (return_id,))
                    
                    # Restore inventory
                    cursor.execute("""
                        UPDATE inventory 
                        SET stock_quantity = stock_quantity + ?
                        WHERE product_id = ?
                    """, (ret['quantity'], ret['item_id']))
                    
                    status = "approved"
                    message = f"Return approved. ${ret['refund_amount']} will be refunded."
                else:
                    # Reject return
                    cursor.execute("""
                        UPDATE returns 
                        SET status = 'rejected', processed_at = CURRENT_TIMESTAMP
                        WHERE return_id = ?
                    """, (return_id,))
                    
                    status = "rejected"
                    message = "Return request rejected."
                
                return ProcessReturnOutput(
                    return_id=return_id,
                    return_status=status,
                    message=message,
                    status="success"
                )
                
        except Exception as e:
            return ProcessReturnOutput(error=str(e), status="failed")