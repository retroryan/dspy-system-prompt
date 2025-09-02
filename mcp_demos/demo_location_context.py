"""Demo: Location-Based Discovery and Context

This demo showcases location-aware tool usage, combining property search
with Wikipedia knowledge to provide rich contextual information.
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.tool_utils.registry import ToolRegistry
from shared.models import ToolCall
from tools.real_estate.mcp_tool_set import RealEstateMCPToolSet


def explore_location(registry: ToolRegistry, city: str, state: str) -> Dict[str, Any]:
    """Explore a location using multiple tools for comprehensive information."""
    
    results = {
        "city": city,
        "state": state,
        "wikipedia_info": None,
        "properties": None,
        "neighborhood_insights": None
    }
    
    print(f"\n🌍 Exploring {city}, {state}")
    print("=" * 50)
    
    # Step 1: Get Wikipedia information about the location
    print(f"\n📚 Researching {city} history and culture...")
    wiki_call = ToolCall(
        tool_name="search_wikipedia_by_location_tool",
        arguments={
            "city": city,
            "state": state,
            "query": "history culture neighborhoods attractions economy",
            "size": 5
        }
    )
    
    wiki_result = registry.execute_tool(wiki_call)
    if wiki_result.success:
        if isinstance(wiki_result.result, str):
            try:
                results["wikipedia_info"] = json.loads(wiki_result.result)
            except:
                results["wikipedia_info"] = {"raw": wiki_result.result}
        else:
            results["wikipedia_info"] = wiki_result.result
        print(f"   ✅ Found Wikipedia articles")
    else:
        print(f"   ⚠️ Could not fetch Wikipedia info: {wiki_result.error}")
    
    # Step 2: Search for properties in the area
    print(f"\n🏠 Searching for properties in {city}...")
    property_call = ToolCall(
        tool_name="search_properties_tool",
        arguments={
            "query": f"homes in {city} {state}",
            "size": 5
        }
    )
    
    property_result = registry.execute_tool(property_call)
    if property_result.success:
        if isinstance(property_result.result, str):
            try:
                results["properties"] = json.loads(property_result.result)
            except:
                results["properties"] = {"raw": property_result.result}
        else:
            results["properties"] = property_result.result
        
        # Count properties
        prop_count = 0
        if isinstance(results["properties"], dict):
            prop_count = results["properties"].get("total_results", 
                        len(results["properties"].get("properties", [])))
        print(f"   ✅ Found {prop_count} properties")
    else:
        print(f"   ⚠️ Could not fetch properties: {property_result.error}")
    
    # Step 3: Get neighborhood-specific insights
    print(f"\n🏘️ Gathering neighborhood insights...")
    neighborhood_call = ToolCall(
        tool_name="natural_language_search_tool",
        arguments={
            "query": f"family-friendly neighborhoods in {city} with good schools parks and community",
            "search_type": "semantic",
            "size": 3
        }
    )
    
    neighborhood_result = registry.execute_tool(neighborhood_call)
    if neighborhood_result.success:
        if isinstance(neighborhood_result.result, str):
            try:
                results["neighborhood_insights"] = json.loads(neighborhood_result.result)
            except:
                results["neighborhood_insights"] = {"raw": neighborhood_result.result}
        else:
            results["neighborhood_insights"] = neighborhood_result.result
        print(f"   ✅ Generated neighborhood insights")
    else:
        print(f"   ⚠️ Could not get insights: {neighborhood_result.error}")
    
    return results


def display_location_summary(location_data: Dict[str, Any]) -> None:
    """Display a comprehensive summary of location data."""
    
    city = location_data["city"]
    state = location_data["state"]
    
    print(f"\n{'='*70}")
    print(f"📍 LOCATION PROFILE: {city}, {state}")
    print(f"{'='*70}")
    
    # Wikipedia Information
    if location_data["wikipedia_info"]:
        print("\n📚 About the Area:")
        print("-" * 40)
        
        wiki = location_data["wikipedia_info"]
        if isinstance(wiki, dict) and "articles" in wiki:
            articles = wiki.get("articles", wiki.get("results", []))
            for article in articles[:3]:
                title = article.get("title", article.get("name", ""))
                summary = article.get("summary", article.get("content", ""))
                if title:
                    print(f"\n• {title}")
                    if summary:
                        print(f"  {summary[:150]}...")
        elif isinstance(wiki, dict) and "raw" in wiki:
            print(f"  {wiki['raw'][:300]}...")
    
    # Property Market Overview
    if location_data["properties"]:
        print("\n🏠 Real Estate Market:")
        print("-" * 40)
        
        props = location_data["properties"]
        if isinstance(props, dict):
            total = props.get("total_results", props.get("total", 0))
            properties = props.get("properties", props.get("results", []))
            
            if total:
                print(f"• {total} properties currently available")
            
            if properties:
                # Calculate price statistics
                prices = [p.get("price", 0) for p in properties if p.get("price")]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    min_price = min(prices)
                    max_price = max(prices)
                    
                    print(f"• Price range: ${min_price:,.0f} - ${max_price:,.0f}")
                    print(f"• Average price: ${avg_price:,.0f}")
                
                # Property type distribution
                types = {}
                for p in properties:
                    ptype = p.get("property_type", p.get("type", "Unknown"))
                    types[ptype] = types.get(ptype, 0) + 1
                
                if types:
                    print(f"• Property types available:")
                    for ptype, count in types.items():
                        print(f"  - {ptype}: {count}")
    
    # Neighborhood Insights
    if location_data["neighborhood_insights"]:
        print("\n🏘️ Neighborhood Insights:")
        print("-" * 40)
        
        insights = location_data["neighborhood_insights"]
        if isinstance(insights, dict):
            properties = insights.get("properties", insights.get("results", []))
            if properties:
                print(f"• Found {len(properties)} family-friendly options")
                for prop in properties[:2]:
                    desc = prop.get("description", prop.get("summary", ""))
                    if desc:
                        print(f"  - {desc[:100]}...")


def demo_location_context():
    """Demonstrate location-based discovery and contextual information."""
    
    print("\n" + "="*70)
    print("DEMO: Location-Based Discovery and Context")
    print("="*70)
    print("Combining multiple tools to provide rich location insights")
    
    # Initialize registry with MCP tools
    print("\n🔧 Initializing MCP tools...")
    registry = ToolRegistry()
    mcp_tools = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    registry.register_tool_set(mcp_tools)
    
    print(f"✅ Connected to MCP server with location-aware tools")
    
    # Locations to explore
    locations = [
        {"city": "San Francisco", "state": "CA", "focus": "Tech hub and cultural center"},
        {"city": "Oakland", "state": "CA", "focus": "Diverse neighborhoods and arts scene"},
        {"city": "Berkeley", "state": "CA", "focus": "University town and progressive community"},
        {"city": "San Jose", "state": "CA", "focus": "Silicon Valley and suburban living"},
        {"city": "Portland", "state": "OR", "focus": "Creative culture and outdoor access"},
        {"city": "Austin", "state": "TX", "focus": "Music scene and tech growth"}
    ]
    
    print(f"\n🗺️ Exploring {len(locations)} locations with contextual discovery...")
    
    # Explore each location
    for i, loc in enumerate(locations[:3], 1):  # Limit to 3 for demo
        print(f"\n{'='*70}")
        print(f"Location {i}: {loc['city']}, {loc['state']}")
        print(f"Focus: {loc['focus']}")
        print(f"{'='*70}")
        
        # Explore the location
        location_data = explore_location(registry, loc["city"], loc["state"])
        
        # Display comprehensive summary
        display_location_summary(location_data)
        
        print(f"\n⏱️ Analysis completed in {datetime.now().strftime('%H:%M:%S')}")
    
    # Cross-location comparison
    print(f"\n{'='*70}")
    print("BONUS: Cross-Location Comparison")
    print(f"{'='*70}")
    
    print("\n🔍 Comparing locations for 'best family neighborhoods'...")
    
    comparison_results = {}
    for loc in locations[:3]:
        print(f"\n• {loc['city']}, {loc['state']}:")
        
        compare_call = ToolCall(
            tool_name="natural_language_search_tool",
            arguments={
                "query": f"best family neighborhoods in {loc['city']} with excellent schools",
                "search_type": "semantic",
                "size": 2
            }
        )
        
        result = registry.execute_tool(compare_call)
        if result.success:
            comparison_results[loc['city']] = result.result
            print(f"  ✅ Analysis complete")
        else:
            print(f"  ⚠️ Could not analyze")
    
    # Summary
    print(f"\n{'='*70}")
    print("DEMO SUMMARY")
    print(f"{'='*70}")
    print("✅ Successfully demonstrated location-based discovery")
    print("🌍 Combined multiple data sources for comprehensive insights:")
    print("   • Wikipedia for history, culture, and general information")
    print("   • Property search for real estate market data")
    print("   • Semantic search for lifestyle and neighborhood insights")
    print("📊 Created rich location profiles with contextual information")
    print("🔄 Showed how multiple tools work together for better results")
    print("\n💡 Key Insight: Location context enhances property search by providing")
    print("   buyers with complete neighborhood and community understanding!")


if __name__ == "__main__":
    try:
        demo_location_context()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Make sure the MCP server is running at http://localhost:8000/mcp")
        sys.exit(1)