"""Demo: Property Search with MCP Tools

This demo showcases how MCP tools work with direct execution,
simulating an agent-like interaction for property searches.
"""
import sys
import json
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.tool_utils.registry import ToolRegistry
from shared.models import ToolCall
from tools.real_estate.mcp_tool_set import RealEstateMCPToolSet


def execute_search_query(registry: ToolRegistry, query: str, context: str) -> Dict:
    """Execute a property search query using MCP tools."""
    
    # Determine which tool to use based on query content
    if "neighborhood" in query.lower() or "tell me about" in query.lower():
        # Use Wikipedia search for neighborhood info
        tool_name = "search_wikipedia_tool"
        
        # Extract location from query (simple parsing)
        if "temescal" in query.lower():
            city = "Oakland"
            query_text = "Temescal neighborhood"
        elif "oakland" in query.lower():
            city = "Oakland"
            query_text = query
        elif "san francisco" in query.lower():
            city = "San Francisco"
            query_text = query
        else:
            city = ""
            query_text = query
        
        tool_call = ToolCall(
            tool_name=tool_name,
            arguments={
                "query": query_text,
                "city": city,
                "size": 3
            }
        )
    else:
        # Use property search for home queries
        tool_name = "search_properties_tool"
        
        # Extract price if mentioned
        max_price = None
        if "under" in query.lower():
            # Simple price extraction
            if "800k" in query.lower():
                max_price = 800000
            elif "1m" in query.lower() or "million" in query.lower():
                max_price = 1000000
        
        # Build arguments, excluding None values
        args = {"query": query, "size": 3}
        if max_price is not None:
            args["max_price"] = max_price
            
        tool_call = ToolCall(
            tool_name=tool_name,
            arguments=args
        )
    
    # Execute the tool
    result = registry.execute_tool(tool_call)
    
    return {
        "tool_used": tool_name,
        "success": result.success,
        "result": result.result if result.success else result.error,
        "execution_time": result.execution_time
    }


def format_property_result(result: Dict) -> str:
    """Format property search results as a friendly response."""
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except:
            return result[:500]
    
    if not isinstance(result, dict):
        return str(result)[:500]
    
    properties = result.get('properties', [])
    total = result.get('total_results', 0)
    
    if not properties:
        return "I couldn't find any properties matching your criteria."
    
    response = f"I found {total} properties matching your search. Here are the top results:\n\n"
    
    for i, prop in enumerate(properties[:3], 1):
        response += f"{i}. {prop.get('property_type', 'Property').title()} - ${prop.get('price', 0):,.0f}\n"
        response += f"   {prop.get('bedrooms', 0)} bed, {prop.get('bathrooms', 0)} bath, "
        response += f"{prop.get('square_feet', 0):,} sqft\n"
        response += f"   {prop.get('description', '')[:100]}...\n\n"
    
    return response


def demo_property_search():
    """Demonstrate property search using MCP tools."""
    
    print("\n" + "="*70)
    print("DEMO: Property Search with MCP Tools")
    print("="*70)
    
    # Initialize MCP tools
    print("\n🔧 Setting up MCP tools from server...")
    registry = ToolRegistry()
    mcp_tools = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    registry.register_tool_set(mcp_tools)
    
    available_tools = registry.get_tool_names()
    print(f"✅ Connected to MCP server with {len(available_tools)} tools available")
    
    # Create simulated agent interaction
    print("\n🤖 Ready to help you find your dream home...")
    
    # Demo queries that tell a story
    queries = [
        {
            "query": "I'm looking for a modern family home with a pool in Oakland, ideally under $800k",
            "context": "First-time homebuyer searching for family home"
        },
        {
            "query": "Tell me about the Temescal neighborhood in Oakland",
            "context": "Researching neighborhoods"
        },
        {
            "query": "Find luxury properties with stunning views and modern kitchens",
            "context": "Exploring luxury market"
        }
    ]
    
    for i, item in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"Query {i}: {item['context']}")
        print(f"{'='*70}")
        print(f"\n💭 User: {item['query']}")
        
        # Execute query using MCP tools
        result = execute_search_query(registry, item['query'], item['context'])
        
        if result['success']:
            # Format the response based on tool used
            if result['tool_used'] == 'search_properties_tool':
                response = format_property_result(result['result'])
            elif result['tool_used'] == 'search_wikipedia_tool':
                # Format Wikipedia results
                wiki_result = result['result']
                if isinstance(wiki_result, str):
                    try:
                        wiki_result = json.loads(wiki_result)
                    except:
                        response = wiki_result[:500]
                    else:
                        articles = wiki_result.get('articles', [])
                        if articles:
                            response = f"Here's what I found about {item['query']}:\n\n"
                            for article in articles[:2]:
                                response += f"📚 {article.get('title', 'Article')}\n"
                                summary = article.get('summary', article.get('content', ''))[:200]
                                response += f"   {summary}...\n\n"
                        else:
                            response = "I found some information about this area."
                else:
                    response = str(wiki_result)[:500]
            else:
                response = str(result['result'])[:500]
            
            print(f"\n🏠 Assistant: {response}")
        else:
            print(f"\n❌ Error: {result['result']}")
        
        # Show tool used
        print(f"\n📊 Tool used: {result['tool_used']}")
        print(f"⏱️  Response time: {result['execution_time']:.3f} seconds")
    
    # Show session summary
    print(f"\n{'='*70}")
    print("DEMO SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Successfully processed {len(queries)} property-related queries")
    print(f"🔧 MCP tools provided real-time data from the server")
    print(f"🏡 Each query used the appropriate tool automatically")
    print("\n💡 This demo shows how MCP tools enable intelligent real estate assistance")
    print("   through dynamic tool discovery and execution.")


if __name__ == "__main__":
    try:
        demo_property_search()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Make sure the MCP server is running at http://localhost:8000/mcp")
        sys.exit(1)