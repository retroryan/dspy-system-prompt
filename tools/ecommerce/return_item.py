"""Return item tool implementation using the unified base class."""
from typing import List, ClassVar, Type, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import CreateReturnOutput

if TYPE_CHECKING:
    from agentic_loop.session import AgentSession


class ReturnItemTool(BaseTool):
    """Tool for returning items for refund or exchange."""
    
    NAME: ClassVar[str] = "return_item"
    MODULE: ClassVar[str] = "tools.ecommerce.return_item"
    _accepts_session: ClassVar[bool] = True  # This tool needs user context
    
    class Arguments(BaseModel):
        """Arguments for returning an item."""
        order_id: str = Field(..., description="Order ID")
        item_id: str = Field(..., description="Item ID to return")
        reason: str = Field(..., description="Return reason")
    
    # Tool definition as instance attributes
    description: str = "Return an item for refund or exchange"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to return an item."""
        # Extract session from kwargs
        session: Optional['AgentSession'] = kwargs.pop('session', None)
        
        # Check for required session and user_id
        if not session or not session.user_id:
            return {"error": "User session required to return items"}
        
        # Get arguments from kwargs
        order_id = kwargs.get('order_id')
        item_id = kwargs.get('item_id')
        reason = kwargs.get('reason')
        
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Create return using the manager
        result: CreateReturnOutput = manager.create_return(session.user_id, order_id, item_id, reason)
        
        # Convert Pydantic model to dict for response
        return result.model_dump(exclude_none=True)
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Return item ITEM123 from order ORD456 because it's defective",
                expected_tools=["return_item"],
                description="Return defective item"
            ),
            ToolTestCase(
                request="I want to return SKU789 from my last order, wrong size",
                expected_tools=["list_orders", "return_item"],
                description="Return for size issue"
            )
        ]