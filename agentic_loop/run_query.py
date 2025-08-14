#!/usr/bin/env python3
"""
Run custom queries through the agentic loop.

Supports both command line arguments and stdin input.
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared import ConsoleFormatter, setup_llm
from agentic_loop.core_loop import run_agent_loop
from shared.tool_utils.registry import ToolRegistry
from tools.ecommerce.tool_set import EcommerceToolSet
from tools.precision_agriculture.tool_set import AgricultureToolSet
from tools.events.tool_set import EventsToolSet

# Available tool sets
TOOL_SETS = {
    EcommerceToolSet.NAME: EcommerceToolSet,
    AgricultureToolSet.NAME: AgricultureToolSet,
    EventsToolSet.NAME: EventsToolSet,
}

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def run_query(query: str, tool_set_name: str, max_iterations: int = 10) -> None:
    """Run a custom query through the agent loop."""
    verbose = os.getenv("DEMO_VERBOSE", "false").lower() == "true"
    
    if verbose:
        console = ConsoleFormatter()
        logger.info(console.section_header('🚀 Running Custom Query'))
        logger.info(f"Tool Set: {tool_set_name}")
        logger.info(f"Query: {query}\n")
    
    # Setup LLM
    setup_llm()
    
    # Create tool registry
    tool_set = TOOL_SETS[tool_set_name]()
    registry = ToolRegistry()
    registry.register_tool_set(tool_set)
    
    # Run the agent loop
    try:
        result = run_agent_loop(
            user_query=query,
            tool_registry=registry,
            tool_set_name=tool_set_name,
            max_iterations=max_iterations
        )
        
        if result['status'] == 'success':
            if verbose:
                trajectory = result['trajectory']
                console = ConsoleFormatter()
                logger.info(console.section_header('📊 Summary', char='-', width=60))
                logger.info(f"✓ Completed in {result['execution_time']:.2f}s")
                logger.info(f"  Iterations: {trajectory.iteration_count}")
                logger.info(f"  Tools used: {', '.join(trajectory.tools_used) if trajectory.tools_used else 'None'}")
                logger.info("")
            
            # Print the final answer
            print(result['answer'])
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            logger.error(f"Error: {error_msg}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run custom queries through the agentic loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poetry run python agentic_loop/run_query.py agriculture "What's the weather in NYC?"
  poetry run python agentic_loop/run_query.py ecommerce "Find laptops under $1000"
  echo "Track order 12345" | poetry run python agentic_loop/run_query.py ecommerce

Tool sets: agriculture, ecommerce, events
        """
    )
    
    parser.add_argument(
        'tool_set',
        choices=list(TOOL_SETS.keys()),
        help='Tool set to use'
    )
    
    parser.add_argument(
        'query',
        nargs='*',
        help='Query (reads from stdin if not provided)'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Max iterations (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Get query from args or stdin
    if args.query:
        query = ' '.join(args.query)
    else:
        # Read from stdin
        query = sys.stdin.read().strip()
    
    if not query:
        logger.error("Error: No query provided")
        logger.error("Provide a query as an argument or via stdin")
        sys.exit(1)
    
    # Run the query
    try:
        run_query(query, args.tool_set, args.max_iterations)
    except KeyboardInterrupt:
        logger.info("\n\nQuery interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()