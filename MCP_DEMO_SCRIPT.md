# MCP Demo Script - Quick Start Guide

## 🚀 Quick Start

```bash
# Make script executable (first time only)
chmod +x run_mcp_demo.sh

# Run interactive menu
./run_mcp_demo.sh

# Run specific demo
./run_mcp_demo.sh 1    # Tool Discovery
./run_mcp_demo.sh 2    # Direct Execution
./run_mcp_demo.sh 3    # Property Search

# Run all demos
./run_mcp_demo.sh --all

# Quick connection test
./run_mcp_demo.sh --quick
```

## 📋 Available Options

| Option | Description |
|--------|-------------|
| `(no args)` | Interactive menu with all options |
| `1` | Tool Discovery Demo - Shows dynamic discovery |
| `2` | Direct Tool Execution - Registry-level execution |
| `3` | Property Search Demo - Agent integration |
| `4` | Complete Showcase - All demos in sequence |
| `5` | Integration Tests - Full test suite |
| `6` | Quick Test - Connection and discovery check |
| `--all` | Run all demos automatically |
| `--test` | Run integration test suite |
| `--quick` | Quick connection test |
| `--help` | Show help information |

## 🎯 Demo Highlights

### Interactive Menu
The default mode presents a user-friendly menu:
- Color-coded options
- Clear descriptions
- Prerequisites check
- Server status validation

### Tool Discovery (Option 1)
- Connects to MCP server
- Discovers 6 real estate tools
- Shows parameter details
- Demonstrates dynamic nature

### Direct Execution (Option 2)
- Property search with filters
- Wikipedia research
- Natural language AI search
- System health check

### Complete Showcase (Option 4)
- Runs multiple demos in sequence
- Shows full capabilities
- Pause between demos
- Summary at the end

## ✅ Prerequisites Check

The script automatically checks:
- Python installation
- Poetry availability
- Dependencies installed
- MCP server accessibility

## 🎨 Features

- **Color-coded output** for better readability
- **Automatic prerequisite checking**
- **Error handling** with helpful messages
- **Interactive and batch modes**
- **Server status validation**
- **Clean, professional interface**

## 🔧 Environment Variables

```bash
# Custom MCP server URL (optional)
MCP_SERVER_URL=http://custom-server:8000/mcp ./run_mcp_demo.sh
```

## 📊 Expected Output

When running the quick test:
```
✅ Successfully discovered 6 tools:
   - search_properties_tool
   - get_property_details_tool
   - search_wikipedia_tool
   - search_wikipedia_by_location_tool
   - natural_language_search_tool
   - health_check_tool
```

## 🎉 Demo Ready

The script provides a professional, easy-to-use interface for demonstrating the MCP tool integration. It handles all setup, validation, and execution details, allowing you to focus on showcasing the functionality.