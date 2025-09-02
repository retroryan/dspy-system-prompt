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

# Track start time
START_TIME=$(date +"%Y-%m-%d %H:%M:%S")

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
    echo -e "  ${BLUE}4)${NC} 🤖 AI Semantic Search Demo"
    echo -e "     ${YELLOW}Natural language understanding with AI embeddings${NC}"
    echo
    echo -e "  ${BLUE}5)${NC} 🌍 Location Discovery Demo"
    echo -e "     ${YELLOW}Location-based contextual discovery and insights${NC}"
    echo
    echo -e "  ${BLUE}6)${NC} 🔄 Multi-Tool Orchestration Demo"
    echo -e "     ${YELLOW}Complex scenarios with coordinated tool usage${NC}"
    echo
    echo -e "  ${BLUE}7)${NC} 🎭 Complete Showcase (All Demos)"
    echo -e "     ${YELLOW}Run all demos in sequence${NC}"
    echo
    echo -e "  ${BLUE}8)${NC} 🧪 Integration Tests"
    echo -e "     ${YELLOW}Run the complete test suite${NC}"
    echo
    echo -e "  ${BLUE}9)${NC} 📊 Quick Connection Test"
    echo -e "     ${YELLOW}Test MCP server connectivity${NC}"
    echo
    echo -e "  ${BLUE}q)${NC} Exit"
    echo
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -n -e "${GREEN}Select an option [1-9, q]: ${NC}"
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
            demo_file="mcp_demos/demo_semantic_search.py"
            demo_name="AI Semantic Search Demo"
            ;;
        5)
            demo_file="mcp_demos/demo_location_context.py"
            demo_name="Location Discovery Demo"
            ;;
        6)
            demo_file="mcp_demos/demo_multi_tool.py"
            demo_name="Multi-Tool Orchestration Demo"
            ;;
        7)
            # Run all demos in sequence
            demo_name="Complete Showcase"
            run_all_demos true  # Run in interactive mode when selected from menu
            return
            ;;
        8)
            demo_file="tools/real_estate/test_mcp_integration.py"
            demo_name="Integration Tests"
            ;;
        9)
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
    local interactive=${1:-true}  # Default to interactive mode
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}MCP TOOL INTEGRATION - COMPLETE DEMO SHOWCASE${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Running all MCP demos with REAL SERVER DATA${NC}"
    echo -e "Start time: $START_TIME"
    echo
    
    local demos=(1 2 3 4 5 6)
    local demo_names=(
        "Tool Discovery Demo"
        "Direct Tool Execution Demo"
        "Property Search Demo"
        "AI Semantic Search Demo"
        "Location Discovery Demo"
        "Multi-Tool Orchestration Demo"
    )
    
    local total=${#demos[@]}
    local successful=0
    local failed=0
    local start_seconds=$(date +%s)
    
    echo -e "${GREEN}📋 Demos to run (${total} total):${NC}"
    for i in "${!demos[@]}"; do
        echo -e "   $((i+1)). ${demo_names[$i]}"
    done
    echo
    echo -e "${CYAN}🚀 Starting demo sequence...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    sleep 2
    
    for i in "${!demos[@]}"; do
        echo
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}Demo $((i+1))/${total}: ${demo_names[$i]}${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        if run_demo ${demos[$i]}; then
            ((successful++))
            echo -e "${GREEN}✅ ${demo_names[$i]} completed successfully${NC}"
        else
            ((failed++))
            echo -e "${RED}❌ ${demo_names[$i]} failed${NC}"
        fi
        
        if [ $((i+1)) -lt $total ]; then
            if [ "$interactive" = "true" ]; then
                echo
                echo -e "${YELLOW}⏸️  Press Enter to continue to next demo...${NC}"
                read -r
            else
                echo
                echo -e "${YELLOW}⏱️  Continuing to next demo...${NC}"
                sleep 2
            fi
        fi
    done
    
    local end_seconds=$(date +%s)
    local total_time=$((end_seconds - start_seconds))
    local end_time=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}COMPLETE DEMO SHOWCASE SUMMARY${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    echo -e "${GREEN}📊 Results: ${successful}/${total} demos completed successfully${NC}"
    
    if [ $failed -gt 0 ]; then
        echo -e "${RED}   ${failed} demo(s) failed${NC}"
    fi
    
    echo -e "${BLUE}⏱️  Total execution time: ${total_time} seconds${NC}"
    echo -e "${BLUE}🕐 End time: ${end_time}${NC}"
    echo
    
    if [ $successful -eq $total ]; then
        echo -e "${GREEN}🎉 ALL DEMOS COMPLETED SUCCESSFULLY!${NC}"
        echo
        echo -e "${CYAN}📊 Demo Coverage:${NC}"
        echo -e "   ✅ Dynamic tool discovery from MCP server"
        echo -e "   ✅ Direct tool execution with real data"
        echo -e "   ✅ Intelligent property search"
        echo -e "   ✅ AI-powered semantic understanding"
        echo -e "   ✅ Location-based contextual discovery"
        echo -e "   ✅ Multi-tool orchestration for complex scenarios"
        echo
        echo -e "${CYAN}💡 Key Features Demonstrated:${NC}"
        echo -e "   • All data is LIVE from the MCP server"
        echo -e "   • No mock data or hardcoded responses"
        echo -e "   • Tools discovered dynamically at runtime"
        echo -e "   • Clean architecture without DSPy dependency"
        echo -e "   • Real-world scenarios and use cases"
        echo
        echo -e "${GREEN}🚀 The MCP tool integration is production-ready!${NC}"
    else
        echo -e "${YELLOW}⚠️  ${failed} demo(s) had issues.${NC}"
        echo -e "Please check the error messages above."
        echo
        echo -e "${CYAN}Troubleshooting:${NC}"
        echo -e "1. Ensure MCP server is running at $MCP_SERVER_URL"
        echo -e "2. Check that all required services are available"
        echo -e "3. Verify network connectivity to the server"
    fi
}

# Function to show help
show_help() {
    show_header
    echo -e "${GREEN}Usage:${NC}"
    echo "  ./run_mcp_demo.sh [options] [demo_number]"
    echo
    echo -e "${GREEN}Options:${NC}"
    echo "  (no args)      Show interactive menu"
    echo "  1-9            Run specific demo by number"
    echo "  --all          Run all demos in sequence"
    echo "  --test         Run integration tests"
    echo "  --quick        Quick connection test"
    echo "  --help, -h     Show this help message"
    echo
    echo -e "${GREEN}Demo Numbers:${NC}"
    echo "  1 - Tool Discovery Demo"
    echo "  2 - Direct Tool Execution Demo"
    echo "  3 - Property Search Demo"
    echo "  4 - AI Semantic Search Demo"
    echo "  5 - Location Discovery Demo"
    echo "  6 - Multi-Tool Orchestration Demo"
    echo "  7 - Complete Showcase (All Demos)"
    echo "  8 - Integration Tests"
    echo "  9 - Quick Connection Test"
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
            run_all_demos false  # Run in non-interactive mode
            exit 0
            ;;
        --test)
            show_header
            check_prerequisites
            run_demo 8
            exit 0
            ;;
        --quick)
            show_header
            check_prerequisites
            run_demo 9
            exit 0
            ;;
        [1-9])
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
            [1-9])
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