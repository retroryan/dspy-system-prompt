"""
Shopping Bot with User Context and Session Management
This example demonstrates how to build a shopping bot using AWS Strands that:
1. Maintains user context through agent state
2. Persists sessions across conversations
3. Automatically passes user context to tools
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from strands import Agent, tool
from strands.session.file_session_manager import FileSessionManager
# For production, you could use S3SessionManager instead:
# from strands.session.s3_session_manager import S3SessionManager

# ============================================================================
# Mock Database/API Client (replace with your actual implementation)
# ============================================================================

class ShoppingAPIClient:
    """Mock API client for demonstration - replace with your actual API"""

    def __init__(self):
        # Mock data storage
        self.orders_db = {
            "user-123": [
                {"order_id": "ORD-001", "items": ["Laptop"], "status": "Delivered", "total": 1299.99},
                {"order_id": "ORD-002", "items": ["Mouse", "Keyboard"], "status": "In Transit", "total": 89.99}
            ],
            "user-456": [
                {"order_id": "ORD-003", "items": ["Monitor"], "status": "Processing", "total": 399.99}
            ]
        }

        self.carts_db = {
            "user-123": [],
            "user-456": []
        }

        self.products_db = [
            {"id": "PROD-001", "name": "Wireless Mouse", "price": 29.99, "in_stock": True},
            {"id": "PROD-002", "name": "Mechanical Keyboard", "price": 129.99, "in_stock": True},
            {"id": "PROD-003", "name": "4K Monitor", "price": 499.99, "in_stock": False},
            {"id": "PROD-004", "name": "USB-C Hub", "price": 49.99, "in_stock": True},
        ]

    def get_orders(self, user_id: str) -> List[Dict]:
        return self.orders_db.get(user_id, [])

    def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> Dict:
        if user_id not in self.carts_db:
            self.carts_db[user_id] = []

        product = next((p for p in self.products_db if p["id"] == product_id), None)
        if product:
            self.carts_db[user_id].append({
                "product_id": product_id,
                "name": product["name"],
                "quantity": quantity,
                "price": product["price"]
            })
            return {"success": True, "message": f"Added {product['name']} to cart"}
        return {"success": False, "message": "Product not found"}

    def get_cart(self, user_id: str) -> List[Dict]:
        return self.carts_db.get(user_id, [])

    def search_products(self, query: str) -> List[Dict]:
        results = []
        for product in self.products_db:
            if query.lower() in product["name"].lower():
                results.append(product)
        return results

# Initialize the mock API client
api_client = ShoppingAPIClient()

# ============================================================================
# Tool Definitions with User Context Access
# ============================================================================

@tool
def lookup_orders(status_filter: Optional[str] = None, agent: Agent = None) -> str:
    """
    Look up customer orders with optional status filter.

    Args:
        status_filter: Optional filter for order status (e.g., 'Delivered', 'In Transit')
        agent: The agent instance (automatically passed by Strands)
    """
    # Access user context from agent state
    user_id = agent.state.get("user_id")
    if not user_id:
        return "Error: User not authenticated. Please log in first."

    # Get orders from API
    orders = api_client.get_orders(user_id)

    # Apply status filter if provided
    if status_filter:
        orders = [o for o in orders if o["status"].lower() == status_filter.lower()]

    if not orders:
        return f"No orders found{' with status ' + status_filter if status_filter else ''}."

    # Format orders for display
    result = f"Found {len(orders)} order(s) for user {user_id}:\n\n"
    for order in orders:
        result += f"• Order {order['order_id']}:\n"
        result += f"  Items: {', '.join(order['items'])}\n"
        result += f"  Status: {order['status']}\n"
        result += f"  Total: ${order['total']:.2f}\n\n"

    # Update last action in state
    agent.state.set("last_action", f"viewed_orders_{datetime.now().isoformat()}")
    agent.state.set("orders_viewed_count", agent.state.get("orders_viewed_count", 0) + 1)

    return result

@tool
def add_to_cart(product_id: str, quantity: int = 1, agent: Agent = None) -> str:
    """
    Add a product to the shopping cart.

    Args:
        product_id: The ID of the product to add
        quantity: Number of items to add (default: 1)
        agent: The agent instance (automatically passed by Strands)
    """
    # Access user context from agent state
    user_id = agent.state.get("user_id")
    if not user_id:
        return "Error: User not authenticated. Please log in first."

    # Add to cart via API
    result = api_client.add_to_cart(user_id, product_id, quantity)

    if result["success"]:
        # Update agent state with cart activity
        agent.state.set("last_action", f"added_to_cart_{datetime.now().isoformat()}")
        cart_additions = agent.state.get("cart_additions_count", 0) + 1
        agent.state.set("cart_additions_count", cart_additions)

        # Track items in current session
        session_items = agent.state.get("session_cart_items", [])
        session_items.append(product_id)
        agent.state.set("session_cart_items", session_items)

    return result["message"]

@tool
def view_cart(agent: Agent = None) -> str:
    """
    View the current shopping cart contents.

    Args:
        agent: The agent instance (automatically passed by Strands)
    """
    # Access user context from agent state
    user_id = agent.state.get("user_id")
    if not user_id:
        return "Error: User not authenticated. Please log in first."

    # Get cart from API
    cart_items = api_client.get_cart(user_id)

    if not cart_items:
        return "Your cart is empty."

    # Calculate total
    total = sum(item["price"] * item["quantity"] for item in cart_items)

    # Format cart contents
    result = f"Shopping Cart for user {user_id}:\n\n"
    for item in cart_items:
        result += f"• {item['name']}\n"
        result += f"  Quantity: {item['quantity']}\n"
        result += f"  Price: ${item['price']:.2f} each\n\n"
    result += f"Total: ${total:.2f}"

    # Update state
    agent.state.set("last_action", f"viewed_cart_{datetime.now().isoformat()}")

    return result

@tool
def search_products(query: str, agent: Agent = None) -> str:
    """
    Search for products in the catalog.

    Args:
        query: Search query for products
        agent: The agent instance (automatically passed by Strands)
    """
    # This tool doesn't require user authentication but we can still track usage
    results = api_client.search_products(query)

    if not results:
        return f"No products found matching '{query}'."

    # Format results
    result = f"Found {len(results)} product(s) matching '{query}':\n\n"
    for product in results:
        result += f"• {product['name']} (ID: {product['id']})\n"
        result += f"  Price: ${product['price']:.2f}\n"
        result += f"  In Stock: {'Yes' if product['in_stock'] else 'No'}\n\n"

    # Track search history in state if user is authenticated
    if agent.state.get("user_id"):
        search_history = agent.state.get("search_history", [])
        search_history.append({"query": query, "timestamp": datetime.now().isoformat()})
        agent.state.set("search_history", search_history[-10:])  # Keep last 10 searches

    return result

@tool
def get_user_stats(agent: Agent = None) -> str:
    """
    Get statistics about the user's shopping activity.

    Args:
        agent: The agent instance (automatically passed by Strands)
    """
    user_id = agent.state.get("user_id")
    if not user_id:
        return "Error: User not authenticated."

    stats = f"User Statistics for {user_id}:\n"
    stats += f"• Orders viewed: {agent.state.get('orders_viewed_count', 0)}\n"
    stats += f"• Items added to cart: {agent.state.get('cart_additions_count', 0)}\n"
    stats += f"• Session started: {agent.state.get('session_start', 'Unknown')}\n"
    stats += f"• Last action: {agent.state.get('last_action', 'None')}\n"

    search_history = agent.state.get('search_history', [])
    if search_history:
        stats += f"• Recent searches: {', '.join([s['query'] for s in search_history[-3:]])}\n"

    return stats

# ============================================================================
# Shopping Bot Class
# ============================================================================

class ShoppingBot:
    """Main shopping bot class that manages user sessions and agent interactions"""

    def __init__(self, session_storage_dir: str = "/tmp/shopping_bot_sessions"):
        self.session_storage_dir = session_storage_dir
        self.tools = [
            lookup_orders,
            add_to_cart,
            view_cart,
            search_products,
            get_user_stats
        ]
        self.system_prompt = """You are a helpful shopping assistant. You can:
        - Look up customer orders
        - Search for products
        - Add items to the shopping cart
        - View the shopping cart
        - Provide user statistics
        
        Always be helpful and guide the user through their shopping experience.
        If a user tries to perform an action that requires authentication and they're not logged in,
        politely ask them to authenticate first."""

    def authenticate_user(self, user_id: str, user_email: str = None) -> Agent:
        """
        Authenticate a user and create/restore their session.

        Args:
            user_id: Unique user identifier
            user_email: User's email address (optional)

        Returns:
            Agent instance with user context loaded
        """
        # Create session manager with user-specific session ID
        session_manager = FileSessionManager(
            session_id=f"user-session-{user_id}",
            storage_dir=self.session_storage_dir
        )

        # For production, you could use S3SessionManager:
        # session_manager = S3SessionManager(
        #     session_id=f"user-session-{user_id}",
        #     bucket="shopping-bot-sessions",
        #     region="us-west-2"
        # )

        # Create agent with session manager
        agent = Agent(
            system_prompt=self.system_prompt,
            tools=self.tools,
            session_manager=session_manager,
            state={
                "user_id": user_id,
                "user_email": user_email or f"{user_id}@example.com",
                "authenticated": True,
                "session_start": datetime.now().isoformat(),
                "session_id": str(uuid.uuid4())
            }
        )

        # Check if this is a returning user
        if not agent.messages:
            # New session - send welcome message
            welcome_msg = f"Welcome back! I'm your shopping assistant. How can I help you today?"
            print(f"[System] New session created for user {user_id}")
        else:
            # Restored session
            print(f"[System] Session restored for user {user_id}")
            print(f"[System] Previous conversation has {len(agent.messages)} messages")

        return agent

    def create_guest_agent(self) -> Agent:
        """Create an agent for non-authenticated browsing"""
        return Agent(
            system_prompt=self.system_prompt + "\n\nNote: This is a guest session. Some features require authentication.",
            tools=[search_products],  # Limited tools for guests
            state={
                "user_id": None,
                "authenticated": False,
                "session_type": "guest",
                "session_start": datetime.now().isoformat()
            }
        )

# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Example of how to use the shopping bot"""

    # Initialize the shopping bot
    bot = ShoppingBot(session_storage_dir="./shopping_sessions")

    # Simulate user authentication (in production, this would come from your auth system)
    user_id = "user-123"
    user_email = "customer@example.com"

    print("=" * 60)
    print("Shopping Bot Demo - User Context & Session Management")
    print("=" * 60)

    # Authenticate user and get their agent
    agent = bot.authenticate_user(user_id, user_email)
    print(f"\n[System] Authenticated as user: {user_id}")

    # Example conversation flow
    conversations = [
        "Hello! Can you show me my recent orders?",
        "Search for wireless mouse",
        "Add product PROD-001 to my cart",
        "What's in my cart?",
        "Show me my stats"
    ]

    for user_message in conversations:
        print(f"\n[User]: {user_message}")
        response = agent(user_message)
        print(f"[Bot]: {response.message}")

    # Demonstrate session persistence
    print("\n" + "=" * 60)
    print("Simulating session end and restart...")
    print("=" * 60)

    # Create a new agent instance with the same user_id
    # This will restore the previous session
    restored_agent = bot.authenticate_user(user_id, user_email)

    # The agent remembers the conversation and state
    print(f"\n[User]: What did we just talk about?")
    response = restored_agent("What did we just talk about and what's in my cart?")
    print(f"[Bot]: {response.message}")

    # Show that state was preserved
    print(f"\n[System] Restored state: {json.dumps(restored_agent.state.get(), indent=2)}")

# ============================================================================
# Lambda Handler Example (for AWS deployment)
# ============================================================================

def lambda_handler(event, context):
    """
    AWS Lambda handler for the shopping bot.
    Expects authenticated requests with user context from API Gateway/Cognito.
    """
    try:
        # Extract user context from authenticated request
        # This assumes API Gateway with Cognito authorizer
        claims = event['requestContext']['authorizer']['claims']
        user_id = claims['sub']  # Cognito user ID
        user_email = claims.get('email', '')

        # Parse request body
        body = json.loads(event['body'])
        user_message = body.get('message', '')

        # Initialize bot and authenticate user
        bot = ShoppingBot(
            # Use S3 for Lambda deployments
            session_storage_dir="/tmp/sessions"  # Lambda's /tmp directory
        )
        agent = bot.authenticate_user(user_id, user_email)

        # Process user message
        response = agent(user_message)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': response.message,
                'session_id': agent.state.get('session_id'),
                'authenticated': True
            })
        }

    except KeyError:
        # Handle unauthenticated requests
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Authentication required'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

if __name__ == "__main__":
    main()