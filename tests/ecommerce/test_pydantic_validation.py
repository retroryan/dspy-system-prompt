"""Test Pydantic validation features in ecommerce models."""

import pytest
from pydantic import ValidationError
from datetime import datetime
from tools.ecommerce.models import (
    CartItem, Cart, AddToCartInput, UpdateCartItemInput,
    UpdateOrderStatusInput, CleanupCartsInput
)


class TestCartItemValidation:
    """Test CartItem model validation."""
    
    def test_valid_cart_item(self):
        """Test creating a valid CartItem."""
        item = CartItem(
            product_id="TEST123",
            quantity=5,
            price=99.99,
            product_name="Test Product",
            subtotal=499.95
        )
        assert item.product_name == "Test Product"
        assert item.quantity == 5
    
    def test_negative_quantity_rejected(self):
        """Test that negative quantity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CartItem(
                product_id="TEST123",
                quantity=-1,
                price=99.99,
                product_name="Test Product",
                subtotal=99.99
            )
        assert 'greater than 0' in str(exc_info.value)
    
    def test_negative_price_rejected(self):
        """Test that negative price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CartItem(
                product_id="TEST123",
                quantity=1,
                price=-10.0,
                product_name="Test Product",
                subtotal=10.0
            )
        assert 'greater than or equal to 0' in str(exc_info.value)
    
    def test_negative_subtotal_rejected(self):
        """Test that negative subtotal is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CartItem(
                product_id="TEST123",
                quantity=1,
                price=10.0,
                product_name="Test Product",
                subtotal=-10.0
            )
        assert 'greater than or equal to 0' in str(exc_info.value)


class TestCartValidation:
    """Test Cart model validation."""
    
    def test_valid_cart(self):
        """Test creating a valid Cart."""
        cart = Cart(
            cart_id=1,
            user_id="test_user",
            items=[],
            total=0.0,
            item_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert cart.user_id == "test_user"
        assert cart.cart_id == 1
    
    def test_cart_with_items(self):
        """Test cart with valid items."""
        item = CartItem(
            product_id="TEST123",
            quantity=2,
            price=50.0,
            product_name="Test Product",
            subtotal=100.0
        )
        cart = Cart(
            cart_id=1,
            user_id="test_user",
            items=[item],
            total=100.0,
            item_count=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert len(cart.items) == 1
        assert cart.total == 100.0
    
    def test_negative_total_rejected(self):
        """Test that negative total is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Cart(
                cart_id=1,
                user_id="test_user",
                items=[],
                total=-50.0,
                item_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        assert 'greater than or equal to 0' in str(exc_info.value)
    
    def test_negative_item_count_rejected(self):
        """Test that negative item count is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Cart(
                cart_id=1,
                user_id="test_user",
                items=[],
                total=0.0,
                item_count=-1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        assert 'greater than or equal to 0' in str(exc_info.value)


class TestInputValidation:
    """Test input model validation."""
    
    def test_valid_add_to_cart_input(self):
        """Test valid AddToCartInput."""
        input_data = AddToCartInput(
            user_id="test_user",
            product_id="PROD123",
            quantity=3
        )
        assert input_data.quantity == 3
        assert input_data.user_id == "test_user"
    
    def test_zero_quantity_rejected_for_add(self):
        """Test that zero quantity is rejected for AddToCartInput."""
        with pytest.raises(ValidationError) as exc_info:
            AddToCartInput(
                user_id="test_user",
                product_id="PROD123",
                quantity=0
            )
        assert 'greater than 0' in str(exc_info.value)
    
    def test_negative_quantity_rejected_for_add(self):
        """Test that negative quantity is rejected for AddToCartInput."""
        with pytest.raises(ValidationError) as exc_info:
            AddToCartInput(
                user_id="test_user",
                product_id="PROD123",
                quantity=-5
            )
        assert 'greater than 0' in str(exc_info.value)
    
    def test_valid_update_cart_item_input(self):
        """Test valid UpdateCartItemInput."""
        input_data = UpdateCartItemInput(
            user_id="test_user",
            product_id="PROD123",
            new_quantity=5
        )
        assert input_data.new_quantity == 5
    
    def test_zero_quantity_allowed_for_update(self):
        """Test that zero quantity is allowed for UpdateCartItemInput (removal)."""
        input_data = UpdateCartItemInput(
            user_id="test_user",
            product_id="PROD123",
            new_quantity=0
        )
        assert input_data.new_quantity == 0
    
    def test_negative_quantity_rejected_for_update(self):
        """Test that negative quantity is rejected for UpdateCartItemInput."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCartItemInput(
                user_id="test_user",
                product_id="PROD123",
                new_quantity=-5
            )
        assert 'greater than or equal to 0' in str(exc_info.value)


class TestOrderStatusValidation:
    """Test order status validation."""
    
    def test_valid_order_statuses(self):
        """Test all valid order statuses."""
        valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        
        for status in valid_statuses:
            input_data = UpdateOrderStatusInput(
                order_id="ORD123",
                new_status=status
            )
            assert input_data.new_status == status
    
    def test_invalid_order_status_rejected(self):
        """Test that invalid order status is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateOrderStatusInput(
                order_id="ORD123",
                new_status="invalid_status"
            )
        assert 'String should match pattern' in str(exc_info.value)


class TestCleanupCartsValidation:
    """Test cleanup carts input validation."""
    
    def test_valid_cleanup_with_default(self):
        """Test CleanupCartsInput with default value."""
        input_data = CleanupCartsInput()
        assert input_data.hours == 24
    
    def test_valid_cleanup_with_custom_hours(self):
        """Test CleanupCartsInput with custom hours."""
        input_data = CleanupCartsInput(hours=48)
        assert input_data.hours == 48
    
    def test_zero_hours_rejected(self):
        """Test that zero hours is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CleanupCartsInput(hours=0)
        assert 'greater than 0' in str(exc_info.value)
    
    def test_negative_hours_rejected(self):
        """Test that negative hours is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CleanupCartsInput(hours=-24)
        assert 'greater than 0' in str(exc_info.value)


class TestModelSerialization:
    """Test Pydantic model serialization features."""
    
    def test_cart_dict_conversion(self):
        """Test converting Cart to dictionary."""
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
                )
            ],
            total=100.0,
            item_count=2,
            created_at=now,
            updated_at=now
        )
        
        cart_dict = cart.model_dump()
        assert cart_dict['cart_id'] == 1
        assert cart_dict['user_id'] == "test_user"
        assert len(cart_dict['items']) == 1
        assert cart_dict['total'] == 100.0
    
    def test_cart_json_serialization(self):
        """Test Cart JSON serialization."""
        now = datetime.now()
        cart = Cart(
            cart_id=1,
            user_id="test_user",
            items=[],
            total=0.0,
            item_count=0,
            created_at=now,
            updated_at=now
        )
        
        cart_json = cart.model_dump_json()
        assert isinstance(cart_json, str)
        assert '"cart_id":1' in cart_json
        assert '"user_id":"test_user"' in cart_json
    
    def test_exclude_none_serialization(self):
        """Test serialization with exclude_none."""
        from tools.ecommerce.models import AddToCartOutput
        
        output = AddToCartOutput(
            status="success",
            cart_id=1,
            cart_total=5
        )
        
        output_dict = output.model_dump(exclude_none=True)
        assert 'error' not in output_dict
        assert 'product_name' not in output_dict
        assert output_dict['status'] == 'success'
        assert output_dict['cart_id'] == 1
    
    def test_cart_recreation_from_dict(self):
        """Test recreating Cart from dictionary."""
        now = datetime.now()
        original_cart = Cart(
            cart_id=1,
            user_id="test_user",
            items=[],
            total=0.0,
            item_count=0,
            created_at=now,
            updated_at=now
        )
        
        cart_dict = original_cart.model_dump()
        recreated_cart = Cart(**cart_dict)
        
        assert recreated_cart.cart_id == original_cart.cart_id
        assert recreated_cart.user_id == original_cart.user_id
        assert recreated_cart.total == original_cart.total