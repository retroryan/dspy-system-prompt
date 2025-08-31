#!/bin/bash

# ============================================================================
# MCP Tool Integration Demo Runner
# ============================================================================
# 
# This script provides easy access to all MCP tool integration demos,
# showcasing dynamic tool discovery and execution without DSPy dependency.
#
# Usage:
#   ./run_mcp_demo.sh           # Show interactive menu
#   ./run_mcp_demo.sh 1         # Run specific demo by number
#   ./run_mcp_demo.sh --all     # Run all demos
#   ./run_mcp_demo.sh --test    # Run integration tests
#   ./run_mcp_demo.sh --help    # Show help
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

# MCP Server URL
MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:8000/mcp}"

# Function to show header
show_header() {
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          ${PURPLE}MCP Tool Integration Demo Runner${CYAN}                   ║${NC}"
    echo -e "${CYAN}║        ${BLUE}Dynamic Tool Discovery Without DSPy${CYAN}                  ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${YELLOW}Server URL: ${GREEN}$MCP_SERVER_URL${NC}"
    echo
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check Python
    if ! command -v python &> /dev/null; then
        echo -e "${RED}✗ Python is not installed${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ Python is available${NC}"
    fi
    
    # Check Poetry
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}✗ Poetry is not installed${NC}"
        echo "  Please install Poetry: https://python-poetry.org"
        exit 1
    else
        echo -e "${GREEN}✓ Poetry is available${NC}"
    fi
    
    # Check if dependencies are installed
    if ! poetry run python -c "import fastmcp" 2>/dev/null; then
        echo -e "${YELLOW}Installing dependencies...${NC}"
        poetry install
    else
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    fi
    
    # Check MCP server
    if curl -s -o /dev/null -w "%{http_code}" "$MCP_SERVER_URL" | grep -q "307\|406\|200"; then
        echo -e "${GREEN}✓ MCP server is accessible at $MCP_SERVER_URL${NC}"
    else
        echo -e "${YELLOW}⚠️  MCP server may not be running at $MCP_SERVER_URL${NC}"
        echo -e "${YELLOW}   Some demos may fail without the server${NC}"
    fi
    
    echo
}

# Function to show menu
show_menu() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Available Demos:${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    echo -e "  ${BLUE}1)${NC} 🔍 Tool Discovery Demo"
    echo -e "     ${YELLOW}Discover tools dynamically from MCP server${NC}"
    echo
    echo -e "  ${BLUE}2)${NC} 🔧 Direct Tool Execution Demo"
    echo -e "     ${YELLOW}Execute MCP tools directly through registry${NC}"
    echo
    echo -e "  ${BLUE}3)${NC} 🏠 Property Search Demo"
    echo -e "     ${YELLOW}Natural language property search with intelligent tool selection${NC}"
    echo
    echo -e "  ${BLUE}4)${NC} 🎭 Complete Showcase"
    echo -e "     ${YELLOW}Run all demos in sequence${NC}"
    echo
    echo -e "  ${BLUE}5)${NC} 🧪 Integration Tests"
    echo -e "     ${YELLOW}Run the complete test suite${NC}"
    echo
    echo -e "  ${BLUE}6)${NC} 📊 Quick Test"
    echo -e "     ${YELLOW}Test MCP connection and tool discovery${NC}"
    echo
    echo -e "  ${BLUE}q)${NC} Exit"
    echo
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -n -e "${GREEN}Select an option [1-6, q]: ${NC}"
}

# Function to run a demo
run_demo() {
    local demo_num=$1
    local demo_file=""
    local demo_name=""
    
    case $demo_num in
        1)
            demo_file="mcp_demos/demo_tool_discovery.py"
            demo_name="Tool Discovery Demo"
            ;;
        2)
            demo_file="mcp_demos/demo_direct_tools.py"
            demo_name="Direct Tool Execution Demo"
            ;;
        3)
            demo_file="mcp_demos/demo_property_search.py"
            demo_name="Property Search Demo"
            ;;
        4)
            demo_file="mcp_demos/run_all_demos.py"
            demo_name="Complete Showcase"
            ;;
        5)
            demo_file="tools/real_estate/test_mcp_integration.py"
            demo_name="Integration Tests"
            ;;
        6)
            # Quick test - just try to discover tools
            echo -e "${CYAN}Running quick MCP connection test...${NC}"
            echo
            poetry run python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tools.real_estate.mcp_client import create_mcp_client

async def test():
    client = create_mcp_client('$MCP_SERVER_URL')
    tools = await client.discover_tools()
    return tools

tools = asyncio.run(test())
print(f'✅ Successfully discovered {len(tools)} tools:')
for t in tools:
    print(f'   - {t.name}')
" 2>/dev/null
            return
            ;;
        *)
            echo -e "${RED}Invalid option: $demo_num${NC}"
            return 1
            ;;
    esac
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Running: ${YELLOW}$demo_name${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    
    # Run the demo with poetry, suppressing warnings
    poetry run python "$demo_file" 2>/dev/null || {
        echo -e "${RED}Demo failed. Check if MCP server is running.${NC}"
        return 1
    }
    
    echo
    echo -e "${GREEN}✓ Demo completed successfully!${NC}"
}

# Function to run all demos
run_all_demos() {
    echo -e "${CYAN}Running all demos in sequence...${NC}"
    echo
    
    for i in 1 2 4; do
        run_demo $i
        echo
        echo -e "${YELLOW}Press Enter to continue to next demo...${NC}"
        read -r
    done
    
    echo -e "${GREEN}All demos completed!${NC}"
}

# Function to show help
show_help() {
    show_header
    echo -e "${GREEN}Usage:${NC}"
    echo "  ./run_mcp_demo.sh [options] [demo_number]"
    echo
    echo -e "${GREEN}Options:${NC}"
    echo "  (no args)      Show interactive menu"
    echo "  1-6            Run specific demo by number"
    echo "  --all          Run all demos in sequence"
    echo "  --test         Run integration tests"
    echo "  --quick        Quick connection test"
    echo "  --help, -h     Show this help message"
    echo
    echo -e "${GREEN}Demo Numbers:${NC}"
    echo "  1 - Tool Discovery Demo"
    echo "  2 - Direct Tool Execution Demo"
    echo "  3 - Property Search Demo"
    echo "  4 - Complete Showcase"
    echo "  5 - Integration Tests"
    echo "  6 - Quick Connection Test"
    echo
    echo -e "${GREEN}Environment Variables:${NC}"
    echo "  MCP_SERVER_URL   MCP server URL (default: http://localhost:8000/mcp)"
    echo
    echo -e "${GREEN}Examples:${NC}"
    echo "  ./run_mcp_demo.sh                  # Interactive menu"
    echo "  ./run_mcp_demo.sh 1                # Run tool discovery demo"
    echo "  ./run_mcp_demo.sh --all            # Run all demos"
    echo "  ./run_mcp_demo.sh --test           # Run tests"
    echo
    echo -e "${GREEN}Requirements:${NC}"
    echo "  • Python 3.8+"
    echo "  • Poetry installed"
    echo "  • MCP server running at $MCP_SERVER_URL"
    echo
}

# Main script logic
main() {
    # Parse command line arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --all)
            show_header
            check_prerequisites
            run_all_demos
            exit 0
            ;;
        --test)
            show_header
            check_prerequisites
            run_demo 5
            exit 0
            ;;
        --quick)
            show_header
            check_prerequisites
            run_demo 6
            exit 0
            ;;
        [1-6])
            show_header
            check_prerequisites
            run_demo "$1"
            exit 0
            ;;
        "")
            # Interactive mode
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
    
    # Interactive menu loop
    while true; do
        show_header
        check_prerequisites
        show_menu
        
        read -r choice
        
        case $choice in
            [1-6])
                echo
                run_demo "$choice"
                echo
                echo -e "${YELLOW}Press Enter to return to menu...${NC}"
                read -r
                ;;
            q|Q)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

# Run main function
main "$@"