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

    E-COMMERCE GUIDELINES:
    - Always use specific identifiers when referencing orders, products, or customers
    - For product searches, be flexible with search terms and filters
    - When tracking orders, use exact order IDs when provided
    
    ORDER MANAGEMENT PRECISION:
    - Order IDs typically follow patterns like "ORD123", "ORD001", or alphanumeric codes
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
        Returns 10 complex test cases that demonstrate conversation history and memory management.
        
        These cases are designed to build on each other, showing how the system
        maintains context across interactions and manages memory efficiently.
        All test cases use actual data from the database for demo_user.
        """
        # Complex conversation-driven test cases using actual data
        test_cases = [
            # Test 1: Start with order history - demo_user has 25 orders
            ToolSetTestCase(
                request="Show me all my recent orders and tell me which ones are delivered",
                expected_tools=["list_orders"],
                expected_arguments={
                    "list_orders": {
                        "user_id": "demo_user"
                    }
                },
                description="Initial order history query - establishes context with real orders",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 2: Reference previous context - ORD003 ($1199.98) is most expensive  
            ToolSetTestCase(
                request="Show me details of the most expensive order from those",
                expected_tools=["get_order"],
                expected_arguments={},
                description="Context-dependent detail retrieval - should find ORD003 ($1199.98)",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 3: Track specific high-value delivered order
            ToolSetTestCase(
                request="Track the status of order ORD004 - the one with the gaming laptop",
                expected_tools=["track_order"],
                expected_arguments={
                    "track_order": {
                        "user_id": "demo_user",
                        "order_id": "ORD004"
                    }
                },
                description="Track specific delivered order with Gaming Laptop ($899.99)",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 4: Start shopping - search for available products
            ToolSetTestCase(
                request="I need a new keyboard. Show me gaming keyboards under $150",
                expected_tools=["search_products"],
                expected_arguments={
                    "search_products": {
                        "query": "gaming keyboard",
                        "max_price": 150
                    }
                },
                description="Product search - KB123, KB456, KB789 are available",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 5: Add specific product to cart
            ToolSetTestCase(
                request="Add the RGB mechanical keyboard KB123 to my cart",
                expected_tools=["add_to_cart"],
                expected_arguments={
                    "add_to_cart": {
                        "user_id": "demo_user",
                        "product_sku": "KB123"
                    }
                },
                description="Add specific product KB123 ($129.99) to cart",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 6: Continue shopping with context
            ToolSetTestCase(
                request="Now find me a mouse to go with that keyboard, preferably wireless",
                expected_tools=["search_products"],
                expected_arguments={},
                description="Continue shopping - MS001 and MS002 mice available",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 7: Check cart and analyze total
            ToolSetTestCase(
                request="What's in my cart now and what's the total?",
                expected_tools=["get_cart"],
                expected_arguments={
                    "get_cart": {
                        "user_id": "demo_user"
                    }
                },
                description="Check cart contents and total after multiple additions",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 8: Return scenario with actual order
            ToolSetTestCase(
                request="I want to return the headphones from order ORD002 because they're defective",
                expected_tools=["return_item"],
                expected_arguments={
                    "return_item": {
                        "user_id": "demo_user",
                        "order_id": "ORD002",
                        "item_id": "HD001",
                        "reason": "defective"
                    }
                },
                description="Return HD001 Wireless Headphones Pro from ORD002",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 9: Checkout the cart
            ToolSetTestCase(
                request="Checkout my cart and ship it to 789 Tech Ave, Demo City, CA 90210",
                expected_tools=["checkout"],
                expected_arguments={
                    "checkout": {
                        "user_id": "demo_user",
                        "shipping_address": "789 Tech Ave, Demo City, CA 90210"
                    }
                },
                description="Complete checkout with accumulated cart items",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            ),
            # Test 10: Summary requiring full memory
            ToolSetTestCase(
                request="Summarize everything we did: what orders we reviewed, what I bought, what I returned",
                expected_tools=[],
                expected_arguments={},
                description="Full conversation summary testing complete memory retention",
                tool_set=cls.NAME,
                scenario="conversation_with_memory"
            )
        ]
        
        return test_cases
    
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