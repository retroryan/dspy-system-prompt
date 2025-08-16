"""Get cart tool implementation using the unified base class."""
from typing import List, ClassVar, Type, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import Cart

if TYPE_CHECKING:
    from agentic_loop.session import AgentSession


class GetCartTool(BaseTool):
    """Tool for retrieving the current shopping cart."""
    
    NAME: ClassVar[str] = "get_cart"
    MODULE: ClassVar[str] = "tools.ecommerce.get_cart"
    _accepts_session: ClassVar[bool] = True  # This tool needs user context
    
    class Arguments(BaseModel):
        """Arguments for getting cart."""
        pass  # No arguments needed - user_id from session
    
    # Tool definition as instance attributes
    description: str = "Get the current shopping cart for a user"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to get cart contents."""
        # Extract session from kwargs
        session: Optional['AgentSession'] = kwargs.pop('session', None)
        
        # Check for required session and user_id
        if not session or not session.user_id:
            return {"error": "User session required to view cart"}
        
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Get cart using the manager
        cart: Cart = manager.get_cart(session.user_id)
        
        # Convert Pydantic model to dict for response
        return cart.model_dump(exclude_none=True)
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Show me my shopping cart",
                expected_tools=["get_cart"],
                description="View cart contents"
            ),
            ToolTestCase(
                request="What's in my cart?",
                expected_tools=["get_cart"],
                description="Check cart items"
            )
        ]