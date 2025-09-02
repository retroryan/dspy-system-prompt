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
    # Handle different response formats from the server
    if isinstance(prop, dict):
        prop_id = prop.get('id', prop.get('property_id', 'N/A'))
        price = prop.get('price', 0)
        bedrooms = prop.get('bedrooms', prop.get('beds', 0))
        bathrooms = prop.get('bathrooms', prop.get('baths', 0))
        sqft = prop.get('square_feet', prop.get('sqft', 0))
        desc = prop.get('description', prop.get('summary', 'No description available'))
        prop_type = prop.get('property_type', prop.get('type', 'Property'))
        address = prop.get('address', prop.get('location', ''))
        
        result = f"  🏠 {prop_type.title()} - ${price:,.0f}\n"
        if address:
            result += f"     📐 {address}\n"
        result += f"     {bedrooms} bed, {bathrooms} bath, {sqft:,} sqft\n"
        result += f"     {desc[:100]}..."
        return result
    else:
        return f"  Property: {str(prop)[:150]}..."


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
        # Parse the result - might be string or dict
        if isinstance(result.result, str):
            try:
                data = json.loads(result.result)
            except:
                # If not JSON, display as is
                print(f"\n✅ Search Results:\n{result.result[:500]}...")
                data = None
        else:
            data = result.result
        
        if data and isinstance(data, dict):
            total = data.get('total_results', data.get('total', 0))
            returned = data.get('returned_results', data.get('count', 0))
            properties = data.get('properties', data.get('results', []))
            
            print(f"\n✅ Found {total} properties (showing {returned or len(properties)}):")
            
            for i, prop in enumerate(properties[:3], 1):
                print(f"\n{format_property(prop)}")
        print(f"\n   ⏱ Execution time: {result.execution_time:.3f}s")
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
    print(f"   Query: {wiki_call.arguments['query']}")
    
    result = registry.execute_tool(wiki_call)
    
    if result.success:
        # Parse result
        if isinstance(result.result, str):
            try:
                data = json.loads(result.result)
            except:
                print(f"\n✅ Research Results:\n{result.result[:500]}...")
                data = None
        else:
            data = result.result
        
        if data and isinstance(data, dict):
            articles = data.get('articles', data.get('results', []))
            
            if articles:
                print(f"\n✅ Found {len(articles)} relevant articles:")
                for article in articles[:3]:
                    title = article.get('title', article.get('name', 'Unknown'))
                    summary = article.get('summary', article.get('content', article.get('description', 'No summary')))
                    url = article.get('url', '')
                    
                    print(f"\n  📚 {title}")
                    if url:
                        print(f"     🔗 {url}")
                    print(f"     {summary[:150]}...")
            else:
                print(f"\nℹ️ No articles found for this location")
        print(f"\n   ⏱ Execution time: {result.execution_time:.3f}s")
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
        # Parse result
        if isinstance(result.result, str):
            try:
                data = json.loads(result.result)
                if isinstance(data, dict):
                    # Check for properties in response
                    properties = data.get('properties', data.get('results', []))
                    if properties:
                        print(f"\n✅ AI found {len(properties)} semantically matching properties:")
                        for prop in properties[:3]:
                            print(f"\n{format_property(prop)}")
                            # Show relevance score if available
                            score = prop.get('relevance_score', prop.get('score'))
                            if score:
                                print(f"     🎯 Relevance: {score:.2f}")
                    else:
                        # Show raw result if no properties
                        print(f"\n✅ AI Search Results:")
                        print(json.dumps(data, indent=2)[:500] + "...")
                else:
                    print(f"\n✅ AI Search Results:")
                    print(result.result[:500] + "...")
            except:
                # If not JSON, display as is
                print(f"\n✅ AI Search Results:")
                print(result.result[:500] + "...")
        else:
            print(f"\n✅ AI found relevant matches based on semantic understanding")
            if isinstance(result.result, dict):
                print(json.dumps(result.result, indent=2)[:500] + "...")
        print(f"\n   ⏱ Execution time: {result.execution_time:.3f}s")
    else:
        print(f"❌ Natural language search failed: {result.error}")
    
    # Demo 4: Property Details
    print(f"\n{'='*70}")
    print("Example 4: Get Property Details")
    print(f"{'='*70}")
    
    details_call = ToolCall(
        tool_name="get_property_details_tool",
        arguments={
            "listing_id": "PROP-001"  # Correct argument name
        }
    )
    
    print(f"🏠 Getting details for property: {details_call.arguments['property_id']}")
    
    result = registry.execute_tool(details_call)
    
    if result.success:
        # Parse result
        if isinstance(result.result, str):
            try:
                data = json.loads(result.result)
            except:
                print(f"\n✅ Property Details:\n{result.result[:500]}...")
                data = None
        else:
            data = result.result
        
        if data and isinstance(data, dict):
            # Display property details
            print(f"\n✅ Property Details:")
            print(f"   ID: {data.get('id', data.get('property_id', 'N/A'))}")
            print(f"   Type: {data.get('property_type', data.get('type', 'N/A'))}")
            print(f"   Price: ${data.get('price', 0):,.0f}")
            print(f"   Bedrooms: {data.get('bedrooms', data.get('beds', 0))}")
            print(f"   Bathrooms: {data.get('bathrooms', data.get('baths', 0))}")
            print(f"   Square Feet: {data.get('square_feet', data.get('sqft', 0)):,}")
            
            # Show address if available
            address = data.get('address', data.get('location'))
            if address:
                print(f"   Address: {address}")
            
            # Show description
            desc = data.get('description', data.get('summary', ''))
            if desc:
                print(f"\n   Description:\n   {desc[:200]}...")
            
            # Show amenities if available
            amenities = data.get('amenities', data.get('features', []))
            if amenities:
                print(f"\n   Amenities:")
                for amenity in amenities[:5]:
                    print(f"   • {amenity}")
        print(f"\n   ⏱ Execution time: {result.execution_time:.3f}s")
    else:
        print(f"❌ Failed to get property details: {result.error}")
    
    # Demo 5: System Health Check
    print(f"\n{'='*70}")
    print("Example 5: System Health Check")
    print(f"{'='*70}")
    
    health_call = ToolCall(
        tool_name="health_check_tool",
        arguments={}
    )
    
    print("🏥 Checking system health...")
    
    result = registry.execute_tool(health_call)
    
    if result.success:
        if isinstance(result.result, str):
            try:
                data = json.loads(result.result)
            except:
                print(f"\n✅ Health Status:\n{result.result[:200]}")
                data = None
        else:
            data = result.result
        
        if data and isinstance(data, dict):
            print(f"\n✅ System Status: {data.get('status', 'unknown').upper()}")
            
            services = data.get('services', {})
            if services:
                print("\n   Service Status:")
                for service_name, service_info in services.items():
                    status = service_info.get('status', 'unknown')
                    emoji = "✅" if status == "healthy" else "⚠️"
                    print(f"   {emoji} {service_name}: {service_info.get('message', 'No message')}")
            
            # Show timestamp if available
            timestamp = data.get('timestamp', data.get('checked_at'))
            if timestamp:
                print(f"\n   Last checked: {timestamp}")
        print(f"\n   ⏱ Execution time: {result.execution_time:.3f}s")
    else:
        print(f"❌ Health check failed: {result.error}")
    
    # Summary
    print(f"\n{'='*70}")
    print("DEMO SUMMARY")
    print(f"{'='*70}")
    print("✅ Successfully demonstrated direct MCP tool execution")
    print("🔧 Tools are registered and accessible through the standard registry")
    print("📊 Each tool returns real data from the MCP server")
    print("🎯 Semantic search uses AI to understand natural language queries")
    print("🚀 No DSPy dependency - using clean, modular architecture")
    print("\n💡 All results are live from the MCP server - no mock data!")


if __name__ == "__main__":
    try:
        demo_direct_tools()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Make sure the MCP server is running at http://localhost:8000/mcp")
        sys.exit(1)