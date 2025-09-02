#!/bin/bash

# ============================================================================
# DSPy Agent Demo Runner - Complete Workflows
# ============================================================================
#
# Usage:
#   ./run_demo.sh                    # Show help
#   ./run_demo.sh agriculture        # Run agriculture demo
#   ./run_demo.sh ecommerce          # Run e-commerce demo  
#   ./run_demo.sh real_estate        # Run real estate demo
#   ./run_demo.sh --all              # Run all demos
#   ./run_demo.sh --list             # List all demos
#
# Options:
#   --verbose, -v                    # Show detailed output
#   --debug                          # Enable debug mode
#   --help, -h                       # Show help
#
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Function to load .env file and get values
get_env_value() {
    local key="$1"
    local default="$2"
    
    if [ -f ".env" ]; then
        # Extract value from .env file, handling comments and spaces
        local value=$(grep "^${key}=" .env 2>/dev/null | head -1 | cut -d'=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/^"//;s/"$//')
        if [ -n "$value" ]; then
            echo "$value"
        else
            echo "$default"
        fi
    else
        echo "$default"
    fi
}

# Parse options
VERBOSE=false
DEBUG=false
DEMO_NAME=""
RUN_ALL=false

# Function to show header
show_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║              ${PURPLE}DSPy Agent Demo Runner${CYAN}                         ║${NC}"
    echo -e "${CYAN}║          ${BLUE}Complete Workflow Demonstrations${CYAN}                   ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Function to show help
show_help() {
    show_header
    echo -e "${GREEN}Usage:${NC}"
    echo "  ./run_demo.sh [options] [demo_name]"
    echo
    echo -e "${GREEN}Available Demos:${NC}"
    echo "  agriculture    Complete farming workflow (weather → planting decision)"
    echo "  ecommerce      Complete shopping workflow (orders → checkout)"
    echo "  real_estate    Complete home buying journey (search → recommendations)"
    echo
    echo -e "${GREEN}Options:${NC}"
    echo "  --all          Run all demos in sequence"
    echo "  --list, -l     List all available demos"
    echo "  --verbose, -v  Show detailed output"
    echo "  --debug        Enable debug mode (DSPY_DEBUG=true)"
    echo "  --help, -h     Show this help message"
    echo
    echo -e "${GREEN}Examples:${NC}"
    echo "  ./run_demo.sh agriculture        # Run agriculture demo"
    echo "  ./run_demo.sh real_estate -v     # Run real estate demo with verbose output"
    echo "  ./run_demo.sh --all              # Run all demos"
    echo "  ./run_demo.sh --debug ecommerce  # Run ecommerce demo with debug output"
    echo
    echo -e "${GREEN}Environment Variables (current values):${NC}"
    
    # Get actual values from .env or environment
    local llm_model=$(get_env_value "LLM_MODEL" "ollama_chat/gemma2:27b")
    local llm_temp=$(get_env_value "LLM_TEMPERATURE" "0.7")
    local llm_tokens=$(get_env_value "LLM_MAX_TOKENS" "1024")
    local demo_debug=$(get_env_value "DEMO_DEBUG" "false")
    local dspy_debug=$(get_env_value "DSPY_DEBUG" "false")
    
    # Determine provider from LLM_MODEL
    local provider="ollama"
    if [[ "$llm_model" == openrouter/* ]]; then
        provider="openrouter"
    elif [[ "$llm_model" == anthropic/* ]]; then
        provider="anthropic"
    elif [[ "$llm_model" == openai/* ]]; then
        provider="openai"
    elif [[ "$llm_model" == gemini/* ]]; then
        provider="gemini"
    elif [[ "$llm_model" == ollama_chat/* ]]; then
        provider="ollama"
    fi
    
    echo "  LLM_MODEL        $llm_model"
    echo "  LLM_TEMPERATURE  $llm_temp"
    echo "  LLM_MAX_TOKENS   $llm_tokens"
    echo "  DEMO_DEBUG       $demo_debug"
    echo "  DSPY_DEBUG       $dspy_debug"
    
    if [ -f ".env" ]; then
        echo
        echo -e "  ${CYAN}(Values loaded from .env)${NC}"
    else
        echo
        echo -e "  ${YELLOW}(Using defaults - no .env file found)${NC}"
    fi
}

# Function to list demos
list_demos() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Demo Name      Description${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "agriculture    Complete farming workflow with weather analysis"
    echo "               - Current weather comparison"
    echo "               - 7-day forecast analysis"
    echo "               - Agricultural conditions assessment"
    echo "               - Planting recommendations"
    echo
    echo "ecommerce      Complete shopping workflow demonstration"
    echo "               - Order history review"
    echo "               - Product search and filtering"
    echo "               - Cart management"
    echo "               - Checkout process"
    echo
    echo "real_estate    Complete home buying journey"
    echo "               - Lifestyle preference discovery"
    echo "               - Neighborhood research & comparison"
    echo "               - School district analysis"
    echo "               - Targeted property search"
    echo "               - Personalized recommendations"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to setup environment
setup_environment() {
    export PYTHONPATH="."
    export DSPY_PROVIDER="${DSPY_PROVIDER:-ollama}"
    export OLLAMA_MODEL="${OLLAMA_MODEL:-gemma2:27b}"
    export LLM_TEMPERATURE="${LLM_TEMPERATURE:-0.7}"
    export LLM_MAX_TOKENS="${LLM_MAX_TOKENS:-1024}"
    
    if [ "$VERBOSE" = true ]; then
        export DEMO_VERBOSE="true"
    fi
    
    if [ "$DEBUG" = true ]; then
        export DSPY_DEBUG="true"
    fi
}

# Function to show configuration
show_configuration() {
    echo -e "${BLUE}Configuration:${NC}"
    echo "  Provider: $DSPY_PROVIDER"
    if [ "$DSPY_PROVIDER" == "ollama" ]; then
        echo "  Model: $OLLAMA_MODEL"
    fi
    echo "  Temperature: $LLM_TEMPERATURE"
    echo "  Max Tokens: $LLM_MAX_TOKENS"
    
    if [ "$VERBOSE" = true ]; then
        echo -e "  ${YELLOW}Verbose: Enabled${NC}"
    fi
    
    if [ "$DEBUG" = true ]; then
        echo -e "  ${YELLOW}Debug: Enabled${NC}"
    fi
    echo
}

# Function to run agriculture demo
run_agriculture() {
    echo -e "${GREEN}Running Agriculture Demo...${NC}"
    echo -e "${BLUE}Complete farming workflow with weather analysis${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    poetry run python -m agentic_loop.demos.agriculture_demo
}

# Function to run ecommerce demo
run_ecommerce() {
    echo -e "${GREEN}Running E-commerce Demo...${NC}"
    echo -e "${BLUE}Complete shopping workflow demonstration${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    poetry run python -m agentic_loop.demos.ecommerce_demo
}

# Function to run real estate demo
run_real_estate() {
    echo -e "${GREEN}Running Real Estate Demo...${NC}"
    echo -e "${BLUE}Complete home buying journey with natural language search${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    
    # Check if MCP server is running (optional)
    if curl -s -f -o /dev/null "http://localhost:8000/mcp" 2>/dev/null; then
        echo -e "${GREEN}✓ MCP server detected${NC}"
    else
        echo -e "${YELLOW}⚠ MCP server not detected at http://localhost:8000/mcp${NC}"
        echo -e "${YELLOW}  Demo will attempt to run anyway...${NC}"
    fi
    echo
    
    PYTHONPATH=. poetry run python agentic_loop/demos/real_estate_demo.py
}

# Function to run a specific demo
run_demo() {
    local demo=$1
    
    case "$demo" in
        agriculture)
            run_agriculture
            ;;
        ecommerce)
            run_ecommerce
            ;;
        real_estate)
            run_real_estate
            ;;
        *)
            echo -e "${RED}Error: Unknown demo '$demo'${NC}"
            echo "Valid demos: agriculture, ecommerce, real_estate"
            exit 1
            ;;
    esac
}

# Function to run all demos
run_all_demos() {
    echo -e "${PURPLE}Running all demos in sequence...${NC}"
    echo
    
    # Run agriculture demo
    echo -e "${CYAN}[1/3] Agriculture Demo${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
    run_agriculture
    echo
    echo -e "${GREEN}✓ Agriculture demo completed${NC}"
    echo
    sleep 2
    
    # Run ecommerce demo
    echo -e "${CYAN}[2/3] E-commerce Demo${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
    run_ecommerce
    echo
    echo -e "${GREEN}✓ E-commerce demo completed${NC}"
    echo
    sleep 2
    
    # Run real estate demo
    echo -e "${CYAN}[3/3] Real Estate Demo${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
    run_real_estate
    echo
    echo -e "${GREEN}✓ Real estate demo completed${NC}"
    echo
    
    echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ All demos completed successfully!${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --list|-l)
            show_header
            list_demos
            exit 0
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        agriculture|ecommerce|real_estate)
            DEMO_NAME=$1
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option '$1'${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main execution
if [ "$RUN_ALL" = true ]; then
    show_header
    setup_environment
    show_configuration
    run_all_demos
elif [ -n "$DEMO_NAME" ]; then
    show_header
    setup_environment
    show_configuration
    run_demo "$DEMO_NAME"
    
    # Check exit status
    if [ $? -eq 0 ]; then
        echo
        echo -e "${GREEN}✅ Demo completed successfully!${NC}"
    else
        echo
        echo -e "${YELLOW}⚠ Demo encountered issues. Check the output above.${NC}"
    fi
else
    # No arguments provided, show help
    show_help
fi