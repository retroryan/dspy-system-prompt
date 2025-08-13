"""Get order tool implementation using the unified base class."""
from typing import List, ClassVar, Type
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import Order


class GetOrderTool(BaseTool):
    """Tool for retrieving order information by order ID."""
    
    NAME: ClassVar[str] = "get_order"
    MODULE: ClassVar[str] = "tools.ecommerce.get_order"
    
    class Arguments(BaseModel):
        """Argument validation model."""
        user_id: str = Field(..., description="User ID")
        order_id: str = Field(
            ..., 
            min_length=1, 
            description="The order ID to retrieve"
        )
    
    # Tool definition as instance attributes
    description: str = "Get order details by order ID"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, user_id: str, order_id: str) -> dict:
        """Execute the tool to get order details."""
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Get order using the manager
        result = manager.get_order(user_id, order_id)
        
        # Check if result is an Order model or a dict with error
        if isinstance(result, Order):
            return result.model_dump(exclude_none=True)
        else:
            return result
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Get order details for order 12345",
                expected_tools=["get_order"],
                description="Basic order lookup"
            ),
            ToolTestCase(
                request="I need to check my order ORD-001",
                expected_tools=["get_order"],
                description="Order status check"
            ),
            ToolTestCase(
                request="Show me information about order ABC123",
                expected_tools=["get_order"],
                description="Order information request"
            )
        ]
