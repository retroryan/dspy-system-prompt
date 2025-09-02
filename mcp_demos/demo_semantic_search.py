"""Demo: AI-Powered Semantic Property Search

This demo showcases the natural language understanding capabilities
of MCP tools using semantic search for intelligent property matching.
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


def display_semantic_results(results: Any, query: str) -> None:
    """Display semantic search results with relevance scores."""
    print(f"\n🤖 AI Understanding: '{query}'")
    print("-" * 40)
    
    if isinstance(results, str):
        try:
            data = json.loads(results)
        except:
            print(f"Raw results: {results[:500]}...")
            return
    else:
        data = results
    
    if isinstance(data, dict):
        properties = data.get('properties', data.get('results', []))
        
        if properties:
            print(f"✅ Found {len(properties)} semantically matching properties:\n")
            
            for i, prop in enumerate(properties, 1):
                # Extract property details
                prop_type = prop.get('property_type', prop.get('type', 'Property'))
                price = prop.get('price', 0)
                bedrooms = prop.get('bedrooms', prop.get('beds', 0))
                bathrooms = prop.get('bathrooms', prop.get('baths', 0))
                sqft = prop.get('square_feet', prop.get('sqft', 0))
                desc = prop.get('description', prop.get('summary', ''))
                address = prop.get('address', prop.get('location', ''))
                score = prop.get('relevance_score', prop.get('score', prop.get('similarity', 0)))
                
                print(f"{i}. 🏠 {prop_type.title()} - ${price:,.0f}")
                if address:
                    print(f"   📍 {address}")
                print(f"   {bedrooms} bed, {bathrooms} bath, {sqft:,} sqft")
                
                # Show relevance/match score if available
                if score:
                    bars = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                    print(f"   🎯 Match Score: [{bars}] {score:.2%}")
                
                if desc:
                    print(f"   📝 {desc[:120]}...")
                print()
        else:
            # No properties found, show raw data
            print("No specific properties found. Raw response:")
            print(json.dumps(data, indent=2)[:500] + "...")
    else:
        print(f"Results: {str(data)[:500]}...")


def demo_semantic_search():
    """Demonstrate AI-powered semantic property search."""
    
    print("\n" + "="*70)
    print("DEMO: AI-Powered Semantic Property Search")
    print("="*70)
    print("Using natural language understanding to find perfect matches")
    
    # Initialize registry with MCP tools
    print("\n🔧 Initializing MCP tools...")
    registry = ToolRegistry()
    mcp_tools = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    registry.register_tool_set(mcp_tools)
    
    print(f"✅ Connected to MCP server with semantic search capabilities")
    
    # Semantic search queries that test understanding
    semantic_queries = [
        {
            "query": "I want a peaceful retreat with nature views where I can work from home and enjoy morning coffee on a deck",
            "description": "Finding homes that match lifestyle preferences"
        },
        {
            "query": "Something perfect for entertaining friends with an open floor plan and outdoor space for BBQs",
            "description": "Social lifestyle and entertainment focus"
        },
        {
            "query": "A cozy nest for a young professional near transit and coffee shops with modern amenities",
            "description": "Urban convenience and modern living"
        },
        {
            "query": "Family-friendly home with safe neighborhood, good schools, and space for kids to play",
            "description": "Family needs and child-focused features"
        },
        {
            "query": "Investment property with good rental potential in an up-and-coming neighborhood",
            "description": "Investment focus and growth potential"
        },
        {
            "query": "Eco-friendly home with solar panels, energy efficiency, and sustainable features",
            "description": "Environmental consciousness and sustainability"
        },
        {
            "query": "Historic charm with original details but updated kitchen and bathrooms",
            "description": "Balance of character and modern updates"
        },
        {
            "query": "Minimalist space with clean lines, lots of natural light, and low maintenance",
            "description": "Aesthetic preferences and lifestyle simplicity"
        }
    ]
    
    print(f"\n🎯 Testing {len(semantic_queries)} semantic understanding scenarios...")
    print("="*70)
    
    for i, item in enumerate(semantic_queries, 1):
        print(f"\n{'='*70}")
        print(f"Scenario {i}: {item['description']}")
        print(f"{'='*70}")
        
        # Execute semantic search
        tool_call = ToolCall(
            tool_name="natural_language_search_tool",
            arguments={
                "query": item['query'],
                "search_type": "semantic",
                "size": 3
            }
        )
        
        print(f"\n💭 Natural Language Query:")
        print(f"   \"{item['query']}\"")
        
        result = registry.execute_tool(tool_call)
        
        if result.success:
            display_semantic_results(result.result, item['query'])
            print(f"⏱️ Search time: {result.execution_time:.3f}s")
        else:
            print(f"❌ Search failed: {result.error}")
    
    # Comparison: Semantic vs Keyword Search
    print(f"\n{'='*70}")
    print("BONUS: Semantic vs Keyword Search Comparison")
    print(f"{'='*70}")
    
    comparison_query = "charming vintage home with character"
    
    print(f"\n🔍 Query: '{comparison_query}'")
    print("-" * 40)
    
    # Keyword search
    print("\n📝 Traditional Keyword Search:")
    keyword_call = ToolCall(
        tool_name="search_properties_tool",
        arguments={
            "query": comparison_query,
            "size": 3
        }
    )
    
    keyword_result = registry.execute_tool(keyword_call)
    if keyword_result.success:
        print("   Uses exact term matching")
        print(f"   Results based on literal keywords: 'charming', 'vintage', 'character'")
        print(f"   ⏱️ Time: {keyword_result.execution_time:.3f}s")
    
    # Semantic search
    print("\n🤖 AI Semantic Search:")
    semantic_call = ToolCall(
        tool_name="natural_language_search_tool",
        arguments={
            "query": comparison_query,
            "search_type": "semantic",
            "size": 3
        }
    )
    
    semantic_result = registry.execute_tool(semantic_call)
    if semantic_result.success:
        print("   Understands intent and context")
        print("   Finds homes with historic features, unique architecture, original details")
        print("   May include: craftsman, tudor, victorian, mid-century modern")
        print(f"   ⏱️ Time: {semantic_result.execution_time:.3f}s")
    
    # Summary
    print(f"\n{'='*70}")
    print("DEMO SUMMARY")
    print(f"{'='*70}")
    print("✅ Demonstrated AI-powered semantic search capabilities")
    print("🤖 Natural language understanding interprets intent, not just keywords")
    print("🎯 Semantic matching finds properties based on lifestyle and preferences")
    print("📊 Relevance scoring ranks results by semantic similarity")
    print("🚀 All powered by real MCP server with AI embeddings")
    print("\n💡 Key Insight: Semantic search understands what buyers really want,")
    print("   not just what they literally say!")


if __name__ == "__main__":
    try:
        demo_semantic_search()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Make sure the MCP server is running at http://localhost:8000/mcp")
        sys.exit(1)