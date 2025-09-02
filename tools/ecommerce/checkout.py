"""Checkout tool implementation using the unified base class."""
from typing import List, ClassVar, Type, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import CheckoutOutput

if TYPE_CHECKING:
    from agentic_loop.session import AgentSession


class CheckoutTool(BaseTool):
    """Tool for checking out and completing a purchase."""
    
    NAME: ClassVar[str] = "checkout"
    MODULE: ClassVar[str] = "tools.ecommerce.checkout"
    _accepts_session: ClassVar[bool] = True  # This tool needs user context
    
    class Arguments(BaseModel):
        """Arguments for checkout."""
        shipping_address: str = Field(..., description="Shipping address for the order")
    
    # Tool definition as instance attributes
    description: str = "Checkout the current cart and create an order"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to checkout cart."""
        # Extract session from kwargs
        session: Optional['AgentSession'] = kwargs.pop('session', None)
        
        # Check for required session and user_id
        if not session or not session.user_id:
            return {"error": "User session required to checkout"}
        
        # Get shipping_address from kwargs
        shipping_address = kwargs.get('shipping_address')
        
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Checkout using the manager
        result: CheckoutOutput = manager.checkout_cart(session.user_id, shipping_address)
        
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