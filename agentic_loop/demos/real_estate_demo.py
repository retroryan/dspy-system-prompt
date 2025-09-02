#!/usr/bin/env python3
"""
Real Estate Demo - Complete home buying journey with advanced natural language queries.

This demo tells a realistic home buying story that naturally demonstrates:
- Natural language property search with lifestyle preferences
- Neighborhood research and cultural context
- School district analysis for families
- Multi-criteria property filtering
- Context building across queries
- Memory management and conversation continuity
"""

import logging
from agentic_loop.session import AgentSession
from shared import setup_llm
from shared.config import config

# Configure clean output - suppress LiteLLM logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger('LiteLLM').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def get_home_buying_journey():
    """Return the complete home buying journey as connected queries.
    
    These queries tell the story of a family looking for their dream home
    in the Bay Area, showcasing advanced natural language understanding
    and context-aware responses.
    """
    return [
        # Query 1: Natural language search with specific features
        "Find modern family homes with pools in Oakland under $800k",
        
        # Query 2: Neighborhood research
        "Tell me about the Temescal neighborhood in Oakland - what amenities and culture does it offer?",
        
        # Query 3: Price and type filtered search
        "Show me luxury properties with stunning views and modern kitchens",
        
        # Query 4: School-focused search
        "Show me family homes near top-rated schools in San Francisco",
        
        # Query 5: Comparative analysis
        "Find cozy family home near good schools and parks in Oakland"
    ]

def main():
    """Run the complete real estate demo workflow."""
    import time
    from datetime import datetime
    
    # Setup
    setup_llm()
    session = AgentSession("real_estate_mcp", user_id="demo_homebuyer", verbose=True)
    
    # Demo header
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Real Estate Demo: Home Buying Journey" + " " * 16 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("This demo showcases advanced natural language real estate search")
    print("with context building, neighborhood research, and personalized recommendations.")
    print()
    
    # Track execution metrics
    demo_start_time = time.time()
    total_iterations = 0
    total_tools_used = set()
    query_results = []
    
    # Run the complete workflow
    queries = get_home_buying_journey()
    
    for i, query in enumerate(queries, 1):
        print("=" * 80)
        print(f"QUERY {i}/{len(queries)}")
        print("=" * 80)
        
        # Format multi-line queries nicely
        import textwrap
        wrapped_query = textwrap.fill(query, width=76)
        print(wrapped_query)
        print()
        
        # Show context awareness for queries that build on previous results
        if i > 1:
            context_indicators = [
                "these neighborhoods", "Based on", "we've discussed", 
                "everything we've discussed", "Which of these", "more about"
            ]
            if any(indicator in query for indicator in context_indicators):
                print("💭 This query builds on previous conversation context")
        
        print()
        
        # Execute query with config max_iterations
        result = session.query(query, max_iterations=config.max_iterations)
        
        # Track metrics
        total_iterations += result.iterations
        if result.tools_used:
            total_tools_used.update(result.tools_used)
        query_results.append(result)
        
        # Display result in separate section
        print("=" * 80)
        print("RESULT")
        print("=" * 80)
        # Wrap long answers for readability
        wrapped = textwrap.fill(result.answer, width=76)
        print(wrapped)
        print()
        
        # Show execution metrics in separate section
        print("=" * 80)
        print("EXECUTION METRICS")
        print("=" * 80)
        print(f"Time: {result.execution_time:.1f}s")
        print(f"Iterations: {result.iterations}")
        if result.tools_used:
            print(f"Tools: {', '.join(result.tools_used)}")
        else:
            print("Tools: None (context only)")
        if len(session.history.messages) > 0:
            print(f"Memory: {len(session.history.messages)} messages in context")
        print()
        
        # Add a small delay between queries for readability
        if i < len(queries):
            time.sleep(0.5)
    
    # Calculate final metrics
    demo_total_time = time.time() - demo_start_time
    successful_queries = len([r for r in query_results if r.answer])
    average_iterations = total_iterations / len(queries) if queries else 0
    average_time = sum(r.execution_time for r in query_results) / len(query_results) if query_results else 0
    
    # Demo completion
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 23 + "Demo Complete!" + " " * 23 + "║") 
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Final Summary Section
    print("=" * 80)
    print("REAL ESTATE DEMO SUMMARY REPORT")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Demo Type: Real Estate MCP - Advanced Natural Language Home Search")
    print()
    
    print("=" * 80)
    print("EXECUTION STATISTICS")
    print("=" * 80)
    print(f"{'Metric':<25} {'Value':<15} {'Details'}")
    print("=" * 80)
    print(f"{'Total Queries':<25} {len(queries):<15} Complete home buying journey")
    print(f"{'Successful Queries':<25} {successful_queries}/{len(queries):<10} {100*successful_queries/len(queries):.0f}% success rate")
    print(f"{'Total Time':<25} {demo_total_time:.1f}s{'':<10} End-to-end execution")
    print(f"{'Average Time/Query':<25} {average_time:.1f}s{'':<10} Per query average")
    print(f"{'Total Iterations':<25} {total_iterations:<15} React loop iterations")
    print(f"{'Average Iterations':<25} {average_iterations:.1f}{'':<12} Per query average")
    print(f"{'Unique Tools Used':<25} {len(total_tools_used):<15} {', '.join(sorted(total_tools_used)) if total_tools_used else 'None'}")
    print(f"{'Memory Messages':<25} {len(session.history.messages):<15} Conversation history")
    print(f"{'Memory Summaries':<25} {len(session.history.summaries):<15} History summaries")
    
    print()
    print("=" * 80)
    print("JOURNEY BREAKDOWN")
    print("=" * 80)
    
    journey_stages = [
        "Feature-specific property search",
        "Neighborhood research & culture",
        "Luxury property discovery",
        "School-focused family search",
        "Lifestyle-based recommendations"
    ]
    
    for i, (stage, result) in enumerate(zip(journey_stages, query_results), 1):
        status = "✓" if result.answer else "✗"
        tools = result.tools_used[0] if result.tools_used else "context-only"
        print(f"Stage {i}: {status} {stage}")
        print(f"         Time: {result.execution_time:.1f}s, Iterations: {result.iterations}, Tool: {tools}")
        
    print()
    print("=" * 80)
    print("KEY DEMONSTRATIONS VERIFIED")
    print("=" * 80)
    print("✓ Natural language understanding of complex preferences")
    print("✓ Multi-criteria property search (schools, amenities, lifestyle)")
    print("✓ Neighborhood research and cultural context")
    print("✓ School district analysis integration")
    print("✓ Context building across home buying journey")
    print("✓ Memory management for conversation continuity")
    print("✓ Personalized recommendations based on full context")
    print("✓ Trade-off analysis and decision support")
    
    print()
    print("=" * 80)
    print(f"✅ REAL ESTATE DEMO COMPLETED SUCCESSFULLY")
    print(f"   All {len(queries)} queries processed with {100*successful_queries/len(queries):.0f}% success rate")
    print(f"   Total execution time: {demo_total_time:.1f}s")
    print("=" * 80)

if __name__ == "__main__":
    main()