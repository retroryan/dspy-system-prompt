"""Track order tool implementation using the unified base class."""
from typing import List, ClassVar, Type
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase
from .cart_inventory_manager import CartInventoryManager
from .models import Order


class TrackOrderTool(BaseTool):
    """Tool for tracking order status."""
    
    NAME: ClassVar[str] = "track_order"
    MODULE: ClassVar[str] = "tools.ecommerce.track_order"
    
    class Arguments(BaseModel):
        """Arguments for tracking an order."""
        user_id: str = Field(..., description="User ID")
        order_id: str = Field(..., description="Order ID")
    
    # Tool definition as instance attributes
    description: str = "Track the status of an order"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, user_id: str, order_id: str) -> dict:
        """Execute the tool to track an order."""
        # Use CartInventoryManager for operations
        manager = CartInventoryManager()
        
        # Get order using the manager
        result = manager.get_order(user_id, order_id)
        
        # Check if result is an Order model or a dict with error
        if isinstance(result, Order):
            order_dict = result.model_dump(exclude_none=True)
            # Add tracking information
            status = order_dict.get("status", "pending")
            
            # Generate tracking info based on status
            if status == "delivered":
                tracking_info = "Order has been delivered"
                estimated_delivery = "Already delivered"
            elif status == "shipped":
                tracking_info = "Order is in transit"
                estimated_delivery = "2-3 business days"
            elif status == "processing":
                tracking_info = "Order is being prepared"
                estimated_delivery = "5-7 business days"
            else:
                tracking_info = f"Order status: {status}"
                estimated_delivery = "To be determined"
            
            return {
                "order_id": order_id,
                "status": status,
                "tracking_info": tracking_info,
                "estimated_delivery": estimated_delivery,
                "order_details": order_dict
            }
        else:
            return result
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Track my order ORD123",
                expected_tools=["track_order"],
                description="Basic order tracking"
            ),
            ToolTestCase(
                request="Where is my order 12345?",
                expected_tools=["track_order"],
                description="Order status inquiry"
            ),
            ToolTestCase(
                request="Check shipping status for order ORD789",
                expected_tools=["track_order"],
                description="Shipping status check"
            )
        ]