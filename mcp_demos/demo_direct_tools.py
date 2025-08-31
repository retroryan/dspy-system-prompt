"""Demo: Direct MCP Tool Execution

This demo shows direct interaction with MCP tools through the registry,
demonstrating the clean integration without the agent layer.
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.tool_utils.registry import ToolRegistry
from shared.models import ToolCall
from tools.real_estate.mcp_tool_set import RealEstateMCPToolSet


def format_property(prop):
    """Format a property for display."""
    return (
        f"  📍 {prop.get('property_type', 'Unknown').title()} - ${prop.get('price', 0):,.0f}\n"
        f"     {prop.get('bedrooms', 0)} bed, {prop.get('bathrooms', 0)} bath, "
        f"{prop.get('square_feet', 0):,} sqft\n"
        f"     {prop.get('description', 'No description')[:80]}..."
    )


def demo_direct_tools():
    """Demonstrate direct MCP tool execution."""
    
    print("\n" + "="*70)
    print("DEMO: Direct MCP Tool Execution")
    print("="*70)
    print("This demo shows how MCP tools work at the registry level")
    
    # Initialize registry with MCP tools
    print("\n🔧 Initializing MCP tool registry...")
    registry = ToolRegistry()
    mcp_tools = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    registry.register_tool_set(mcp_tools)
    
    tools = registry.get_tool_names()
    print(f"✅ Registered {len(tools)} MCP tools:")
    for tool_name in tools:
        tool = registry.get_tool(tool_name)
        print(f"   - {tool_name}: {tool.description[:60]}...")
    
    # Demo 1: Property Search
    print(f"\n{'='*70}")
    print("Example 1: Searching for Properties")
    print(f"{'='*70}")
    
    search_call = ToolCall(
        tool_name="search_properties_tool",
        arguments={
            "query": "spacious home with modern kitchen and natural light",
            "min_price": 400000,
            "max_price": 900000,
            "size": 5
        }
    )
    
    print(f"🔍 Searching: '{search_call.arguments['query']}'")
    print(f"   Price range: ${search_call.arguments['min_price']:,} - ${search_call.arguments['max_price']:,}")
    
    result = registry.execute_tool(search_call)
    
    if result.success:
        data = json.loads(result.result) if isinstance(result.result, str) else result.result
        print(f"\n✅ Found {data.get('total_results', 0)} properties (showing {data.get('returned_results', 0)}):")
        
        for prop in data.get('properties', [])[:3]:
            print(f"\n{format_property(prop)}")
    else:
        print(f"❌ Search failed: {result.error}")
    
    # Demo 2: Neighborhood Research
    print(f"\n{'='*70}")
    print("Example 2: Researching Neighborhoods")
    print(f"{'='*70}")
    
    wiki_call = ToolCall(
        tool_name="search_wikipedia_by_location_tool",
        arguments={
            "city": "San Francisco",
            "state": "CA",
            "query": "neighborhoods culture history",
            "size": 3
        }
    )
    
    print(f"🌆 Researching: {wiki_call.arguments['city']}, {wiki_call.arguments['state']}")
    
    result = registry.execute_tool(wiki_call)
    
    if result.success:
        data = json.loads(result.result) if isinstance(result.result, str) else result.result
        articles = data.get('articles', [])
        
        print(f"\n✅ Found {len(articles)} relevant articles:")
        for article in articles[:3]:
            print(f"\n  📚 {article.get('title', 'Unknown')}")
            summary = article.get('summary', 'No summary')
            print(f"     {summary[:150]}...")
    else:
        print(f"❌ Research failed: {result.error}")
    
    # Demo 3: Natural Language Search
    print(f"\n{'='*70}")
    print("Example 3: AI-Powered Natural Language Search")
    print(f"{'='*70}")
    
    nl_call = ToolCall(
        tool_name="natural_language_search_tool",
        arguments={
            "query": "cozy cottage with character near parks and cafes perfect for young couple",
            "search_type": "semantic",
            "size": 3
        }
    )
    
    print(f"🤖 Natural language query: '{nl_call.arguments['query']}'")
    print(f"   Using {nl_call.arguments['search_type']} search with AI embeddings")
    
    result = registry.execute_tool(nl_call)
    
    if result.success:
        # Parse result - it might be a string or dict
        if isinstance(result.result, str):
            # Try to extract meaningful content
            print(f"\n✅ AI Search Results:")
            print(result.result[:500] + "...")
        else:
            print(f"\n✅ AI found relevant matches based on semantic understanding")
    else:
        print(f"❌ Natural language search failed: {result.error}")
    
    # Demo 4: System Health Check
    print(f"\n{'='*70}")
    print("Example 4: System Health Check")
    print(f"{'='*70}")
    
    health_call = ToolCall(
        tool_name="health_check_tool",
        arguments={}
    )
    
    print("🏥 Checking system health...")
    
    result = registry.execute_tool(health_call)
    
    if result.success:
        data = json.loads(result.result) if isinstance(result.result, str) else result.result
        print(f"\n✅ System Status: {data.get('status', 'unknown').upper()}")
        
        services = data.get('services', {})
        for service_name, service_info in services.items():
            status = service_info.get('status', 'unknown')
            emoji = "✅" if status == "healthy" else "⚠️"
            print(f"   {emoji} {service_name}: {service_info.get('message', 'No message')}")
    else:
        print(f"❌ Health check failed: {result.error}")
    
    # Summary
    print(f"\n{'='*70}")
    print("DEMO SUMMARY")
    print(f"{'='*70}")
    print("✅ Successfully demonstrated direct MCP tool execution")
    print("🔧 Tools are registered and accessible through the standard registry")
    print("📊 Each tool returns structured data that can be processed")
    print("🚀 No DSPy dependency - using clean, modular architecture")


if __name__ == "__main__":
    try:
        demo_direct_tools()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Make sure the MCP server is running at http://localhost:8000/mcp")
        sys.exit(1)