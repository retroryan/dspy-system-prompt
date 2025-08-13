#!/usr/bin/env python
"""Run a custom e-commerce query through the agentic loop."""

import sys
import os
import logging
from agentic_loop.core_loop import run_agent_loop
from shared.tool_utils.registry import ToolRegistry
from tools.ecommerce.tool_set import EcommerceToolSet
from shared.llm_utils import setup_llm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    # Get query from command line or stdin
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = sys.stdin.read().strip()
    
    if not query:
        print("Error: No query provided")
        sys.exit(1)
    
    # Setup LLM
    setup_llm()
    
    # Create tool set and registry
    tool_set = EcommerceToolSet()
    tool_registry = ToolRegistry()
    tool_registry.register_tool_set(tool_set)
    
    # Check verbose mode
    verbose = os.getenv("DEMO_VERBOSE", "false").lower() == "true"
    
    # Run the agent loop
    try:
        result = run_agent_loop(
            user_query=query,
            tool_registry=tool_registry,
            tool_set_name="ecommerce",
            max_iterations=10  # Allow more iterations for complex queries
        )
        
        # Print the result
        if result and result.get('status') == 'success':
            if verbose:
                print("\n" + "=" * 60)
                print("📊 Final Result:")
                print("=" * 60)
                print(f"Tools used: {', '.join(result.get('tools_used', []))}")
                print(f"Iterations: {result.get('total_iterations', 0)}")
                print(f"Execution time: {result.get('execution_time', 0):.2f}s")
                print("=" * 60)
            
            final_answer = result.get('answer', 'No answer generated')
            print(final_answer)
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"Error: {error_msg}")
    except Exception as e:
        print(f"Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()