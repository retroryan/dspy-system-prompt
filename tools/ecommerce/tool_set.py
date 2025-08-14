from typing import List, ClassVar, Type, Optional
from shared.tool_utils.base_tool_sets import ToolSet, ToolSetConfig, ToolSetTestCase
from datetime import datetime, timedelta
import dspy
import logging

logger = logging.getLogger(__name__)


# NOTE: ReactSignatures in this project follow a specific design pattern:
# - They only define input fields (e.g., user_query)
# - The ReactAgent dynamically adds the standard React output fields at runtime:
#   (next_thought, next_tool_name, next_tool_args)
# - This separation allows tool sets to provide domain-specific instructions
#   while the ReactAgent handles the standard React pattern implementation
class EcommerceReactSignature(dspy.Signature):
    """E-commerce tool execution requirements.
    
    CURRENT DATE: {current_date}
    CURRENT USER: demo_user (use this as user_id for all operations requiring user context)

    E-COMMERCE GUIDELINES:
    - Always use specific identifiers when referencing orders, products, or customers
    - For product searches, be flexible with search terms and filters
    - When tracking orders, use exact order IDs when provided
    - IMPORTANT: Always include user_id="demo_user" when calling tools that require user context
    
    ORDER MANAGEMENT PRECISION:
    - Order IDs typically follow patterns like "ORD123", "ORD001", or alphanumeric codes
    - Always use user_id="demo_user" for order operations (track_order, list_orders, get_order, return_item)
    - Product SKUs are usually alphanumeric codes
    - Tracking numbers may have various formats depending on carrier
    
    PRODUCT SEARCH OPTIMIZATION:
    - Support partial product name matching
    - Allow price range filtering
    - Enable category-based searches
    - Handle brand and feature-specific queries
    
    CUSTOMER SUPPORT WORKFLOW:
    - For returns, always verify order details first
    - Provide clear reason codes for cancellations/returns
    - Include relevant order information in responses
    - Handle edge cases like expired return windows
    
    CART OPERATIONS:
    - Always use user_id="demo_user" for cart operations (add_to_cart, get_cart, remove_from_cart, etc.)
    - Validate product availability before adding to cart
    - Handle quantity specifications properly
    - Support multiple items in single operations when applicable
    
    Use precise identifiers and maintain data consistency across operations.
    """
    
    user_query: str = dspy.InputField(
        desc="E-commerce query that may reference orders, products, customers, or shopping operations"
    )


class EcommerceExtractSignature(dspy.Signature):
    """Synthesize e-commerce information into user-friendly responses.
    
    Take the e-commerce data from tools and create a comprehensive, natural response
    that directly addresses the user's query about orders, products, or shopping.
    """
    
    user_query: str = dspy.InputField(
        desc="Original e-commerce query from user"
    )
    ecommerce_analysis: str = dspy.OutputField(
        desc="Comprehensive, user-friendly e-commerce analysis that directly answers the query"
    )


class EcommerceToolSet(ToolSet):
    """
    A specific tool set for e-commerce and shopping tools.
    
    This set includes tools for order management, product search, cart operations,
    and customer support functionalities.
    """
    NAME: ClassVar[str] = "ecommerce"
    
    def __init__(self):
        """
        Initializes the EcommerceToolSet, defining its name, description,
        and the specific tool classes it encompasses.
        """
        from tools.ecommerce.get_order import GetOrderTool
        from tools.ecommerce.list_orders import ListOrdersTool
        from tools.ecommerce.add_to_cart import AddToCartTool
        from tools.ecommerce.search_products import SearchProductsTool
        from tools.ecommerce.track_order import TrackOrderTool
        from tools.ecommerce.return_item import ReturnItemTool
        from tools.ecommerce.get_cart import GetCartTool
        from tools.ecommerce.checkout import CheckoutTool
        from tools.ecommerce.update_cart_item import UpdateCartItemTool
        from tools.ecommerce.remove_from_cart import RemoveFromCartTool
        from tools.ecommerce.clear_cart import ClearCartTool
        
        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="E-commerce and shopping tools for order management, product search, cart operations, and customer support",
                tool_classes=[
                    # Product search
                    SearchProductsTool,
                    # Cart operations
                    AddToCartTool,
                    GetCartTool,
                    UpdateCartItemTool,
                    RemoveFromCartTool,
                    ClearCartTool,
                    CheckoutTool,
                    # Order management
                    GetOrderTool,
                    ListOrdersTool,
                    TrackOrderTool,
                    # Customer support
                    ReturnItemTool
                ]
            )
        )
    
    def _perform_initialization(self) -> None:
        """
        Initialize the e-commerce database with test data.
        
        This ensures that the SQLite database is populated with:
        - Products from products.json
        - Demo orders
        - Demo carts
        """
        from tools.ecommerce.cart_inventory_manager import CartInventoryManager
        
        logger.info("Initializing e-commerce database with test data...")
        
        # Create the manager and reset the database with demo data
        manager = CartInventoryManager()
        manager.reset_database()
        
        logger.info("E-commerce database initialized successfully")
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Returns a predefined list of test cases for e-commerce scenarios.
        
        These cases cover various interactions with e-commerce tools, including
        order management, product search, cart operations, and customer support.
        """
        # Basic test cases
        basic_cases = [
            ToolSetTestCase(
                request="I want to check my order status for order ORD001",
                expected_tools=["track_order"],
                expected_arguments={
                    "track_order": {
                        "user_id": "demo_user",
                        "order_id": "ORD001"
                    }
                },
                description="Check specific order status",
                tool_set=cls.NAME,
                scenario="order_management"
            ),
            ToolSetTestCase(
                request="Show me all orders for demo_user",
                expected_tools=["list_orders"],
                expected_arguments={
                    "list_orders": {
                        "user_id": "demo_user"
                    }
                },
                description="List customer orders",
                tool_set=cls.NAME,
                scenario="order_management"
            ),
            ToolSetTestCase(
                request="Add product KB123 to my cart",
                expected_tools=["add_to_cart"],
                expected_arguments={
                    "add_to_cart": {
                        "user_id": "demo_user",
                        "product_sku": "KB123"
                    }
                },
                description="Add item to shopping cart",
                tool_set=cls.NAME,
                scenario="shopping"
            ),
            ToolSetTestCase(
                request="Search for wireless headphones under $100",
                expected_tools=["search_products"],
                expected_arguments={
                    "search_products": {
                        "query": "wireless headphones",
                        "max_price": 100
                    }
                },
                description="Product search with price filter",
                tool_set=cls.NAME,
                scenario="shopping"
            ),
            ToolSetTestCase(
                request="Track my order ORD002",
                expected_tools=["track_order"],
                expected_arguments={
                    "track_order": {
                        "user_id": "demo_user",
                        "order_id": "ORD002"
                    }
                },
                description="Track shipment status",
                tool_set=cls.NAME,
                scenario="order_management"
            ),
            ToolSetTestCase(
                request="Get details for order ORD003",
                expected_tools=["get_order"],
                expected_arguments={
                    "get_order": {
                        "user_id": "demo_user",
                        "order_id": "ORD003"
                    }
                },
                description="Retrieve order details",
                tool_set=cls.NAME,
                scenario="order_management"
            ),
            ToolSetTestCase(
                request="Return item HD001 from order ORD002 because it's defective",
                expected_tools=["get_order", "return_item"],
                expected_arguments={
                    "get_order": {
                        "user_id": "demo_user",
                        "order_id": "ORD002"
                    },
                    "return_item": {
                        "user_id": "demo_user",
                        "order_id": "ORD002",
                        "item_id": "HD001",
                        "reason": "defective"
                    }
                },
                description="Return defective item",
                tool_set=cls.NAME,
                scenario="customer_support"
            ),
            ToolSetTestCase(
                request="I need to find laptops in my price range and add one to my cart",
                expected_tools=["search_products"],
                expected_arguments={
                    "search_products": {
                        "query": "laptops"
                    }
                },
                description="Multi-step shopping process - search phase",
                tool_set=cls.NAME,
                scenario="shopping"
            ),
            ToolSetTestCase(
                request="Find bluetooth speakers under $50",
                expected_tools=["search_products"],
                expected_arguments={
                    "search_products": {
                        "query": "bluetooth speakers",
                        "max_price": 50
                    }
                },
                description="Product search with specific category and price",
                tool_set=cls.NAME,
                scenario="shopping"
            ),
            ToolSetTestCase(
                request="Check the status of order ORD004 and get full order details",
                expected_tools=["get_order"],
                expected_arguments={
                    "get_order": {
                        "user_id": "demo_user",
                        "order_id": "ORD004"
                    }
                },
                description="Comprehensive order inquiry",
                tool_set=cls.NAME,
                scenario="order_management"
            ),
            ToolSetTestCase(
                request="List all my recent orders and track the latest one",
                expected_tools=["list_orders", "track_order"],
                expected_arguments={
                    "list_orders": {
                        "user_id": "demo_user"
                    }
                },
                description="Recent orders with tracking follow-up",
                tool_set=cls.NAME,
                scenario="order_management"
            ),
            ToolSetTestCase(
                request="Search for gaming keyboards and add the best one under $150 to cart",
                expected_tools=["search_products", "add_to_cart"],
                expected_arguments={
                    "search_products": {
                        "query": "gaming keyboards",
                        "max_price": 150
                    }
                },
                description="Product search with intent to purchase",
                tool_set=cls.NAME,
                scenario="shopping"
            )
        ]
        
        # Complex test scenarios (from run_demo_ecom.sh)
        complex_cases = [
            ToolSetTestCase(
                request="I have a budget of $1500. I need to buy a laptop for work and a wireless mouse. Find the best laptop under my budget, add it to my cart with a compatible mouse, and then checkout to 789 Tech Ave.",
                expected_tools=["search_products", "add_to_cart", "checkout"],
                expected_arguments={
                    "checkout": {
                        "user_id": "demo_user",
                        "shipping_address": "789 Tech Ave"
                    }
                },
                description="Multi-step purchase with budget constraints",
                tool_set=cls.NAME,
                scenario="complex_shopping"
            ),
            ToolSetTestCase(
                request="Compare gaming keyboards under $150 and wireless headphones under $100. Add the highest-rated item from each category to my cart, but only if the total stays under $200.",
                expected_tools=["search_products", "add_to_cart", "get_cart"],
                expected_arguments={},
                description="Comparative shopping with price optimization",
                tool_set=cls.NAME,
                scenario="complex_shopping"
            ),
            ToolSetTestCase(
                request="For user demo_user, check the status of their most recent order. If it's been delivered and contains any electronics over $500, initiate a return for the most expensive item citing 'changed mind'.",
                expected_tools=["list_orders", "track_order", "get_order", "return_item"],
                expected_arguments={},
                description="Order tracking and conditional return processing",
                tool_set=cls.NAME,
                scenario="complex_support"
            ),
            ToolSetTestCase(
                request="I want to buy 2 wireless mice and 1 mechanical keyboard. Add them to my cart.",
                expected_tools=["search_products", "add_to_cart"],
                expected_arguments={},
                description="Multiple product purchase",
                tool_set=cls.NAME,
                scenario="complex_shopping"
            ),
            ToolSetTestCase(
                request="For user demo_user, list all their delivered orders from the past month. For any order over $300, check if it contains laptops or monitors, and if so, process a return for quality issues and tell me the expected refund amount.",
                expected_tools=["list_orders", "get_order", "return_item"],
                expected_arguments={},
                description="Complex return with refund verification",
                tool_set=cls.NAME,
                scenario="complex_support"
            ),
            ToolSetTestCase(
                request="I need to buy a laptop under $1000 and gaming accessories under $200. Add them to my cart and calculate the total.",
                expected_tools=["search_products", "add_to_cart", "get_cart"],
                expected_arguments={},
                description="Multi-product shopping with budget",
                tool_set=cls.NAME,
                scenario="complex_shopping"
            ),
            ToolSetTestCase(
                request="Check what's currently in my cart. If the total is over $500 and includes any out-of-stock items, remove them and suggest similar alternatives that are in stock.",
                expected_tools=["get_cart", "remove_from_cart", "search_products", "add_to_cart"],
                expected_arguments={},
                description="Abandoned cart recovery with alternatives",
                tool_set=cls.NAME,
                scenario="complex_cart"
            ),
            ToolSetTestCase(
                request="For user demo_user, review their last 5 orders and identify the most frequently purchased category. Then search for new products in that category and add the top-rated one to their cart if it's different from what they've bought before.",
                expected_tools=["list_orders", "get_order", "search_products", "add_to_cart"],
                expected_arguments={},
                description="Order history analysis with reorder",
                tool_set=cls.NAME,
                scenario="complex_personalization"
            ),
            ToolSetTestCase(
                request="I'm setting up a home office. Find a laptop, monitor, keyboard, and mouse that are all compatible and stay within a $2000 budget. Prioritize items that are frequently bought together.",
                expected_tools=["search_products", "add_to_cart", "get_cart"],
                expected_arguments={},
                description="Bundle shopping with compatibility check",
                tool_set=cls.NAME,
                scenario="complex_shopping"
            ),
            ToolSetTestCase(
                request="I received order ORD012 but one item was damaged. First check the order details, then process a return for the damaged item with reason 'arrived damaged', and add a replacement to my cart for immediate reorder.",
                expected_tools=["get_order", "return_item", "search_products", "add_to_cart"],
                expected_arguments={
                    "get_order": {
                        "user_id": "demo_user",
                        "order_id": "ORD012"
                    }
                },
                description="Customer service escalation flow",
                tool_set=cls.NAME,
                scenario="complex_support"
            )
        ]
        
        return basic_cases + complex_cases
    
    @classmethod
    def get_react_signature(cls) -> Type[dspy.Signature]:
        """
        Return the React signature for e-commerce tools.
        
        This signature contains e-commerce operation instructions to ensure
        tools receive proper identifiers and handle shopping workflows correctly.
        """
        return EcommerceReactSignature
    
    @classmethod
    def get_extract_signature(cls) -> Type[dspy.Signature]:
        """
        Return the Extract signature for e-commerce synthesis.
        
        This signature focuses on synthesizing e-commerce information into
        user-friendly analysis without any tool-specific instructions.
        """
        return EcommerceExtractSignature