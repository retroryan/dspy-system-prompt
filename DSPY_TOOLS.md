# DSPy MCP Tools Implementation Analysis

## Executive Summary

DSPy has elegantly solved the dynamic tool discovery problem that we're facing. Their implementation provides a clean, simple pattern for integrating MCP (Model Context Protocol) tools with LLM agents. This document provides an in-depth analysis of how DSPy implements MCP tool support, with extensive code references and explanations of the complete flow.

## Core Architecture Overview

### The Fundamental Insight

DSPy treats tools as **instances** rather than **classes**. This is the key insight that eliminates all complexity around dynamic class generation. A tool in DSPy is simply an instance of the `Tool` class that wraps a callable function. The function can be:
- A regular Python function
- An async function
- A lambda
- Any callable object

This design means that MCP tools, which are discovered at runtime from a server, can be easily wrapped as Tool instances without any metaprogramming or dynamic class creation.

## The Complete MCP Tool Flow

### 1. MCP Server Definition

The MCP server defines tools using the FastMCP framework. Here's how a tool is defined on the server side (from `tests/utils/resources/mcp_server.py`):

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("test")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def get_account_name(account: Account):
    """This extracts the name from account"""
    return account.profile.name
```

The `@mcp.tool()` decorator registers these functions as discoverable tools in the MCP server. The server automatically:
- Extracts the function signature
- Generates JSON schema from type hints
- Provides the function description from docstring
- Makes the tool available for discovery via MCP protocol

### 2. Client-Side Tool Discovery

On the client side, DSPy connects to the MCP server and discovers available tools. From the tutorial (`docs/docs/tutorials/mcp/index.md`), here's the discovery process:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",
    args=["path/to/mcp_server.py"],
    env=None,
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize the connection
        await session.initialize()
        
        # List available tools - this queries the MCP server
        tools = await session.list_tools()
        
        # Convert each MCP tool to a DSPy Tool
        dspy_tools = []
        for tool in tools.tools:
            dspy_tools.append(dspy.Tool.from_mcp_tool(session, tool))
```

This process:
1. **Establishes connection**: Creates a stdio connection to the MCP server process
2. **Initializes session**: Performs MCP protocol handshake
3. **Discovers tools**: Calls `list_tools()` which returns all registered tools from the server
4. **Converts to DSPy Tools**: Each MCP tool is converted to a DSPy Tool instance

### 3. MCP to DSPy Tool Conversion

The conversion from MCP tool to DSPy Tool is handled by `convert_mcp_tool()` in `dspy/utils/mcp.py`:

```python
def convert_mcp_tool(session: "mcp.client.session.ClientSession", tool: "mcp.types.Tool") -> Tool:
    """Build a DSPy tool from an MCP tool.
    
    Args:
        session: The MCP session to use.
        tool: The MCP tool to convert.
    
    Returns:
        A dspy Tool object.
    """
    # Extract arguments from the MCP tool's input schema
    args, arg_types, arg_desc = convert_input_schema_to_tool_args(tool.inputSchema)
    
    # Create an async function that captures the session and tool name
    async def func(*args, **kwargs):
        result = await session.call_tool(tool.name, arguments=kwargs)
        return _convert_mcp_tool_result(result)
    
    # Return a Tool instance wrapping this function
    return Tool(
        func=func,
        name=tool.name,
        desc=tool.description,
        args=args,
        arg_types=arg_types,
        arg_desc=arg_desc
    )
```

This function performs several critical operations:

1. **Schema Extraction**: Converts the MCP tool's JSON schema into DSPy's format
2. **Session Capture**: The `session` parameter is captured in the closure of the `func` function
3. **Async Wrapper**: Creates an async function that will call the MCP server when executed
4. **Tool Creation**: Returns a Tool instance with all metadata and the executable function

The session capture is crucial - it means each Tool instance maintains its connection to the MCP server without any global state or complex lifecycle management.

### 4. The DSPy Tool Class

The Tool class (`dspy/adapters/types/tool.py`) is remarkably simple. Here are the key parts:

```python
class Tool(Type):
    """Tool class.
    
    This class is used to simplify the creation of tools for tool calling 
    (function calling) in LLMs. Only supports functions for now.
    """
    
    func: Callable
    name: str | None = None
    desc: str | None = None
    args: dict[str, Any] | None = None
    arg_types: dict[str, Any] | None = None
    arg_desc: dict[str, str] | None = None
    has_kwargs: bool = False
    
    def __init__(self, func: Callable, name: str | None = None, ...):
        """Initialize the Tool class."""
        super().__init__(func=func, name=name, desc=desc, args=args, ...)
        self._parse_function(func, arg_desc)
```

The Tool class:
- **Stores a callable**: The `func` attribute holds any callable (sync or async)
- **Maintains metadata**: Name, description, and argument schemas
- **Auto-infers types**: Can extract type information from function signatures
- **Validates arguments**: Uses JSON schema validation before calling

### 5. Tool Execution

When a tool is executed, the flow is straightforward. From the Tool class:

```python
@with_callbacks
async def acall(self, **kwargs):
    """Async call method for tools."""
    # Validate and parse arguments against the schema
    parsed_kwargs = self._validate_and_parse_args(**kwargs)
    
    # Call the wrapped function
    result = self.func(**parsed_kwargs)
    
    # Handle async results
    if asyncio.iscoroutine(result):
        return await result
    else:
        # Sync functions can be called in async context
        return result

def __call__(self, **kwargs):
    """Sync call method for tools."""
    parsed_kwargs = self._validate_and_parse_args(**kwargs)
    result = self.func(**parsed_kwargs)
    
    # Handle async functions in sync context
    if asyncio.iscoroutine(result):
        if settings.allow_tool_async_sync_conversion:
            return self._run_async_in_sync(result)
        else:
            raise ValueError("Use acall for async tools")
    return result
```

The execution flow:
1. **Validation**: Arguments are validated against the JSON schema
2. **Type Conversion**: Arguments are converted to correct Python types
3. **Function Call**: The wrapped function is called with parsed arguments
4. **Async Handling**: Handles both sync and async execution appropriately

For MCP tools, when `self.func(**parsed_kwargs)` is called, it executes the async function created in `convert_mcp_tool()`, which in turn calls `session.call_tool()` to execute the tool on the MCP server.

### 6. Integration with ReAct Agent

The ReAct module (`dspy/predict/react.py`) uses tools in its reasoning loop:

```python
class ReAct(Module):
    def __init__(self, signature: type["Signature"], tools: list[Callable], max_iters: int = 10):
        """ReAct stands for "Reasoning and Acting"."""
        super().__init__()
        
        # Convert all tools to Tool instances if they aren't already
        tools = [t if isinstance(t, Tool) else Tool(t) for t in tools]
        tools = {tool.name: tool for tool in tools}
        
        # Add a special "finish" tool
        tools["finish"] = Tool(
            func=lambda: "Completed.",
            name="finish",
            desc=f"Marks the task as complete",
            args={},
        )
        
        self.tools = tools
```

In the forward method, tools are executed within the reasoning loop:

```python
async def aforward(self, **input_args):
    trajectory = {}
    max_iters = input_args.pop("max_iters", self.max_iters)
    
    for idx in range(max_iters):
        # Get LLM to decide on next action
        pred = await self._async_call_with_potential_trajectory_truncation(
            self.react, trajectory, **input_args
        )
        
        # Store the reasoning
        trajectory[f"thought_{idx}"] = pred.next_thought
        trajectory[f"tool_name_{idx}"] = pred.next_tool_name
        trajectory[f"tool_args_{idx}"] = pred.next_tool_args
        
        # Execute the selected tool
        try:
            # This calls the tool's acall method
            trajectory[f"observation_{idx}"] = await self.tools[pred.next_tool_name].acall(
                **pred.next_tool_args
            )
        except Exception as err:
            trajectory[f"observation_{idx}"] = f"Execution error: {err}"
        
        # Check if we're done
        if pred.next_tool_name == "finish":
            break
```

The ReAct loop:
1. **LLM Reasoning**: Asks the LLM to think and select a tool
2. **Tool Selection**: LLM provides tool name and arguments
3. **Tool Execution**: Calls the tool's `acall()` method with arguments
4. **Observation**: Stores the tool's response
5. **Iteration**: Continues until "finish" tool is selected or max iterations

### 7. Result Processing

When an MCP tool returns a result, it needs to be converted from MCP's format to Python. From `dspy/utils/mcp.py`:

```python
def _convert_mcp_tool_result(call_tool_result: "mcp.types.CallToolResult") -> str | list[Any]:
    from mcp.types import TextContent
    
    text_contents: list[TextContent] = []
    non_text_contents = []
    
    # Separate text and non-text content
    for content in call_tool_result.content:
        if isinstance(content, TextContent):
            text_contents.append(content)
        else:
            non_text_contents.append(content)
    
    # Extract text from text contents
    tool_content = [content.text for content in text_contents]
    if len(text_contents) == 1:
        tool_content = tool_content[0]
    
    # Handle errors
    if call_tool_result.isError:
        raise RuntimeError(f"Failed to call a MCP tool: {tool_content}")
    
    return tool_content or non_text_contents
```

This handles:
- **Content Type Separation**: MCP can return text, images, or other content types
- **Text Extraction**: Extracts text from TextContent objects
- **Error Handling**: Converts MCP errors to Python exceptions
- **Fallback**: Returns non-text content if no text is available

## Key Design Patterns

### 1. Instance-Based Tools

Unlike traditional OOP where tools would be classes, DSPy uses instances:

```python
# Traditional approach (what we were trying)
class AddTool(BaseTool):
    def execute(self, a: int, b: int):
        return a + b

# DSPy approach
def add(a: int, b: int):
    return a + b

tool = Tool(func=add, name="add")
```

This is simpler and allows runtime tool creation without metaprogramming.

### 2. Closure-Based Session Management

The MCP session is captured in the tool's function closure:

```python
async def func(*args, **kwargs):
    # 'session' is captured from the enclosing scope
    result = await session.call_tool(tool.name, arguments=kwargs)
    return _convert_mcp_tool_result(result)
```

This eliminates the need for:
- Global session management
- Complex dependency injection
- Session lifecycle management

Each tool instance maintains its own reference to the session.

### 3. Async-First with Sync Support

DSPy handles both async and sync execution elegantly:

```python
def _run_async_in_sync(self, coroutine):
    try:
        # Check if we're already in an async context
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No async context, create one
        return asyncio.run(coroutine)
    
    # We're in async context, run until complete
    return loop.run_until_complete(coroutine)
```

This allows MCP tools (which are async) to work in both sync and async contexts.

### 4. Validation Through JSON Schema

Arguments are validated using JSON schema before execution:

```python
def _validate_and_parse_args(self, **kwargs):
    # Validate against JSON schema
    for k, v in kwargs.items():
        if k not in self.args:
            if self.has_kwargs:
                continue
            else:
                raise ValueError(f"Arg {k} is not in the tool's args.")
        try:
            instance = v.model_dump() if hasattr(v, "model_dump") else v
            type_str = self.args[k].get("type")
            if type_str is not None and type_str != "Any":
                validate(instance=instance, schema=self.args[k])
        except ValidationError as e:
            raise ValueError(f"Arg {k} is invalid: {e.message}")
```

This provides:
- Type safety without complex type systems
- Clear error messages
- Support for nested Pydantic models

## Complete Example Flow

Let's trace through a complete example of booking a flight using MCP tools:

1. **User Request**: "Book a flight from SFO to JFK on 09/01/2025"

2. **Tool Discovery**:
   ```python
   tools = await session.list_tools()
   # Returns: [fetch_flight_info, book_itinerary, get_user_info, ...]
   ```

3. **Tool Conversion**:
   ```python
   for tool in tools.tools:
       dspy_tool = dspy.Tool.from_mcp_tool(session, tool)
       # Creates Tool instance with async function that calls session.call_tool()
   ```

4. **ReAct Initialization**:
   ```python
   react = dspy.ReAct(DSPyAirlineCustomerService, tools=dspy_tools)
   # Stores tools in dictionary by name
   ```

5. **First Iteration** - Fetch Flights:
   - LLM thinks: "I need to fetch flight information"
   - Selects tool: `fetch_flight_info`
   - Provides args: `{date: {year: 2025, month: 9, day: 1}, origin: "SFO", destination: "JFK"}`
   - Tool execution: `await tools["fetch_flight_info"].acall(**args)`
   - MCP call: `await session.call_tool("fetch_flight_info", arguments=args)`
   - Server executes the actual function and returns flight list

6. **Second Iteration** - Get User Info:
   - LLM thinks: "I need user information for Adam"
   - Selects tool: `get_user_info`
   - Provides args: `{name: "Adam"}`
   - Tool execution follows same pattern

7. **Third Iteration** - Book Flight:
   - LLM thinks: "Now I can book the flight"
   - Selects tool: `book_itinerary`
   - Provides args: `{flight: {...}, user_profile: {...}}`
   - Server creates booking and returns confirmation

8. **Final Iteration** - Complete:
   - LLM selects: `finish` tool
   - Loop terminates
   - Final answer extracted from trajectory

## Why This Architecture Works

### Simplicity
- No dynamic class generation
- No complex inheritance hierarchies
- Tools are just functions wrapped in a simple class
- Clear, traceable execution flow

### Flexibility
- Supports any callable (functions, lambdas, methods)
- Handles both sync and async execution
- Works with local and remote (MCP) tools uniformly
- Easy to extend with new tool sources

### Maintainability
- Session management through closures is clean
- No global state
- Each tool is self-contained
- Clear separation of concerns

### Reliability
- JSON schema validation catches errors early
- MCP protocol handles serialization
- Async/await pattern prevents blocking
- Error handling at each level

## Lessons for Our Implementation

Based on this analysis, our implementation should:

1. **Modify BaseTool to support instances**: Allow tools to be instances, not just classes
2. **Use closures for MCP client**: Capture the MCP client in tool closures
3. **Single Tool proxy class**: One MCPToolProxy class for all MCP tools
4. **Simple validation**: Use JSON schema validation like DSPy
5. **Async-to-sync conversion**: Use `asyncio.run()` for our sync-only architecture
6. **Direct execution**: No complex delegation, just call the wrapped function

The key insight is that **dynamic tool discovery doesn't require dynamic class creation**. Tools can be instances created at runtime that implement a simple interface. This makes the entire system much simpler and more maintainable.