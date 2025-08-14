#!/bin/bash

# Function to show help
show_help() {
    echo "DSPy Agentic Loop Demo"
    echo ""
    echo "Usage: ./run_demo.sh [OPTIONS] [ARGS]"
    echo ""
    echo "Modes:"
    echo "  Test Mode (default):"
    echo "    ./run_demo.sh [TOOL_SET] [TEST_INDEX]"
    echo ""
    echo "  Query Mode:"
    echo "    ./run_demo.sh --query TOOL_SET \"Your query here\""
    echo "    echo \"Your query\" | ./run_demo.sh --query TOOL_SET"
    echo ""
    echo "Options:"
    echo "  --query, -q      Run a custom query with specified tool set"
    echo "  --verbose, -v    Show agent thoughts and tool results"
    echo "  --debug, -d      Enable full DSPy debug output (very verbose!)"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "Tool Sets:"
    echo "  agriculture      Weather and farming tools (default)"
    echo "  ecommerce       Shopping and order management tools"
    echo "  events          Event planning and management tools"
    echo ""
    echo "Examples:"
    echo "  # Test mode examples:"
    echo "  ./run_demo.sh                           # Run default agriculture test cases"
    echo "  ./run_demo.sh ecommerce                 # Run all ecommerce test cases"
    echo "  ./run_demo.sh ecommerce 3               # Run ecommerce test case 3 only"
    echo "  ./run_demo.sh --verbose agriculture 2   # Verbose mode for agriculture test 2"
    echo ""
    echo "  # Query mode examples:"
    echo "  ./run_demo.sh --query agriculture \"What's the weather in NYC?\""
    echo "  ./run_demo.sh -q ecommerce \"Find laptops under \$1000\""
    echo "  echo \"Track order 12345\" | ./run_demo.sh --query ecommerce"
    echo ""
    echo "  # Complex ecommerce scenarios:"
    echo "  ./run_demo.sh ecommerce                 # Run all test cases including complex ones"
    echo "  ./run_demo.sh ecommerce 13              # Run complex multi-step purchase test"
    exit 0
}

# Initialize variables
QUERY_MODE=false
TOOL_SET=""
REMAINING_ARGS=()

# Process command line flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            ;;
        --debug|-d)
            echo "🐛 Running in debug mode (DSPY_DEBUG=true)"
            export DSPY_DEBUG=true
            shift
            ;;
        --verbose|-v)
            echo "📢 Running in verbose mode (DEMO_VERBOSE=true)"
            export DEMO_VERBOSE=true
            shift
            ;;
        --query|-q)
            QUERY_MODE=true
            shift
            # Next argument should be the tool set
            if [[ "$#" -gt 0 ]]; then
                TOOL_SET="$1"
                shift
            fi
            # Remaining arguments are the query
            break
            ;;
        *)
            REMAINING_ARGS+=("$1")
            shift
            ;;
    esac
done

# Add any remaining arguments after --query processing
while [[ "$#" -gt 0 ]]; do
    REMAINING_ARGS+=("$1")
    shift
done

# Ensure test_results directory exists for logging
mkdir -p test_results

if [ "$QUERY_MODE" = true ]; then
    # Query mode - use run_query.py
    if [ -z "$TOOL_SET" ]; then
        echo "Error: Tool set required for query mode"
        echo "Usage: ./run_demo.sh --query TOOL_SET \"Your query\""
        exit 1
    fi
    
    # Check if query is provided as arguments or should be read from stdin
    if [ ${#REMAINING_ARGS[@]} -gt 0 ]; then
        # Query provided as arguments
        exec poetry run python -m agentic_loop.run_query "$TOOL_SET" "${REMAINING_ARGS[@]}"
    else
        # Read from stdin
        exec poetry run python -m agentic_loop.run_query "$TOOL_SET"
    fi
else
    # Test mode - use demo_react_agent.py
    echo "📊 Test results will be saved to test_results/ directory"
    exec poetry run python -m agentic_loop.demo_react_agent "${REMAINING_ARGS[@]}"
fi