"""Checkout tool implementation using the unified base class."""
from typing import List, ClassVar, Type
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import CheckoutOutput


class CheckoutTool(BaseTool):
    """Tool for checking out and completing a purchase."""
    
    NAME: ClassVar[str] = "checkout"
    MODULE: ClassVar[str] = "tools.ecommerce.checkout"
    
    class Arguments(BaseModel):
        """Arguments for checkout."""
        user_id: str = Field(..., description="User ID")
        shipping_address: str = Field(..., description="Shipping address for the order")
    
    # Tool definition as instance attributes
    description: str = "Checkout the current cart and create an order"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, user_id: str, shipping_address: str) -> dict:
        """Execute the tool to checkout cart."""
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Checkout using the manager
        result: CheckoutOutput = manager.checkout_cart(user_id, shipping_address)
        
        # Convert Pydantic model to dict for response
        return result.model_dump(exclude_none=True)
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Checkout my cart and ship to 123 Main St",
                expected_tools=["checkout"],
                description="Complete purchase"
            ),
            ToolTestCase(
                request="Complete my order and send to 456 Oak Ave",
                expected_tools=["checkout"],
                description="Finish checkout"
            )
        ]