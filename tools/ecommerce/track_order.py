"""Track order tool implementation using the unified base class."""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, ClassVar, Dict, Any, Type
from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class TrackOrderTool(BaseTool):
    """Tool for tracking order status."""
    
    NAME: ClassVar[str] = "track_order"
    MODULE: ClassVar[str] = "tools.ecommerce.track_order"
    
    class Arguments(BaseModel):
        """Arguments for tracking an order."""
        order_id: str = Field(..., description="Order ID")
    
    # Tool definition as instance attributes
    description: str = "Track the status of an order"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, order_id: str) -> dict:
        """Execute the tool to track an order."""
        # First try the new orders.json file
        file_path = Path(__file__).resolve().parent.parent / "data" / "orders.json"
        
        # Fall back to customer_order_data.json if orders.json doesn't exist
        if not file_path.exists():
            file_path = Path(__file__).resolve().parent.parent / "data" / "customer_order_data.json"
            
        if file_path.exists():
            with open(file_path, "r") as file:
                data = json.load(file)
            order_list = data["orders"]
            
            for order in order_list:
                # Check both 'order_id' and 'id' fields for compatibility
                if order.get("order_id") == order_id or order.get("id") == order_id:
                    # Calculate estimated delivery based on status
                    status = order.get("status", "processing")
                    tracking = order.get("tracking_number")
                    
                    # Estimate delivery date based on status
                    if status == "delivered":
                        delivery_date = "Already delivered"
                    elif status == "shipped":
                        # Assume 2-3 days from order date for shipped items
                        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
                        estimated_delivery = order_date + timedelta(days=3)
                        delivery_date = estimated_delivery.strftime("%Y-%m-%d")
                    elif status == "processing":
                        # Assume 5-7 days from order date for processing items
                        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
                        estimated_delivery = order_date + timedelta(days=7)
                        delivery_date = estimated_delivery.strftime("%Y-%m-%d")
                    else:
                        delivery_date = "Unknown"
                    
                    return {
                        "order_id": order_id,
                        "status": status,
                        "delivery_date": delivery_date,
                        "tracking_number": tracking if tracking else f"TRK{order_id}",
                        "shipping_address": order.get("shipping_address", "Not available")
                    }
        
        # If order not found in file, return generic tracking info
        return {
            "order_id": order_id,
            "status": "In transit",
            "delivery_date": "Tomorrow",
            "tracking_number": f"TRK{order_id}"
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Track my order ORD789",
                expected_tools=["track_order"],
                description="Track specific order"
            ),
            ToolTestCase(
                request="Where is my package ORDER123?",
                expected_tools=["track_order"],
                description="Check package location"
            )
        ]