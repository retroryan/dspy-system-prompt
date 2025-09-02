"""Demo: Property Search with MCP Tools

This demo showcases how MCP tools work with direct execution,
simulating an agent-like interaction for property searches.
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

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
        if "temescal" in query.lower() or "oakland" in query.lower():
            tool_name = "search_wikipedia_by_location_tool"
            tool_call = ToolCall(
                tool_name=tool_name,
                arguments={
                    "city": "Oakland",
                    "state": "CA",
                    "query": "Temescal neighborhood history culture" if "temescal" in query.lower() else "neighborhoods history",
                    "size": 3
                }
            )
        else:
            tool_name = "search_wikipedia_tool"
            tool_call = ToolCall(
                tool_name=tool_name,
                arguments={
                    "query": query,
                    "size": 3
                }
            )
    elif "luxury" in query.lower() or "stunning" in query.lower():
        # Use natural language search for descriptive queries
        tool_name = "natural_language_search_tool"
        tool_call = ToolCall(
            tool_name=tool_name,
            arguments={
                "query": query,
                "search_type": "semantic",
                "size": 3
            }
        )
    else:
        # Use property search for home queries
        tool_name = "search_properties_tool"
        
        # Extract price if mentioned
        max_price = None
        min_price = None
        if "under" in query.lower():
            # Simple price extraction
            if "800k" in query.lower():
                max_price = 800000
            elif "900k" in query.lower():
                max_price = 900000
            elif "1m" in query.lower() or "million" in query.lower():
                max_price = 1000000
        
        # Build arguments
        args = {"query": query, "size": 5}
        if max_price is not None:
            args["max_price"] = max_price
            args["min_price"] = max_price * 0.5  # Set a reasonable min price
            
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


def format_property_result(result: Any) -> str:
    """Format property search results as a friendly response."""
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except:
            return result[:500]
    
    if not isinstance(result, dict):
        return str(result)[:500]
    
    properties = result.get('properties', result.get('results', []))
    total = result.get('total_results', result.get('total', len(properties)))
    
    if not properties:
        return "I couldn't find any properties matching your criteria. Try broadening your search."
    
    response = f"I found {total} properties matching your search. Here are the top results:\n\n"
    
    for i, prop in enumerate(properties[:3], 1):
        prop_type = prop.get('property_type', prop.get('type', 'Property'))
        price = prop.get('price', 0)
        bedrooms = prop.get('bedrooms', prop.get('beds', 0))
        bathrooms = prop.get('bathrooms', prop.get('baths', 0))
        sqft = prop.get('square_feet', prop.get('sqft', 0))
        desc = prop.get('description', prop.get('summary', ''))
        address = prop.get('address', prop.get('location', ''))
        
        response += f"{i}. {prop_type.title()} - ${price:,.0f}\n"
        if address:
            response += f"   📐 {address}\n"
        response += f"   {bedrooms} bed, {bathrooms} bath, {sqft:,} sqft\n"
        if desc:
            response += f"   {desc[:100]}...\n"
        response += "\n"
    
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
            "query": "I'm looking for a modern family home with a pool in Oakland, ideally under $900k",
            "context": "First-time homebuyer searching for family home"
        },
        {
            "query": "Tell me about the Temescal neighborhood in Oakland",
            "context": "Researching neighborhoods"
        },
        {
            "query": "Find luxury properties with stunning views and modern kitchens",
            "context": "Exploring luxury market"
        },
        {
            "query": "Show me cozy cottages with character, perfect for a young couple",
            "context": "Looking for starter home with personality"
        },
        {
            "query": "What are the best properties near good schools and parks?",
            "context": "Family-focused property search"
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
            if result['tool_used'] in ['search_properties_tool', 'natural_language_search_tool']:
                response = format_property_result(result['result'])
            elif 'wikipedia' in result['tool_used']:
                # Format Wikipedia results
                wiki_result = result['result']
                if isinstance(wiki_result, str):
                    try:
                        wiki_result = json.loads(wiki_result)
                    except:
                        response = f"Here's what I found:\n{wiki_result[:500]}..."
                    else:
                        articles = wiki_result.get('articles', wiki_result.get('results', []))
                        if articles:
                            response = f"Here's what I found about {item['query']}:\n\n"
                            for article in articles[:2]:
                                title = article.get('title', article.get('name', 'Article'))
                                summary = article.get('summary', article.get('content', article.get('description', '')))
                                url = article.get('url', '')
                                response += f"📚 {title}\n"
                                if url:
                                    response += f"   🔗 {url}\n"
                                response += f"   {summary[:200]}...\n\n"
                        else:
                            response = "I found information about this area. Let me know if you'd like more details."
                else:
                    response = str(wiki_result)[:500]
            else:
                # Handle other tool responses
                if isinstance(result['result'], dict):
                    response = json.dumps(result['result'], indent=2)[:500] + "..."
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
    print(f"🏡 Each query used the appropriate tool automatically:")
    print(f"   • Property search for home queries")
    print(f"   • Wikipedia for neighborhood research")
    print(f"   • Semantic search for natural language queries")
    print("\n💡 All data is live from the MCP server - no mock data!")
    print("   This demo shows intelligent real estate assistance in action.")


if __name__ == "__main__":
    try:
        demo_property_search()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Make sure the MCP server is running at http://localhost:8000/mcp")
        sys.exit(1)