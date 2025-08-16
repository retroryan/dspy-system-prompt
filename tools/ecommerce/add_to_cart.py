"""Add to cart tool implementation using the unified base class."""
from typing import List, ClassVar, Type, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from shared.tool_utils.error_handling import safe_tool_execution
from .cart_inventory_manager import CartInventoryManager
from .models import AddToCartOutput

if TYPE_CHECKING:
    from agentic_loop.session import AgentSession


class AddToCartTool(BaseTool):
    """Tool for adding products to shopping cart."""
    
    NAME: ClassVar[str] = "add_to_cart"
    MODULE: ClassVar[str] = "tools.ecommerce.add_to_cart"
    _accepts_session: ClassVar[bool] = True  # This tool needs user context
    
    class Arguments(BaseModel):
        """Arguments for adding to cart."""
        product_id: str = Field(..., description="Product ID to add to cart")
        quantity: int = Field(default=1, ge=1, description="Quantity to add")
    
    # Tool definition as instance attributes
    description: str = "Add a product to the shopping cart"
    args_model: Type[BaseModel] = Arguments
    
    @safe_tool_execution
    def execute(self, **kwargs) -> dict:
        """Execute the tool to add product to cart."""
        # Extract session from kwargs
        session: Optional['AgentSession'] = kwargs.pop('session', None)
        
        # Check for required session and user_id
        if not session or not session.user_id:
            return {"error": "User session required to add to cart"}
        
        # Get product_id and quantity from kwargs
        product_id = kwargs.get('product_id')
        quantity = kwargs.get('quantity', 1)
        
        # Use CartInventoryManager for real operations
        manager = CartInventoryManager()
        
        # Add to cart using the manager
        result: AddToCartOutput = manager.add_to_cart(session.user_id, product_id, quantity)
        
        # Check if operation failed and raise appropriate error
        if result.status == "failed" and result.error:
            # The manager already returns structured errors, just pass them through
            return result.model_dump(exclude_none=True)
        
        # Convert Pydantic model to dict for response
        return result.model_dump(exclude_none=True)
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Add product PROD123 to my cart",
                expected_tools=["add_to_cart"],
                description="Add single product"
            ),
            ToolTestCase(
                request="Add 3 units of SKU456 to cart",
                expected_tools=["add_to_cart"],
                description="Add multiple quantities"
            )
        ]