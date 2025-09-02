"""Get order tool implementation using the unified base class."""
from typing import List, ClassVar, Type, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import Order

if TYPE_CHECKING:
    from agentic_loop.session import AgentSession


class GetOrderTool(BaseTool):
    """Tool for retrieving order information by order ID."""
    
    NAME: ClassVar[str] = "get_order"
    MODULE: ClassVar[str] = "tools.ecommerce.get_order"
    _accepts_session: ClassVar[bool] = True  # This tool needs user context
    
    class Arguments(BaseModel):
        """Argument validation model."""
        order_id: str = Field(
            ..., 
            min_length=1, 
            description="The order ID to retrieve"
        )
    
    # Tool definition as instance attributes
    description: str = "Get order details by order ID"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to get order details."""
        # Extract session from kwargs
        session: Optional['AgentSession'] = kwargs.pop('session', None)
        
        # Check for required session and user_id
        if not session or not session.user_id:
            return {"error": "User session required to get order details"}
        
        # Get order_id from kwargs
        order_id = kwargs.get('order_id')
        
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Get order using the manager
        result = manager.get_order(session.user_id, order_id)
        
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
