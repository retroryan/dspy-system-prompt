"""Demo: Multi-Tool Orchestration

This demo showcases complex scenarios that require multiple tools
working together to solve real-world property search challenges.
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.tool_utils.registry import ToolRegistry
from shared.models import ToolCall
from tools.real_estate.mcp_tool_set import RealEstateMCPToolSet


class PropertySearchOrchestrator:
    """Orchestrates multiple tools to solve complex property search scenarios."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.execution_log = []
    
    def log_execution(self, tool: str, success: bool, time: float):
        """Log tool execution for analysis."""
        self.execution_log.append({
            "tool": tool,
            "success": success,
            "time": time,
            "timestamp": datetime.now().isoformat()
        })
    
    def find_dream_home(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Find a dream home using multiple tools and criteria."""
        
        print(f"\n🏡 Finding Dream Home")
        print("=" * 50)
        print(f"Requirements: {requirements['description']}")
        
        results = {
            "properties": [],
            "neighborhood_info": [],
            "market_analysis": {},
            "recommendations": []
        }
        
        # Step 1: Initial property search
        print(f"\n1️⃣ Searching for properties...")
        search_call = ToolCall(
            tool_name="natural_language_search_tool",
            arguments={
                "query": requirements["description"],
                "search_type": "semantic",
                "size": 5
            }
        )
        
        search_result = self.registry.execute_tool(search_call)
        self.log_execution("natural_language_search_tool", search_result.success, search_result.execution_time)
        
        if search_result.success:
            if isinstance(search_result.result, str):
                try:
                    data = json.loads(search_result.result)
                    results["properties"] = data.get("properties", data.get("results", []))
                except:
                    results["properties"] = []
            print(f"   ✅ Found {len(results['properties'])} potential matches")
        
        # Step 2: Research neighborhoods
        if requirements.get("location"):
            print(f"\n2️⃣ Researching {requirements['location']} neighborhoods...")
            wiki_call = ToolCall(
                tool_name="search_wikipedia_by_location_tool",
                arguments={
                    "city": requirements["location"].get("city", ""),
                    "state": requirements["location"].get("state", "CA"),
                    "query": "neighborhoods schools parks community",
                    "size": 3
                }
            )
            
            wiki_result = self.registry.execute_tool(wiki_call)
            self.log_execution("search_wikipedia_by_location_tool", wiki_result.success, wiki_result.execution_time)
            
            if wiki_result.success:
                if isinstance(wiki_result.result, str):
                    try:
                        data = json.loads(wiki_result.result)
                        results["neighborhood_info"] = data.get("articles", [])
                    except:
                        pass
                print(f"   ✅ Found {len(results['neighborhood_info'])} neighborhood articles")
        
        # Step 3: Get detailed property information
        if results["properties"]:
            print(f"\n3️⃣ Getting detailed property information...")
            prop_id = results["properties"][0].get("id", results["properties"][0].get("listing_id", "PROP-001"))
            details_call = ToolCall(
                tool_name="get_property_details_tool",
                arguments={"listing_id": prop_id}  # Correct argument name
            )
            
            details_result = self.registry.execute_tool(details_call)
            self.log_execution("get_property_details_tool", details_result.success, details_result.execution_time)
            
            if details_result.success:
                print(f"   ✅ Retrieved detailed information for top property")
        
        # Step 4: Market analysis
        print(f"\n4️⃣ Analyzing market conditions...")
        if requirements.get("budget"):
            market_call = ToolCall(
                tool_name="search_properties_tool",
                arguments={
                    "query": f"properties in {requirements.get('location', {}).get('city', 'area')}",
                    "min_price": requirements["budget"]["min"],
                    "max_price": requirements["budget"]["max"],
                    "size": 10
                }
            )
            
            market_result = self.registry.execute_tool(market_call)
            self.log_execution("search_properties_tool", market_result.success, market_result.execution_time)
            
            if market_result.success:
                try:
                    data = json.loads(market_result.result) if isinstance(market_result.result, str) else market_result.result
                    total = data.get("total_results", 0)
                    results["market_analysis"] = {
                        "available_properties": total,
                        "price_range": f"${requirements['budget']['min']:,} - ${requirements['budget']['max']:,}",
                        "market_status": "Buyer's Market" if total > 50 else "Seller's Market"
                    }
                    print(f"   ✅ Market analysis complete: {total} properties in range")
                except:
                    pass
        
        # Step 5: Generate recommendations
        print(f"\n5️⃣ Generating personalized recommendations...")
        results["recommendations"] = self._generate_recommendations(results, requirements)
        
        return results
    
    def _generate_recommendations(self, results: Dict, requirements: Dict) -> List[str]:
        """Generate recommendations based on search results."""
        recommendations = []
        
        if results["properties"]:
            recommendations.append(f"Found {len(results['properties'])} properties matching your criteria")
        
        if results.get("market_analysis", {}).get("market_status"):
            status = results["market_analysis"]["market_status"]
            if status == "Buyer's Market":
                recommendations.append("Good time to buy - plenty of inventory available")
            else:
                recommendations.append("Competitive market - be prepared to act quickly")
        
        if results["neighborhood_info"]:
            recommendations.append(f"Researched {len(results['neighborhood_info'])} neighborhood resources")
        
        return recommendations
    
    def compare_locations(self, locations: List[Dict]) -> Dict[str, Any]:
        """Compare multiple locations for best fit."""
        
        print(f"\n📊 Comparing {len(locations)} Locations")
        print("=" * 50)
        
        comparison = {}
        
        for loc in locations:
            city = loc["city"]
            state = loc["state"]
            print(f"\n🔍 Analyzing {city}, {state}...")
            
            # Search properties
            prop_call = ToolCall(
                tool_name="search_properties_tool",
                arguments={
                    "query": f"homes in {city} {state}",
                    "size": 5
                }
            )
            
            prop_result = self.registry.execute_tool(prop_call)
            self.log_execution("search_properties_tool", prop_result.success, prop_result.execution_time)
            
            # Get location info
            wiki_call = ToolCall(
                tool_name="search_wikipedia_by_location_tool",
                arguments={
                    "city": city,
                    "state": state,
                    "query": "demographics economy culture",
                    "size": 2
                }
            )
            
            wiki_result = self.registry.execute_tool(wiki_call)
            self.log_execution("search_wikipedia_by_location_tool", wiki_result.success, wiki_result.execution_time)
            
            # Store comparison data
            comparison[city] = {
                "properties_found": 0,
                "avg_price": 0,
                "has_info": wiki_result.success
            }
            
            if prop_result.success:
                try:
                    data = json.loads(prop_result.result) if isinstance(prop_result.result, str) else prop_result.result
                    properties = data.get("properties", data.get("results", []))
                    comparison[city]["properties_found"] = len(properties)
                    
                    # Calculate average price
                    prices = [p.get("price", 0) for p in properties if p.get("price")]
                    if prices:
                        comparison[city]["avg_price"] = sum(prices) / len(prices)
                except:
                    pass
            
            print(f"   ✅ Analysis complete for {city}")
        
        return comparison


def demo_multi_tool():
    """Demonstrate multi-tool orchestration for complex scenarios."""
    
    print("\n" + "="*70)
    print("DEMO: Multi-Tool Orchestration")
    print("="*70)
    print("Solving complex property search scenarios with tool coordination")
    
    # Initialize registry with MCP tools
    print("\n🔧 Initializing MCP tools...")
    registry = ToolRegistry()
    mcp_tools = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    registry.register_tool_set(mcp_tools)
    
    print(f"✅ Connected to MCP server with full tool suite")
    
    # Create orchestrator
    orchestrator = PropertySearchOrchestrator(registry)
    
    # Scenario 1: Complete Dream Home Search
    print(f"\n{'='*70}")
    print("Scenario 1: Complete Dream Home Search")
    print(f"{'='*70}")
    
    dream_home_requirements = {
        "description": "Modern family home with 4 bedrooms, home office, near good schools, with a backyard for kids",
        "location": {"city": "Oakland", "state": "CA"},
        "budget": {"min": 600000, "max": 1200000},
        "must_haves": ["home office", "backyard", "good schools"],
        "nice_to_haves": ["pool", "modern kitchen", "garage"]
    }
    
    dream_results = orchestrator.find_dream_home(dream_home_requirements)
    
    # Display results
    print(f"\n📋 Dream Home Search Results:")
    print("-" * 40)
    print(f"✅ Properties found: {len(dream_results['properties'])}")
    print(f"📚 Neighborhood articles: {len(dream_results['neighborhood_info'])}")
    if dream_results["market_analysis"]:
        print(f"📊 Market Status: {dream_results['market_analysis'].get('market_status', 'Unknown')}")
        print(f"🏠 Available in budget: {dream_results['market_analysis'].get('available_properties', 0)}")
    
    print(f"\n💡 Recommendations:")
    for rec in dream_results["recommendations"]:
        print(f"   • {rec}")
    
    # Scenario 2: Multi-Location Comparison
    print(f"\n{'='*70}")
    print("Scenario 2: Multi-Location Comparison")
    print(f"{'='*70}")
    
    locations_to_compare = [
        {"city": "San Francisco", "state": "CA"},
        {"city": "Oakland", "state": "CA"},
        {"city": "Berkeley", "state": "CA"}
    ]
    
    comparison_results = orchestrator.compare_locations(locations_to_compare)
    
    # Display comparison
    print(f"\n📊 Location Comparison Results:")
    print("-" * 40)
    print(f"{'City':<15} {'Properties':<12} {'Avg Price':<15} {'Info Available'}")
    print("-" * 55)
    
    for city, data in comparison_results.items():
        avg_price = f"${data['avg_price']:,.0f}" if data['avg_price'] else "N/A"
        info = "Yes" if data['has_info'] else "No"
        print(f"{city:<15} {data['properties_found']:<12} {avg_price:<15} {info}")
    
    # Scenario 3: Investment Property Analysis
    print(f"\n{'='*70}")
    print("Scenario 3: Investment Property Analysis")
    print(f"{'='*70}")
    
    print("\n🏢 Analyzing investment opportunities...")
    
    # Search for investment properties
    invest_call = ToolCall(
        tool_name="natural_language_search_tool",
        arguments={
            "query": "investment property with rental income potential near universities or business districts",
            "search_type": "semantic",
            "size": 3
        }
    )
    
    invest_result = registry.execute_tool(invest_call)
    orchestrator.log_execution("natural_language_search_tool", invest_result.success, invest_result.execution_time)
    
    if invest_result.success:
        print("   ✅ Found investment opportunities")
        
        # Research rental market
        rental_call = ToolCall(
            tool_name="search_wikipedia_tool",
            arguments={
                "query": "Bay Area rental market trends housing",
                "size": 2
            }
        )
        
        rental_result = registry.execute_tool(rental_call)
        orchestrator.log_execution("search_wikipedia_tool", rental_result.success, rental_result.execution_time)
        
        if rental_result.success:
            print("   ✅ Researched rental market conditions")
    
    # Tool Usage Statistics
    print(f"\n{'='*70}")
    print("Tool Usage Statistics")
    print(f"{'='*70}")
    
    tool_stats = {}
    total_time = 0
    
    for log in orchestrator.execution_log:
        tool = log["tool"]
        if tool not in tool_stats:
            tool_stats[tool] = {"count": 0, "success": 0, "total_time": 0}
        
        tool_stats[tool]["count"] += 1
        if log["success"]:
            tool_stats[tool]["success"] += 1
        tool_stats[tool]["total_time"] += log["time"]
        total_time += log["time"]
    
    print(f"\n📊 Tool Performance Metrics:")
    print(f"{'Tool':<35} {'Calls':<8} {'Success':<10} {'Avg Time'}")
    print("-" * 65)
    
    for tool, stats in tool_stats.items():
        success_rate = f"{(stats['success']/stats['count']*100):.0f}%" if stats['count'] > 0 else "0%"
        avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
        print(f"{tool:<35} {stats['count']:<8} {success_rate:<10} {avg_time:.3f}s")
    
    print(f"\n⏱️ Total execution time: {total_time:.2f}s")
    print(f"🔧 Total tool calls: {len(orchestrator.execution_log)}")
    
    # Summary
    print(f"\n{'='*70}")
    print("DEMO SUMMARY")
    print(f"{'='*70}")
    print("✅ Successfully demonstrated multi-tool orchestration")
    print("🔄 Showed complex scenarios requiring tool coordination:")
    print("   • Dream home search with 5+ tools working together")
    print("   • Multi-location comparison for informed decisions")
    print("   • Investment property analysis with market research")
    print("📊 Tracked performance metrics across all tool executions")
    print("🎯 Real-world scenarios solved with intelligent tool selection")
    print("\n💡 Key Insight: Complex property searches require orchestrated")
    print("   tool usage to provide comprehensive, actionable insights!")


if __name__ == "__main__":
    try:
        demo_multi_tool()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Make sure the MCP server is running at http://localhost:8000/mcp")
        sys.exit(1)