"""Remove from cart tool implementation using the unified base class."""
from typing import List, ClassVar, Type, Optional
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import RemoveFromCartOutput


class RemoveFromCartTool(BaseTool):
    """Tool for removing items from the shopping cart."""
    
    NAME: ClassVar[str] = "remove_from_cart"
    MODULE: ClassVar[str] = "tools.ecommerce.remove_from_cart"
    
    class Arguments(BaseModel):
        """Arguments for removing from cart."""
        user_id: str = Field(..., description="User ID")
        product_id: str = Field(..., description="Product ID to remove")
        quantity: Optional[int] = Field(default=None, description="Quantity to remove (None removes all)")
    
    # Tool definition as instance attributes
    description: str = "Remove items from the shopping cart"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, user_id: str, product_id: str, quantity: Optional[int] = None) -> dict:
        """Execute the tool to remove items from cart."""
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Remove from cart using the manager
        result: RemoveFromCartOutput = manager.remove_from_cart(user_id, product_id, quantity)
        
        # Convert Pydantic model to dict for response
        return result.model_dump(exclude_none=True)
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Remove PROD123 from my cart",
                expected_tools=["remove_from_cart"],
                description="Remove all of a product"
            ),
            ToolTestCase(
                request="Remove 2 units of PROD456 from my cart",
                expected_tools=["remove_from_cart"],
                description="Remove partial quantity"
            )
        ]