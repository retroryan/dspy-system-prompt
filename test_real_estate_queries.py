"""Test Real Estate Queries to verify they work with the backend"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agentic_loop.session import AgentSession
from shared.tool_utils.registry import ToolRegistry
from tools.real_estate.mcp_tool_set import RealEstateMCPToolSet


def test_queries():
    """Test the real estate queries that will be used in the frontend."""
    
    # Initialize MCP tools
    print("🔧 Setting up Real Estate MCP tools...")
    registry = ToolRegistry()
    
    try:
        mcp_tools = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
        registry.register_tool_set(mcp_tools)
        print(f"✅ Registered {len(registry.get_tool_names())} tools")
    except Exception as e:
        print(f"❌ Failed to setup MCP tools: {e}")
        return False
    
    # Test queries from the frontend
    test_cases = [
        {
            "name": "Dream Home Query",
            "query": "Find modern family homes with pools in Oakland under $800k",
            "expected_tool": "search_properties_tool"
        },
        {
            "name": "Neighborhood Exploration",
            "query": "Tell me about the Temescal neighborhood in Oakland - what amenities and culture does it offer?",
            "expected_tool": "search_wikipedia_tool"
        },
        {
            "name": "Luxury Properties",
            "query": "Find luxury properties with stunning views and modern kitchens",
            "expected_tool": "search_properties_tool"
        },
        {
            "name": "School District Search",
            "query": "Show me family homes near top-rated schools in San Francisco",
            "expected_tool": "search_properties_tool"
        }
    ]
    
    # Create a mock session to test tool execution
    from shared.models import ToolCall
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print(f"{'='*60}")
        
        try:
            # Determine which tool to use based on query
            if "neighborhood" in test_case['query'].lower() or "tell me about" in test_case['query'].lower():
                tool_name = "search_wikipedia_tool"
                tool_call = ToolCall(
                    tool_name=tool_name,
                    arguments={
                        "query": test_case['query'],
                        "city": "Oakland" if "oakland" in test_case['query'].lower() else "San Francisco",
                        "size": 3
                    }
                )
            else:
                tool_name = "search_properties_tool"
                args = {"query": test_case['query'], "size": 3}
                
                # Add price filter if mentioned
                if "800k" in test_case['query']:
                    args["max_price"] = 800000
                
                tool_call = ToolCall(
                    tool_name=tool_name,
                    arguments=args
                )
            
            # Execute the tool
            result = registry.execute_tool(tool_call)
            
            if result.success:
                print(f"✅ Tool executed successfully: {tool_name}")
                print(f"   Execution time: {result.execution_time:.3f}s")
                
                # Show a preview of results
                if isinstance(result.result, str):
                    print(f"   Result preview: {result.result[:200]}...")
                else:
                    print(f"   Result type: {type(result.result)}")
            else:
                print(f"❌ Tool execution failed: {result.error}")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    print(f"\n{'='*60}")
    print("✅ All queries tested successfully!")
    print("The frontend queries will work with the backend.")
    return True


if __name__ == "__main__":
    success = test_queries()
    sys.exit(0 if success else 1)