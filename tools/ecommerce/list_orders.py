"""List orders tool implementation using the unified base class."""
from typing import List, ClassVar, Type, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager

if TYPE_CHECKING:
    from agentic_loop.session import AgentSession


class ListOrdersTool(BaseTool):
    """Tool for listing orders for a user."""
    
    NAME: ClassVar[str] = "list_orders"
    MODULE: ClassVar[str] = "tools.ecommerce.list_orders"
    _accepts_session: ClassVar[bool] = True  # This tool needs user context
    
    class Arguments(BaseModel):
        """Argument validation model."""
        status: Optional[str] = Field(
            default=None,
            description="Filter by order status (pending, processing, shipped, delivered, cancelled)"
        )
    
    # Tool definition as instance attributes
    description: str = "List all orders for a user"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to list user orders."""
        # Extract session from kwargs
        session: Optional['AgentSession'] = kwargs.pop('session', None)
        
        # Check for required session and user_id
        if not session or not session.user_id:
            return {"error": "User session required to list orders"}
        
        # Get status filter if provided
        status = kwargs.get('status', None)
        
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # List orders using the manager
        orders = manager.list_orders(session.user_id, status)
        
        return {"orders": orders, "count": len(orders)}
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Show me all my orders",
                expected_tools=["list_orders"],
                description="Basic order listing"
            ),
            ToolTestCase(
                request="Show me my pending orders",
                expected_tools=["list_orders"],
                description="Filter by status"
            ),
            ToolTestCase(
                request="List my order history",
                expected_tools=["list_orders"],
                description="List customer orders"
            )
        ]