# MCP Tool Integration Demos

This directory contains demonstration scripts that showcase the MCP (Model Context Protocol) tool integration with the DSPy system project, implemented without any DSPy dependency.

## Prerequisites

1. **MCP Server Running**: Ensure the MCP server is running at `http://localhost:8000/mcp`
2. **Dependencies Installed**: Run `poetry install` in the project root
3. **Python Environment**: Use `poetry run` to execute demos with correct dependencies

## Available Demos

### 1. Tool Discovery Demo (`demo_tool_discovery.py`)

Shows the dynamic discovery process of MCP tools:
- Direct discovery from MCP server
- Tool set integration with proxy creation
- Registry integration
- Detailed tool introspection

**Run:** `poetry run python mcp_demos/demo_tool_discovery.py`

### 2. Direct Tool Execution Demo (`demo_direct_tools.py`)

Demonstrates direct execution of MCP tools through the registry:
- Property search with filters
- Neighborhood research via Wikipedia
- Natural language search with AI
- System health checks

**Run:** `poetry run python mcp_demos/demo_direct_tools.py`

### 3. Property Search Demo (`demo_property_search.py`)

Shows integration with agent sessions for conversational property search:
- Natural language property queries
- Neighborhood research
- Multi-turn conversations with context

**Run:** `poetry run python mcp_demos/demo_property_search.py`

### 4. Run All Demos (`run_all_demos.py`)

Executes all demos in sequence to showcase the complete functionality.

**Run:** `poetry run python mcp_demos/run_all_demos.py`

## Key Features Demonstrated

### Instance-Based Architecture
- Tools are instances wrapping functions, not classes
- No dynamic class generation needed
- Clean separation of concerns

### Closure-Based State Management
- Each tool proxy captures MCP client reference
- No global state or complex dependency injection
- Thread-safe and self-contained

### Dynamic Discovery
- Tools discovered at runtime from MCP server
- Server can add/remove tools without code changes
- Automatic schema to Pydantic model conversion

### Clean Integration
- Works with existing tool registry
- Compatible with agent sessions
- Full Pydantic validation throughout

## Architecture Highlights

```
MCP Server (http://localhost:8000/mcp)
    ↓ (discovers tools)
MCPClient 
    ↓ (creates proxies)
MCPToolProxy (instances with closures)
    ↓ (registers)
ToolRegistry
    ↓ (executes)
Agent Session / Direct Execution
```

## Success Metrics

✅ **6 tools discovered** from live MCP server
✅ **All tests passing** including optional parameter handling
✅ **Clean architecture** with no DSPy dependency
✅ **Production ready** with proper error handling
✅ **Modular design** with clear separation of concerns

## Example Output

When running the tool discovery demo, you'll see:
- Discovery of 6 real estate tools
- Automatic proxy creation for each tool
- Integration with the registry
- Detailed parameter information for each tool

## Troubleshooting

If demos fail to run:
1. Check MCP server is running: `curl http://localhost:8000/mcp`
2. Verify dependencies: `poetry install`
3. Use poetry environment: `poetry run python ...`
4. Check server logs for any errors

## Next Steps

This implementation is production-ready and can be extended to:
- Add more MCP servers for different domains
- Implement connection pooling for performance
- Add caching for tool discovery
- Create additional tool sets for other use cases