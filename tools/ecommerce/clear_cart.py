"""Clear cart tool implementation using the unified base class."""
from typing import List, ClassVar, Type, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import ClearCartOutput

if TYPE_CHECKING:
    from agentic_loop.session import AgentSession


class ClearCartTool(BaseTool):
    """Tool for clearing all items from the shopping cart."""
    
    NAME: ClassVar[str] = "clear_cart"
    MODULE: ClassVar[str] = "tools.ecommerce.clear_cart"
    _accepts_session: ClassVar[bool] = True  # This tool needs user context
    
    class Arguments(BaseModel):
        """Arguments for clearing cart."""
        pass  # No arguments needed - user_id injected by session
    
    # Tool definition as instance attributes
    description: str = "Clear all items from the shopping cart"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to clear cart."""
        # Extract session from kwargs
        session: Optional['AgentSession'] = kwargs.pop('session', None)
        
        # Check for required session and user_id
        if not session or not session.user_id:
            return {"error": "User session required to clear cart"}
        
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Clear cart using the manager
        result: ClearCartOutput = manager.clear_cart(session.user_id)
        
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