#!/bin/bash

# Function to show help
show_help() {
    echo "DSPy Agentic Loop Demo"
    echo ""
    echo "Usage: ./run_demo.sh [OPTIONS] [TOOL_SET] [TEST_INDEX]"
    echo ""
    echo "Options:"
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
    echo "  ./run_demo.sh                    # Run with default agriculture tools"
    echo "  ./run_demo.sh --verbose          # Show detailed agent thoughts"
    echo "  ./run_demo.sh -v ecommerce       # Verbose mode with ecommerce tools"
    echo "  ./run_demo.sh agriculture 2      # Run only test case 2"
    exit 0
}

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
        *)
            break
            ;;
    esac
done

exec poetry run python -m agentic_loop.demo_react_agent "$@"