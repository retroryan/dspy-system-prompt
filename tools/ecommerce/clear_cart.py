"""Clear cart tool implementation using the unified base class."""
from typing import List, ClassVar, Type
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import ClearCartOutput


class ClearCartTool(BaseTool):
    """Tool for clearing all items from the shopping cart."""
    
    NAME: ClassVar[str] = "clear_cart"
    MODULE: ClassVar[str] = "tools.ecommerce.clear_cart"
    
    class Arguments(BaseModel):
        """Arguments for clearing cart."""
        user_id: str = Field(..., description="User ID")
    
    # Tool definition as instance attributes
    description: str = "Clear all items from the shopping cart"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, user_id: str) -> dict:
        """Execute the tool to clear cart."""
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Clear cart using the manager
        result: ClearCartOutput = manager.clear_cart(user_id)
        
        # Convert Pydantic model to dict for response
        return result.model_dump(exclude_none=True)
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Clear my shopping cart",
                expected_tools=["clear_cart"],
                description="Empty the cart"
            ),
            ToolTestCase(
                request="Remove all items from my cart",
                expected_tools=["clear_cart"],
                description="Clear entire cart"
            )
        ]