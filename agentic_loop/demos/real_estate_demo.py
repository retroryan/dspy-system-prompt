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
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich import box
from rich.layout import Layout
from rich.text import Text

# Configure clean output - suppress LiteLLM logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger('LiteLLM').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

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
        "Find cozy family home near good schools and parks in Oakland",
        
        # Query 6: Rich property details (NEW FEATURE!)
        "Give me comprehensive details about property prop-oak-125, including neighborhood demographics, local amenities, and relevant Wikipedia information about the area"
    ]

def main():
    """Run the complete real estate demo workflow."""
    import time
    from datetime import datetime
    import os
    
    # Setup
    setup_llm()
    
    # Check for verbose mode from environment
    verbose = os.getenv("DEMO_VERBOSE", "false").lower() == "true"
    
    
    session = AgentSession("real_estate_mcp", user_id="demo_homebuyer", verbose=verbose)
    
    # Demo header with rich
    console.print(Panel.fit(
        "[bold cyan]Real Estate Demo: Home Buying Journey[/bold cyan]\n\n" +
        "[italic]Advanced natural language real estate search with context building,\n" +
        "neighborhood research, and personalized recommendations.[/italic]" +
        ("\n\n[yellow]🔍 VERBOSE MODE: Showing agent thinking process[/yellow]" if verbose else ""),
        border_style="cyan",
        box=box.DOUBLE
    ))
    console.print()
    
    # Track execution metrics
    demo_start_time = time.time()
    total_iterations = 0
    total_tools_used = set()
    query_results = []
    
    # Run the complete workflow
    queries = get_home_buying_journey()
    
    for i, query in enumerate(queries, 1):
        # Query header
        console.rule(f"[bold blue]Query {i}/{len(queries)}[/bold blue]", style="blue")
        console.print()
        
        # Display the query in a nice panel
        query_panel = Panel(
            query,
            title=f"[bold]User Query[/bold]",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(query_panel)
        
        # Show context awareness for queries that build on previous results
        if i > 1:
            context_indicators = [
                "these neighborhoods", "Based on", "we've discussed", 
                "everything we've discussed", "Which of these", "more about"
            ]
            if any(indicator in query for indicator in context_indicators):
                console.print("\n[dim italic]💭 This query builds on previous conversation context[/dim italic]\n")
        
        # Execute query with progress spinner or verbose output
        if verbose:
            # In verbose mode, show agent thinking section
            console.print()
            console.print("[bold yellow]🤖 Agent Thinking Process:[/bold yellow]")
            console.print("[dim]" + "─" * 80 + "[/dim]")
            result = session.query(query, max_iterations=config.max_iterations)
            console.print("[dim]" + "─" * 80 + "[/dim]")
        else:
            # Normal mode with spinner
            with console.status("[bold green]Processing query...", spinner="dots") as status:
                result = session.query(query, max_iterations=config.max_iterations)
        
        # Track metrics
        total_iterations += result.iterations
        if result.tools_used:
            total_tools_used.update(result.tools_used)
        query_results.append(result)
        
        # Display result in a beautiful panel
        console.print()
        result_panel = Panel(
            result.answer,
            title="[bold green]Assistant Response[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(result_panel)
        
        # Show execution metrics in a table
        metrics_table = Table(show_header=False, box=box.SIMPLE, padding=0)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="white")
        
        metrics_table.add_row("⏱️  Time", f"{result.execution_time:.1f}s")
        metrics_table.add_row("🔄 Iterations", str(result.iterations))
        
        if result.tools_used:
            metrics_table.add_row("🔧 Tools", ', '.join(result.tools_used))
        else:
            metrics_table.add_row("🔧 Tools", "None (context only)")
        
        if len(session.history.messages) > 0:
            metrics_table.add_row("💾 Memory", f"{len(session.history.messages)} messages")
        
        console.print()
        console.print(metrics_table)
        console.print()
        
        # Add a small delay between queries for readability
        if i < len(queries):
            time.sleep(0.5)
    
    # Calculate final metrics
    demo_total_time = time.time() - demo_start_time
    successful_queries = len([r for r in query_results if r.answer])
    average_iterations = total_iterations / len(queries) if queries else 0
    average_time = sum(r.execution_time for r in query_results) / len(query_results) if query_results else 0
    
    # Demo completion
    console.rule("[bold green]Demo Complete![/bold green]", style="green")
    console.print()
    
    # Final Summary Report with Rich formatting
    summary_title = Panel(
        Text("REAL ESTATE DEMO SUMMARY REPORT", justify="center", style="bold cyan"),
        box=box.DOUBLE,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(summary_title)
    console.print()
    
    # Date and demo type
    console.print(f"[dim]Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    console.print(f"[dim]Demo Type: Real Estate MCP - Advanced Natural Language Home Search[/dim]")
    console.print()
    
    # Execution Statistics Table
    stats_table = Table(
        title="[bold]Execution Statistics[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    stats_table.add_column("Metric", style="cyan", width=25)
    stats_table.add_column("Value", style="yellow", width=15)
    stats_table.add_column("Details", style="white")
    
    stats_table.add_row(
        "Total Queries", 
        str(len(queries)), 
        "Complete home buying journey"
    )
    stats_table.add_row(
        "Successful Queries",
        f"{successful_queries}/{len(queries)}",
        f"[green]{100*successful_queries/len(queries):.0f}% success rate[/green]"
    )
    stats_table.add_row(
        "Total Time",
        f"{demo_total_time:.1f}s",
        "End-to-end execution"
    )
    stats_table.add_row(
        "Average Time/Query",
        f"{average_time:.1f}s",
        "Per query average"
    )
    stats_table.add_row(
        "Total Iterations",
        str(total_iterations),
        "React loop iterations"
    )
    stats_table.add_row(
        "Average Iterations",
        f"{average_iterations:.1f}",
        "Per query average"
    )
    stats_table.add_row(
        "Unique Tools Used",
        str(len(total_tools_used)),
        ', '.join(sorted(total_tools_used)) if total_tools_used else 'None'
    )
    stats_table.add_row(
        "Memory Messages",
        str(len(session.history.messages)),
        "Conversation history"
    )
    stats_table.add_row(
        "Memory Summaries",
        str(len(session.history.summaries)),
        "History summaries"
    )
    
    console.print(stats_table)
    
    console.print()
    
    # Journey Breakdown Table
    journey_table = Table(
        title="[bold]Journey Breakdown[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    journey_table.add_column("Stage", style="cyan", width=10)
    journey_table.add_column("Description", style="white", width=35)
    journey_table.add_column("Status", justify="center", width=8)
    journey_table.add_column("Time", style="yellow", width=8)
    journey_table.add_column("Iterations", style="yellow", width=10)
    journey_table.add_column("Tool", style="magenta", width=20)
    
    journey_stages = [
        "Feature-specific property search",
        "Neighborhood research & culture",
        "Luxury property discovery",
        "School-focused family search",
        "Lifestyle-based recommendations",
        "Rich property details with full data"
    ]
    
    for i, (stage, result) in enumerate(zip(journey_stages, query_results), 1):
        status = "[green]✓[/green]" if result.answer else "[red]✗[/red]"
        tools = result.tools_used[0] if result.tools_used else "context-only"
        journey_table.add_row(
            f"Stage {i}",
            stage,
            status,
            f"{result.execution_time:.1f}s",
            str(result.iterations),
            tools
        )
    
    console.print(journey_table)
        
    console.print()
    
    # Key Demonstrations Panel
    demonstrations = [
        "✓ Natural language understanding of complex preferences",
        "✓ Multi-criteria property search (schools, amenities, lifestyle)",
        "✓ Neighborhood research and cultural context",
        "✓ School district analysis integration",
        "✓ Context building across home buying journey",
        "✓ Memory management for conversation continuity",
        "✓ Personalized recommendations based on full context",
        "✓ Trade-off analysis and decision support",
        "✓ Rich property details with embedded neighborhood & Wikipedia data"
    ]
    
    demo_panel = Panel(
        "\n".join([f"[green]{demo}[/green]" for demo in demonstrations]),
        title="[bold]Key Demonstrations Verified[/bold]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(demo_panel)
    
    console.print()
    
    # Final success message
    success_panel = Panel(
        f"[bold green]✅ REAL ESTATE DEMO COMPLETED SUCCESSFULLY[/bold green]\n\n" +
        f"All {len(queries)} queries processed with [bold]{100*successful_queries/len(queries):.0f}% success rate[/bold]\n" +
        f"Total execution time: [bold]{demo_total_time:.1f}s[/bold]",
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(success_panel)

if __name__ == "__main__":
    main()