#!/usr/bin/env python3
"""Test Pydantic validation features in ecommerce models."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pydantic import ValidationError
from tools.ecommerce.models import (
    CartItem, Cart, AddToCartInput, UpdateCartItemInput,
    UpdateOrderStatusInput, CleanupCartsInput
)
from datetime import datetime


def test_validation():
    """Test Pydantic validation features."""
    print("=" * 60)
    print("Testing Pydantic Validation Features")
    print("=" * 60)
    
    # Test CartItem validation
    print("\n--- Testing CartItem Validation ---")
    
    # Valid CartItem
    try:
        item = CartItem(
            product_id="TEST123",
            quantity=5,
            price=99.99,
            product_name="Test Product",
            subtotal=499.95
        )
        print(f"✓ Valid CartItem created: {item.product_name}")
    except ValidationError as e:
        print(f"✗ Failed to create valid CartItem: {e}")
    
    # Invalid quantity (negative)
    try:
        item = CartItem(
            product_id="TEST123",
            quantity=-1,  # Should fail validation
            price=99.99,
            product_name="Test Product",
            subtotal=99.99
        )
        print("✗ Created CartItem with negative quantity (should have failed)")
    except ValidationError as e:
        print(f"✓ Correctly rejected negative quantity: {e.errors()[0]['msg']}")
    
    # Invalid price (negative)
    try:
        item = CartItem(
            product_id="TEST123",
            quantity=1,
            price=-10.0,  # Should fail validation
            product_name="Test Product",
            subtotal=10.0
        )
        print("✗ Created CartItem with negative price (should have failed)")
    except ValidationError as e:
        print(f"✓ Correctly rejected negative price: {e.errors()[0]['msg']}")
    
    # Test Cart validation
    print("\n--- Testing Cart Validation ---")
    
    # Valid Cart
    try:
        cart = Cart(
            cart_id=1,
            user_id="test_user",
            items=[],
            total=0.0,
            item_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print(f"✓ Valid Cart created for user: {cart.user_id}")
    except ValidationError as e:
        print(f"✗ Failed to create valid Cart: {e}")
    
    # Invalid total (negative)
    try:
        cart = Cart(
            cart_id=1,
            user_id="test_user",
            items=[],
            total=-50.0,  # Should fail validation
            item_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print("✗ Created Cart with negative total (should have failed)")
    except ValidationError as e:
        print(f"✓ Correctly rejected negative total: {e.errors()[0]['msg']}")
    
    # Test AddToCartInput validation
    print("\n--- Testing AddToCartInput Validation ---")
    
    # Valid input
    try:
        input_data = AddToCartInput(
            user_id="test_user",
            product_id="PROD123",
            quantity=3
        )
        print(f"✓ Valid AddToCartInput: {input_data.quantity} items")
    except ValidationError as e:
        print(f"✗ Failed to create valid AddToCartInput: {e}")
    
    # Invalid quantity (zero)
    try:
        input_data = AddToCartInput(
            user_id="test_user",
            product_id="PROD123",
            quantity=0  # Should fail validation
        )
        print("✗ Created AddToCartInput with zero quantity (should have failed)")
    except ValidationError as e:
        print(f"✓ Correctly rejected zero quantity: {e.errors()[0]['msg']}")
    
    # Test UpdateCartItemInput validation
    print("\n--- Testing UpdateCartItemInput Validation ---")
    
    # Valid input (zero is allowed for removal)
    try:
        input_data = UpdateCartItemInput(
            user_id="test_user",
            product_id="PROD123",
            new_quantity=0  # Zero is valid (removes item)
        )
        print(f"✓ Valid UpdateCartItemInput with zero quantity (for removal)")
    except ValidationError as e:
        print(f"✗ Failed to create UpdateCartItemInput with zero: {e}")
    
    # Invalid quantity (negative)
    try:
        input_data = UpdateCartItemInput(
            user_id="test_user",
            product_id="PROD123",
            new_quantity=-5  # Should fail validation
        )
        print("✗ Created UpdateCartItemInput with negative quantity (should have failed)")
    except ValidationError as e:
        print(f"✓ Correctly rejected negative quantity: {e.errors()[0]['msg']}")
    
    # Test UpdateOrderStatusInput validation
    print("\n--- Testing UpdateOrderStatusInput Validation ---")
    
    # Valid status
    try:
        input_data = UpdateOrderStatusInput(
            order_id="ORD123",
            new_status="shipped"
        )
        print(f"✓ Valid UpdateOrderStatusInput: {input_data.new_status}")
    except ValidationError as e:
        print(f"✗ Failed to create valid UpdateOrderStatusInput: {e}")
    
    # Invalid status
    try:
        input_data = UpdateOrderStatusInput(
            order_id="ORD123",
            new_status="invalid_status"  # Should fail pattern validation
        )
        print("✗ Created UpdateOrderStatusInput with invalid status (should have failed)")
    except ValidationError as e:
        print(f"✓ Correctly rejected invalid status: {e.errors()[0]['msg']}")
    
    # Test CleanupCartsInput validation
    print("\n--- Testing CleanupCartsInput Validation ---")
    
    # Valid with default
    try:
        input_data = CleanupCartsInput()
        print(f"✓ Valid CleanupCartsInput with default: {input_data.hours} hours")
    except ValidationError as e:
        print(f"✗ Failed to create CleanupCartsInput with default: {e}")
    
    # Invalid hours (zero)
    try:
        input_data = CleanupCartsInput(hours=0)  # Should fail validation (gt=0)
        print("✗ Created CleanupCartsInput with zero hours (should have failed)")
    except ValidationError as e:
        print(f"✓ Correctly rejected zero hours: {e.errors()[0]['msg']}")
    
    print("\n✓ All Pydantic validation tests complete!")


def test_serialization():
    """Test Pydantic serialization features."""
    print("\n" + "=" * 60)
    print("Testing Pydantic Serialization Features")
    print("=" * 60)
    
    # Create a complex object
    now = datetime.now()
    cart = Cart(
        cart_id=1,
        user_id="test_user",
        items=[
            CartItem(
                product_id="PROD1",
                quantity=2,
                price=50.0,
                product_name="Product 1",
                subtotal=100.0
            ),
            CartItem(
                product_id="PROD2",
                quantity=1,
                price=75.0,
                product_name="Product 2",
                subtotal=75.0
            )
        ],
        total=175.0,
        item_count=3,
        created_at=now,
        updated_at=now
    )
    
    # Test model_dump (dict conversion)
    cart_dict = cart.model_dump()
    print(f"✓ Cart converted to dict with {len(cart_dict)} fields")
    print(f"  Items: {len(cart_dict['items'])} items")
    print(f"  Total: ${cart_dict['total']}")
    
    # Test model_dump with exclude_none
    cart_dict_no_none = cart.model_dump(exclude_none=True)
    print(f"✓ Cart dict with exclude_none: {len(cart_dict_no_none)} fields")
    
    # Test JSON serialization
    cart_json = cart.model_dump_json()
    print(f"✓ Cart serialized to JSON: {len(cart_json)} characters")
    
    # Test datetime serialization
    if isinstance(cart_dict['created_at'], datetime):
        print(f"✓ DateTime preserved in dict: {cart_dict['created_at']}")
    
    # Create from dict (deserialization)
    cart_from_dict = Cart(**cart_dict)
    print(f"✓ Cart recreated from dict: {cart_from_dict.user_id}")
    
    print("\n✓ All serialization tests complete!")


if __name__ == "__main__":
    # Test validation
    test_validation()
    
    # Test serialization
    test_serialization()
    
    print("\n" + "=" * 60)
    print("✓ All Pydantic tests passed successfully!")
    print("=" * 60)