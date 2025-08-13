# E-Commerce Module Guide

## Quick Start

### Running Tests

```bash
# Run all ecommerce tests with pytest
poetry run pytest tests/ecommerce/

# Run specific test class
poetry run pytest tests/ecommerce/test_cart_inventory.py::TestPhase1CoreInfrastructure

# Run with verbose output
poetry run pytest tests/ecommerce/ -v

# Run only Pydantic validation tests
poetry run pytest tests/ecommerce/test_pydantic_validation.py

# Run tests with coverage report
poetry run pytest tests/ecommerce/ --cov=tools.ecommerce

# Run integration with agentic loop
poetry run python -m agentic_loop.demo_react_agent ecommerce
```

### Basic Usage Example

```python
from tools.ecommerce.cart_inventory_manager import CartInventoryManager

# Initialize the manager
manager = CartInventoryManager()

# Add item to cart
result = manager.add_to_cart("user123", "KB123", 2)
print(f"Added to cart: {result.status}")

# Checkout
result = manager.checkout_cart("user123", "123 Main St")
print(f"Order placed: {result.order_id}")
```

---

## Overview

The e-commerce module provides a complete shopping cart and order management system with inventory tracking, built using SQLite for persistence and Pydantic for type-safe data models.

## Architecture

### Core Components

```
tools/ecommerce/
├── models.py                    # Pydantic models for all data structures
├── cart_inventory_manager.py    # Main business logic manager
├── add_to_cart.py               # Tool for adding items to cart
├── search_products.py           # Product search functionality
├── list_orders.py               # Order listing tool
├── get_order.py                 # Order retrieval tool
├── track_order.py               # Order tracking tool
├── return_item.py               # Return processing tool
└── test_*.py                    # Test suites
```

### Data Storage

- **SQLite Database**: Persistent storage for all stateful data
  - Carts and cart items
  - Orders and order items
  - Inventory tracking
  - Returns processing

- **JSON File**: Product catalog (`data/products.json`)
  - Product definitions
  - Base prices
  - Initial stock levels

## Key Features

### 1. Cart Management

**Adding Items to Cart**
- Automatic cart creation for new users
- Inventory validation before adding
- Quantity updates for existing items
- Real-time stock reservation

```python
# Add product to cart
result = manager.add_to_cart(user_id="alice", product_id="KB123", quantity=2)
# Returns: AddToCartOutput with cart_id, total, status
```

**Cart Operations**
- View cart contents with calculated totals
- Update item quantities
- Remove items (partial or complete)
- Clear entire cart

```python
# Get current cart
cart = manager.get_cart("alice")
# Returns: Cart object with items, total, timestamps

# Update quantity
result = manager.update_cart_item("alice", "KB123", new_quantity=3)

# Remove item
result = manager.remove_from_cart("alice", "KB123", quantity=1)

# Clear cart
result = manager.clear_cart("alice")
```

### 2. Inventory Management

**Stock Tracking**
- Real-time inventory levels
- Reserved vs available quantities
- Automatic reservation on cart add
- Release on cart removal/abandonment

```python
# Check inventory status
inv = manager.get_product_inventory("KB123")
# Returns: InventoryStatus with stock_quantity, reserved_quantity, available_quantity

# Update stock levels
result = manager.update_stock("KB123", new_stock=100)
```

**Inventory States**
- **Stock Quantity**: Total items in warehouse
- **Reserved Quantity**: Items in active carts
- **Available Quantity**: Stock - Reserved (can be sold)

### 3. Order Processing

**Checkout Flow**
1. Validates cart contents
2. Creates order with unique ID
3. Commits inventory (reduces stock)
4. Clears cart
5. Returns order confirmation

```python
# Complete checkout
result = manager.checkout_cart(
    user_id="alice",
    shipping_address="123 Main St, City, ST 12345"
)
# Returns: CheckoutOutput with order_id, total, status
```

**Order Management**
- List orders (all or filtered by status)
- Get detailed order information
- Update order status
- Track shipping progress

```python
# List user's orders
orders = manager.list_orders("alice", status="delivered")

# Get specific order
order = manager.get_order("alice", "ORD2001")

# Update order status
result = manager.update_order_status("ORD2001", "shipped")
```

### 4. Returns Processing

**Return Flow**
1. Validate order eligibility (must be delivered/shipped)
2. Create return request
3. Process approval/rejection
4. Restore inventory if approved
5. Track refund amount

```python
# Create return request
result = manager.create_return(
    user_id="alice",
    order_id="ORD2001",
    item_id="KB123",
    reason="Defective product"
)

# Process return
result = manager.process_return(return_id="RET1001", approve=True)
```

### 5. Cart Abandonment

**Automatic Cleanup**
- Identifies abandoned carts by age
- Releases reserved inventory
- Maintains data integrity

```python
# Clean up carts older than 24 hours
result = manager.cleanup_abandoned_carts(hours=24)
# Returns: CleanupCartsOutput with carts_cleaned, items_released
```

## Data Models (Pydantic)

### Core Models

**CartItem**
```python
class CartItem(BaseModel):
    product_id: str
    quantity: int         # Must be > 0
    price: float         # Must be >= 0
    product_name: str
    subtotal: float      # Must be >= 0
```

**Cart**
```python
class Cart(BaseModel):
    cart_id: int
    user_id: str
    items: List[CartItem]
    total: float         # Must be >= 0
    item_count: int      # Must be >= 0
    created_at: datetime
    updated_at: datetime
```

**Order**
```python
class Order(BaseModel):
    order_id: str
    user_id: str
    status: str          # pending|processing|shipped|delivered|cancelled
    total: float
    shipping_address: Optional[str]
    created_at: str
    items: List[OrderItem]
    item_count: int
    total_items: int
```

## Database Schema

### Tables

1. **inventory**: Product stock levels
2. **carts**: Shopping cart headers
3. **cart_items**: Items in carts
4. **orders**: Order headers
5. **order_items**: Items in orders
6. **returns**: Return requests

### Relationships
- Carts → Cart Items (1:N)
- Orders → Order Items (1:N)
- Orders → Returns (1:N)
- Products ↔ Inventory (1:1)

## Testing

### Test Phases

**Phase 1: Infrastructure**
- Database initialization
- Product loading
- Demo data seeding
- Statistics generation

**Phase 2: Cart & Inventory**
- Cart operations (add/remove/update)
- Inventory tracking
- Multi-user scenarios
- Cart abandonment

**Phase 3: Order Management**
- Checkout process
- Order retrieval
- Status updates
- Returns processing

### Validation Testing

The module includes comprehensive Pydantic validation tests:
- Field constraints (positive quantities, non-negative prices)
- Status enumerations
- Required vs optional fields
- Serialization/deserialization

## Usage in Agentic Loop

The e-commerce tools integrate with the DSPy agentic loop system:

```python
# Available tools in EcommerceToolSet
- search_products: Find products by query
- add_to_cart: Add items to shopping cart
- get_order: Retrieve order details
- list_orders: List user's orders
- track_order: Track shipping status
- return_item: Process returns
```

### Example Agent Interaction

```
User: "Find wireless keyboards and add the cheapest one to my cart"

Agent:
1. search_products(query="wireless keyboard")
2. Analyze results for cheapest option
3. add_to_cart(product_id="KB789", quantity=1)
4. Return confirmation to user
```

## Configuration

### Environment Variables
```bash
# Database location (default: tools/db_files/ecommerce_demo.db)
# If not specified, databases are stored in tools/db_files/
ECOMMERCE_DB_PATH=./tools/db_files/ecommerce_demo.db

# Demo user for testing
DEMO_USER_ID=demo_user
```

### Products Configuration

Products are defined in `data/products.json`:
```json
{
  "products": [
    {
      "id": "KB123",
      "name": "Gaming Mechanical Keyboard RGB",
      "price": 129.99,
      "category": "Electronics",
      "stock": 45,
      "tags": ["gaming", "mechanical", "rgb"]
    }
  ]
}
```

## Best Practices

### Inventory Management
1. Always check availability before adding to cart
2. Reserve inventory immediately on cart add
3. Release inventory on removal/abandonment
4. Commit inventory only on successful checkout

### Error Handling
1. All methods return Pydantic models with `status` field
2. Check `status == "success"` before proceeding
3. Error details in `error` field when `status == "failed"`
4. Use validation to catch issues early

### Performance
1. Use database indexes for frequent queries
2. Batch operations when possible
3. Clean up abandoned carts regularly
4. Monitor inventory levels

## Troubleshooting

### Common Issues

**Insufficient Stock Error**
- Check available inventory with `get_product_inventory()`
- Ensure no abandoned carts holding inventory
- Run `cleanup_abandoned_carts()` if needed

**Cart Not Found**
- Cart may have been cleaned up
- Use `get_or_create_cart()` to ensure cart exists

**Order Status Validation**
- Only valid statuses: pending, processing, shipped, delivered, cancelled
- Returns only allowed for shipped/delivered orders

### Debug Commands

```python
# Check system statistics
stats = manager.get_stats()
print(f"Orders: {stats.total_orders}")
print(f"Active carts: {stats.active_carts}")
print(f"Inventory: {stats.inventory}")

# Reset database with demo data
manager.reset_database()

# Check specific product inventory
inv = manager.get_product_inventory("KB123")
print(f"Available: {inv.available_quantity}")
```

## API Reference

See individual tool files for detailed API documentation:
- `cart_inventory_manager.py`: Core manager methods
- `models.py`: All Pydantic model definitions
- Test files: Usage examples and validation

## Future Enhancements

Potential improvements to consider:
- User authentication/sessions
- Payment processing integration
- Shipping calculations
- Discount/coupon system
- Product recommendations
- Wishlist functionality
- Multi-currency support
- Analytics and reporting