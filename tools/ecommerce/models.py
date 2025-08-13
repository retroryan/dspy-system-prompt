"""Pydantic models for E-commerce tools.

This module provides type-safe data models for all e-commerce operations
including cart management, orders, inventory, and returns.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class CartItem(BaseModel):
    """Represents an item in a shopping cart."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    product_id: str
    quantity: int = Field(gt=0, description="Quantity must be positive")
    price: float = Field(ge=0, description="Price must be non-negative")
    product_name: str
    subtotal: float = Field(ge=0, description="Subtotal must be non-negative")


class Cart(BaseModel):
    """Represents a user's shopping cart."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )
    
    cart_id: int
    user_id: str
    items: List[CartItem] = Field(default_factory=list)
    total: float = Field(ge=0, default=0.0, description="Total must be non-negative")
    item_count: int = Field(ge=0, default=0, description="Item count must be non-negative")
    created_at: datetime
    updated_at: datetime


class AddToCartInput(BaseModel):
    """Input for adding items to cart."""
    user_id: str
    product_id: str
    quantity: int = Field(gt=0, description="Quantity must be positive")


class AddToCartOutput(BaseModel):
    """Output from adding items to cart."""
    cart_id: Optional[int] = None
    cart_total: Optional[int] = None
    cart_value: Optional[float] = None
    added: Optional[str] = None
    product_name: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    status: str
    error: Optional[str] = None
    product_id: Optional[str] = None
    requested_quantity: Optional[int] = None
    available_stock: Optional[int] = None
    current_in_cart: Optional[int] = None
    requested_additional: Optional[int] = None


class RemoveFromCartInput(BaseModel):
    """Input for removing items from cart."""
    user_id: str
    product_id: str
    quantity: Optional[int] = None


class RemoveFromCartOutput(BaseModel):
    """Output from removing items from cart."""
    cart_id: Optional[int] = None
    removed: Optional[str] = None
    quantity_removed: Optional[int] = None
    status: str
    error: Optional[str] = None


class UpdateCartItemInput(BaseModel):
    """Input for updating cart items."""
    user_id: str
    product_id: str
    new_quantity: int = Field(ge=0, description="Quantity must be non-negative")


class UpdateCartItemOutput(BaseModel):
    """Output from updating cart items."""
    cart_id: Optional[int] = None
    product_id: Optional[str] = None
    old_quantity: Optional[int] = None
    new_quantity: Optional[int] = None
    status: str
    error: Optional[str] = None
    requested: Optional[int] = None


class ClearCartInput(BaseModel):
    """Input for clearing cart."""
    user_id: str


class ClearCartOutput(BaseModel):
    """Output from clearing cart."""
    cart_id: Optional[int] = None
    items_cleared: Optional[int] = None
    message: Optional[str] = None
    status: str
    error: Optional[str] = None


class CheckoutInput(BaseModel):
    """Input for checkout."""
    user_id: str
    shipping_address: str


class CheckoutOutput(BaseModel):
    """Output from checkout."""
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    total: Optional[float] = None
    items: Optional[int] = None
    shipping_address: Optional[str] = None
    message: Optional[str] = None
    status: str
    error: Optional[str] = None


class OrderItem(BaseModel):
    """Represents an item in an order."""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class Order(BaseModel):
    """Represents an order."""
    order_id: str
    user_id: str
    status: str
    total: float
    shipping_address: Optional[str] = None
    created_at: str
    items: List[OrderItem]
    item_count: int
    total_items: int


class OrderSummary(BaseModel):
    """Summary of an order for listing."""
    order_id: str
    status: str
    total: float
    created_at: str
    shipping_address: Optional[str] = None
    item_count: int


class GetOrderInput(BaseModel):
    """Input for getting order details."""
    user_id: str
    order_id: str


class ListOrdersInput(BaseModel):
    """Input for listing orders."""
    user_id: str
    status: Optional[str] = None


class UpdateOrderStatusInput(BaseModel):
    """Input for updating order status."""
    order_id: str
    new_status: str = Field(
        pattern="^(pending|processing|shipped|delivered|cancelled)$",
        description="Valid order statuses"
    )


class UpdateOrderStatusOutput(BaseModel):
    """Output from updating order status."""
    order_id: Optional[str] = None
    new_status: Optional[str] = None
    status: str
    error: Optional[str] = None


class CreateReturnInput(BaseModel):
    """Input for creating a return."""
    user_id: str
    order_id: str
    item_id: str
    reason: str


class CreateReturnOutput(BaseModel):
    """Output from creating a return."""
    return_id: Optional[str] = None
    order_id: Optional[str] = None
    item_id: Optional[str] = None
    reason: Optional[str] = None
    refund_amount: Optional[float] = None
    message: Optional[str] = None
    status: str
    error: Optional[str] = None


class ProcessReturnInput(BaseModel):
    """Input for processing a return."""
    return_id: str
    approve: bool = True


class ProcessReturnOutput(BaseModel):
    """Output from processing a return."""
    return_id: Optional[str] = None
    return_status: Optional[str] = None
    message: Optional[str] = None
    status: str
    error: Optional[str] = None


class InventoryStatus(BaseModel):
    """Status of inventory for a product."""
    product_id: str
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int
    last_restocked: Optional[str] = None


class UpdateStockInput(BaseModel):
    """Input for updating stock."""
    product_id: str
    new_stock: int = Field(ge=0, description="Stock must be non-negative")


class UpdateStockOutput(BaseModel):
    """Output from updating stock."""
    product_id: Optional[str] = None
    new_stock: Optional[int] = None
    status: str
    error: Optional[str] = None


class StatsOutput(BaseModel):
    """Statistics about carts and orders."""
    total_orders: int
    orders_by_status: Dict[str, int]
    active_carts: int
    inventory: Dict[str, Any]
    pending_returns: int


class CleanupCartsInput(BaseModel):
    """Input for cleaning up abandoned carts."""
    hours: int = Field(default=24, gt=0, description="Hours before cart considered abandoned")


class CleanupCartsOutput(BaseModel):
    """Output from cleaning up carts."""
    carts_cleaned: Optional[int] = None
    items_released: Optional[int] = None
    status: str
    error: Optional[str] = None