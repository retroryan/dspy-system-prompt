#!/usr/bin/env python3
"""
Primary query runner for the agentic loop.

This is THE way to execute queries through the custom agentic loop.
Uses AgentSession directly and returns type-safe SessionResult.

Can be:
- Imported and used programmatically
- Called from command line
- Used by demo_runner to showcase capabilities
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared import ConsoleFormatter, setup_llm
from agentic_loop.session import AgentSession, SessionResult

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def run_query(
    query: str,
    tool_set_name: str = "agriculture",
    max_iterations: int = 10,
    verbose: Optional[bool] = None,
    session: Optional[AgentSession] = None
) -> SessionResult:
    """
    Execute a query through the agentic loop using AgentSession.
    
    This is THE primary way to run queries. Clean, simple, type-safe.
    
    Args:
        query: The user's question or task
        tool_set_name: Which tool set to use (agriculture, ecommerce, events)
        max_iterations: Maximum React loop iterations
        verbose: Whether to show detailed logs (defaults to DEMO_VERBOSE env var)
        session: Optional existing session for multi-turn conversations
    
    Returns:
        SessionResult with trajectory, answer, and metadata
    """
    # Determine verbosity
    if verbose is None:
        verbose = os.getenv("DEMO_VERBOSE", "false").lower() == "true"
    
    # Setup LLM (idempotent - safe to call multiple times)
    setup_llm()
    
    # Create or use provided session
    if session is None:
        session = AgentSession(
            tool_set_name=tool_set_name,
            verbose=verbose
        )
    
    # Execute query through session (THE way to interact with agents)
    result = session.query(query, max_iterations=max_iterations)
    
    return result


def main():
    """Command-line interface for run_query."""
    parser = argparse.ArgumentParser(
        description="Run queries through the agentic loop",
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
        choices=['agriculture', 'ecommerce', 'events'],
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
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed execution logs'
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
    
    # Determine verbosity
    verbose = args.verbose or os.getenv("DEMO_VERBOSE", "false").lower() == "true"
    
    # Display header if verbose
    if verbose:
        console = ConsoleFormatter()
        logger.info(console.section_header('🚀 Running Query'))
        logger.info(f"Tool Set: {args.tool_set}")
        logger.info(f"Query: {query}\n")
    
    # Run the query
    try:
        result = run_query(
            query=query,
            tool_set_name=args.tool_set,
            max_iterations=args.max_iterations,
            verbose=verbose
        )
        
        # Display results based on verbosity
        if verbose:
            console = ConsoleFormatter()
            logger.info(console.section_header('📊 Summary', char='-', width=60))
            logger.info(f"✓ Completed in {result.execution_time:.2f}s")
            logger.info(f"  Iterations: {result.iterations}")
            logger.info(f"  Tools used: {', '.join(result.tools_used) if result.tools_used else 'None'}")
            logger.info("")
        
        # Always print the final answer
        print(result.answer)
        
    except KeyboardInterrupt:
        logger.info("\n\nQuery interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()