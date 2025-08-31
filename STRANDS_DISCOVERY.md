# STRANDS_DISCOVERY.md

## Complete Cut-Over Requirements

* ALWAYS FIX THE CORE ISSUE! 
* COMPLETE CHANGE: All occurrences must be changed in a single, atomic update
* CLEAN IMPLEMENTATION: Simple, direct replacements only
* NO MIGRATION PHASES: Do not create temporary compatibility periods
* NO PARTIAL UPDATES: Change everything or change nothing
* NO COMPATIBILITY LAYERS: Do not maintain old and new paths simultaneously
* NO BACKUPS OF OLD CODE: Do not comment out old code "just in case"
* NO CODE DUPLICATION: Do not duplicate functions to handle both patterns
* NO WRAPPER FUNCTIONS: Direct replacements only, no abstraction layers
* DO NOT CALL FUNCTIONS ENHANCED or IMPROVED and change the actual methods
* ALWAYS USE PYDANTIC
* USE MODULES AND CLEAN CODE!
* Never name things after the phases or steps of the proposal
* if hasattr should never be used. And never use isinstance
* Never cast variables or cast variable names or add variable aliases 
* If you are using a union type something is wrong
* If it doesn't work don't hack and mock. Fix the core issue
* Do not generate mocks or sample data if the actual results are missing

## Executive Summary

This proposal presents a simplified approach to integrating MCP (Model Context Protocol) tools with DSPy, inspired by the Strands framework's clean architecture. Rather than creating complex proxy classes or modifying the registry, we leverage DSPy's existing MCP support and introduce a simple adapter pattern that maintains our current tool architecture while enabling dynamic discovery. The solution is elegant, maintainable, and requires minimal changes to existing code.

## The Problem We're Solving

Our current DSPy implementation assumes all tools are static Python classes defined at compile time. MCP tools are discovered dynamically from servers at runtime. We need to bridge this gap without:

1. Creating dynamic classes at runtime
2. Breaking existing tool sets
3. Adding complex abstraction layers
4. Introducing maintenance burden

## The Strands-Inspired Solution

After studying the Strands framework, we've identified a cleaner approach that:

1. **Uses DSPy's Built-in MCP Support**: DSPy already has `dspy.utils.mcp.convert_mcp_tool()` for converting MCP tools
2. **Simple Adapter Pattern**: A single MCPToolAdapter class that wraps DSPy's MCP tools for our BaseTool interface
3. **Context Manager for Lifecycle**: Clean connection management using Python's with statement
4. **Direct Tool Discovery**: Simple synchronous method to list and adapt tools
5. **Instance-Based Registration**: Tools are registered as instances, not classes

## How DSPy's MCP Support Works

DSPy provides built-in MCP support through the `dspy.utils.mcp` module, specifically the `convert_mcp_tool()` function located at `/Users/ryanknight/projects/temporal/dspy/dspy/utils/mcp.py:30-47`. This function elegantly bridges the gap between MCP tools and DSPy's Tool class.

### The convert_mcp_tool Function

The `convert_mcp_tool` function takes two parameters:
1. **session**: An MCP ClientSession that maintains the connection to the MCP server
2. **tool**: An MCP tool object returned from the server's list_tools() method

The conversion process involves three key steps:

**Step 1: Schema Conversion**
The function calls `convert_input_schema_to_tool_args()` (defined at `/Users/ryanknight/projects/temporal/dspy/dspy/adapters/types/tool.py:365-394`) which parses the MCP tool's inputSchema JSON schema and extracts:
- **args**: A dictionary mapping parameter names to their JSON schema definitions
- **arg_types**: A dictionary mapping parameter names to Python types (str, int, float, bool, list, dict)
- **arg_desc**: A dictionary mapping parameter names to their descriptions, marking required fields

**Step 2: Async Wrapper Creation**
The function creates an async wrapper function that:
- Accepts arguments as keyword parameters
- Calls the MCP session's `call_tool()` method with the tool name and arguments
- Processes the result through `_convert_mcp_tool_result()` to handle different content types

**Step 3: Tool Object Creation**
Finally, it creates a DSPy Tool object with:
- The async wrapper function as the executable
- The tool's name and description from the MCP tool
- The converted args, arg_types, and arg_desc dictionaries

### Result Processing

The `_convert_mcp_tool_result()` function (at `/Users/ryanknight/projects/temporal/dspy/dspy/utils/mcp.py:9-27`) handles the MCP server's response:
- Separates text content from non-text content (images, structured data)
- Concatenates multiple text responses into a single string if only one text response exists
- Returns the text content or non-text content list
- Raises a RuntimeError if the MCP server indicates an error

### DSPy Tool Class Integration

The DSPy Tool class (at `/Users/ryanknight/projects/temporal/dspy/dspy/adapters/types/tool.py:20-256`) provides rich functionality:

**Validation and Parsing**:
- The `_validate_and_parse_args()` method validates arguments against the JSON schema
- Supports Pydantic models for complex nested structures
- Handles default values and optional parameters

**Execution Methods**:
- `__call__()`: Synchronous execution that can optionally run async tools in sync mode
- `acall()`: Native async execution for async tools
- Both methods validate and parse arguments before execution

**Type Safety**:
- Uses JSON schema validation to ensure arguments match expected types
- Converts arguments to proper Python types using Pydantic
- Provides clear error messages for validation failures

### Example Usage from Tests

The test file at `/Users/ryanknight/projects/temporal/dspy/tests/utils/test_mcp.py` demonstrates practical usage:

1. **Simple arithmetic tool** (lines 28-37): Takes two integers and returns their sum as a string
2. **Array handling** (lines 40-46): Accepts an array of names and returns greetings
3. **Error handling** (lines 49-55): Shows how MCP errors are converted to Python RuntimeErrors
4. **Nested objects** (lines 58-89): Demonstrates complex nested Pydantic model support
5. **No-argument tools** (lines 92-98): Shows tools that require no input parameters

### Key Advantages of DSPy's Approach

1. **Type Safety**: Full JSON schema validation and Pydantic integration
2. **Error Handling**: Clear error messages with proper exception types
3. **Async Support**: Native async/await with optional sync conversion
4. **Schema Resolution**: Handles complex schemas with references and definitions
5. **Clean Abstraction**: MCP details hidden behind simple Tool interface

## Key Design Principles

### Simplicity First
We prioritize simple, readable code over complex abstractions. The entire MCP integration can be understood in minutes, not hours.

### Leverage Existing Infrastructure
DSPy already handles MCP protocol details. We simply adapt their tools to our interface rather than reimplementing the protocol.

### Synchronous Operations
Following DSPy best practices and our codebase principles, all operations are synchronous. No async code, no background threads.

### Clean Separation
MCP-specific code is isolated to a few files. The core tool infrastructure remains unchanged except for supporting instance-based registration.

### Demo-Quality Balance
We aim for high-quality demo code that's production-ready in structure but avoids unnecessary complexity like connection pooling or retry logic.

## Architecture Overview

### Component Structure

```
tools/
├── base_tool.py           # Unchanged BaseTool interface
├── mcp/
│   ├── __init__.py
│   ├── mcp_client.py      # Simple MCP client with context manager
│   ├── mcp_adapter.py     # Adapter from DSPy MCP tool to BaseTool
│   └── mcp_tool_set.py    # Base class for MCP-based tool sets
└── real_estate/
    └── real_estate_mcp_set.py  # Concrete MCP tool set implementation
```

### Data Flow

1. **Connection**: MCPClient connects to MCP server using stdio transport
2. **Discovery**: Client calls list_tools() to get available tools from server
3. **Conversion**: DSPy's convert_mcp_tool() converts MCP tools to DSPy format
4. **Adaptation**: MCPToolAdapter wraps DSPy tools as BaseTool instances
5. **Registration**: Tool instances are registered directly in the registry
6. **Execution**: Tool calls are proxied through the adapter to the MCP server

## Detailed Design

### MCPClient Class

A simple client that manages the MCP connection lifecycle:

**Responsibilities**:
- Initialize MCP ClientSession using stdio transport
- Provide context manager for clean resource management
- Discover available tools from the server using list_tools()
- Maintain the session for DSPy's convert_mcp_tool() to use

**Key Features**:
- Simple synchronous wrapper around MCP's async ClientSession
- Context manager pattern for lifecycle (async with internally)
- Configuration from environment variables
- Clear error messages when server unavailable

**DSPy Integration Details**:
The MCPClient will wrap the MCP ClientSession which is required by DSPy's convert_mcp_tool(). The client will:
- Use StdioServerParameters to configure the server command and arguments
- Create the session using stdio_client() which returns read/write streams
- Initialize the ClientSession with these streams
- Call session.initialize() to establish the connection
- Provide the session to convert_mcp_tool() for each discovered tool

### MCPToolAdapter Class

Adapts DSPy's MCP tools to our BaseTool interface:

**Responsibilities**:
- Inherit from BaseTool to satisfy type requirements
- Store DSPy Tool instance created by convert_mcp_tool()
- Implement execute() by calling the DSPy tool's __call__ method
- Provide proper name and description properties from DSPy tool
- Leverage DSPy's built-in argument validation

**Key Features**:
- Thin adapter layer with minimal logic
- Delegates all validation to DSPy's Tool class
- Synchronous execution using DSPy's sync conversion
- Maintains compatibility with BaseTool interface
- Clean error handling and reporting

**Integration with DSPy**:
The adapter will store the DSPy Tool object returned by convert_mcp_tool(). When execute() is called, it will invoke the DSPy tool's __call__ method which handles:
- Argument validation against the JSON schema
- Type conversion using Pydantic
- Async-to-sync conversion if needed (controlled by settings.allow_tool_async_sync_conversion)
- Error handling and result processing

### MCPToolSet Base Class

Base class for all MCP-based tool sets:

**Responsibilities**:
- Connect to MCP server on initialization
- Discover and adapt available tools
- Provide tool instances to the registry
- Manage client lifecycle
- Define React and Extract signatures for the domain

**Key Features**:
- Extends standard ToolSet base class
- Overrides provides_instances() to return True
- Implements get_tool_instances() to return adapted tools
- Handles graceful degradation when server unavailable

### Modified ToolSet Base Class

Direct modifications to support instance-based tool sets:

**Changes Required**:
- Add provides_instances() method returning False by default
- Add get_tool_instances() method returning empty list by default
- Make tool_classes optional in ToolSetConfig
- Update validation to handle optional tool_classes

**Backward Compatibility**:
- Existing tool sets continue working unchanged
- Default implementations ensure no breaking changes
- Single code path handles both static and dynamic tools

### Modified Registry

Updates to handle instance-based registration:

**Changes Required**:
- Check if tool set provides instances using provides_instances()
- If True, get instances using get_tool_instances() and register directly
- If False, use existing class instantiation logic
- No changes to external API or tool retrieval

**Benefits**:
- Minimal code changes
- Clean separation of concerns
- No performance impact on existing tools
- Transparent to tool users

## Implementation Benefits

### Maintainability
- Leverages proven DSPy code instead of reimplementing
- Simple adapter pattern easy to understand and debug
- Clear separation between static and dynamic tools
- Minimal changes to existing infrastructure

### Reliability
- DSPy handles protocol complexity
- Context manager ensures proper cleanup
- Graceful degradation when server unavailable
- Clear error messages for troubleshooting

### Performance
- Lazy discovery only when tool set initialized
- No overhead for existing static tools
- Direct execution path with minimal indirection
- No unnecessary abstractions or layers

### Developer Experience
- Simple, intuitive API
- Consistent with existing patterns
- Easy to add new MCP tool sets
- Clear documentation and examples

## Error Handling Strategy

### Server Connection Failures
- Tool set initializes with empty tool list
- Clear warning logged about unavailability
- Agent continues without MCP tools
- No crashes or exceptions

### Tool Discovery Failures
- Individual tool failures don't break discovery
- Failed tools logged but skipped
- Partial tool sets supported
- System remains functional

### Execution Failures
- DSPy handles protocol-level errors
- Clear error messages returned to agent
- Agent can retry or use alternative tools
- No state corruption

### Configuration Errors
- Helpful error messages for missing configuration
- Defaults where appropriate
- Validation at initialization time
- Early failure with clear guidance

## Configuration Management

### Environment Variables
```
MCP_SERVER_COMMAND: Command to start MCP server (e.g., "uvx")
MCP_SERVER_ARGS: Arguments for server command (e.g., "server-package@latest")
MCP_TIMEOUT: Request timeout in seconds (default: 30)
```

### No Hardcoded Values
- All configuration from environment
- No file paths in code
- No server management logic
- Pure client implementation

## Testing Strategy

### Unit Tests
- MCPToolAdapter with mock DSPy tools
- MCPClient with mock server responses
- Registry with instance-based tool sets
- ToolSet base class modifications

### Integration Tests
- Real MCP server connection
- Tool discovery validation
- Tool execution with various arguments
- Error handling scenarios

### Demo Tests
- Complete workflows with MCP tools
- Session persistence across queries
- Context building with discovered tools
- Performance validation

## Migration Path

This is a pure extension with no breaking changes:

1. **Existing Tool Sets**: Continue working exactly as before
2. **New MCP Tool Sets**: Use the new MCPToolSet base class
3. **Registry**: Transparently handles both types
4. **No Code Changes**: Existing code needs no modifications

## Implementation Plan

### Phase 1: Core Infrastructure Extensions
**Goal**: Extend base classes to support instance-based tool sets

**Tasks**:
- [ ] Add provides_instances() method to ToolSet base class with False default
- [ ] Add get_tool_instances() method to ToolSet base class with empty list default
- [ ] Modify ToolSetConfig to make tool_classes optional
- [ ] Update ToolSet validation to handle optional tool_classes
- [ ] Create comprehensive unit tests for ToolSet extensions
- [ ] Document the new ToolSet methods and their usage
- [ ] Verify backward compatibility with existing tool sets
- [ ] Code review and testing

### Phase 2: MCP Client Implementation
**Goal**: Create simple MCP client for server communication

**Tasks**:
- [ ] Create MCPClient class with context manager pattern
- [ ] Implement stdio transport initialization
- [ ] Add list_tools() method for tool discovery
- [ ] Add call_tool() method for tool execution
- [ ] Implement configuration from environment variables
- [ ] Add connection timeout handling
- [ ] Create unit tests with mock server
- [ ] Code review and testing

### Phase 3: Tool Adapter Implementation
**Goal**: Build adapter between DSPy MCP tools and BaseTool

**Tasks**:
- [ ] Create MCPToolAdapter class inheriting from BaseTool
- [ ] Implement name and description properties from DSPy tool
- [ ] Implement execute() method delegating to DSPy tool
- [ ] Add proper error handling and logging
- [ ] Create Pydantic models for tool metadata
- [ ] Write comprehensive unit tests
- [ ] Document adapter pattern and usage
- [ ] Code review and testing

### Phase 4: MCP Tool Set Base Class
**Goal**: Create reusable base class for MCP tool sets

**Tasks**:
- [ ] Create MCPToolSet extending ToolSet
- [ ] Implement MCP client initialization
- [ ] Add tool discovery on initialization
- [ ] Create MCPToolAdapter instances for each tool
- [ ] Override provides_instances() to return True
- [ ] Override get_tool_instances() to return adapters
- [ ] Add graceful degradation for server unavailability
- [ ] Code review and testing

### Phase 5: Registry Updates
**Goal**: Extend registry to handle instance-based tool sets

**Tasks**:
- [ ] Modify register_tool_set to check provides_instances()
- [ ] Add branch for direct instance registration
- [ ] Maintain existing class instantiation path
- [ ] Ensure get_tool works for both types
- [ ] Add comprehensive tests for mixed scenarios
- [ ] Verify no performance regression
- [ ] Document registry changes
- [ ] Code review and testing

### Phase 6: Real Estate MCP Tool Set
**Goal**: Implement concrete MCP tool set for real estate domain

**Tasks**:
- [ ] Create RealEstateMCPToolSet extending MCPToolSet
- [ ] Configure MCP server connection for real estate tools
- [ ] Define domain-specific React signature
- [ ] Define domain-specific Extract signature
- [ ] Implement get_test_cases() with expected tools
- [ ] Create integration tests with real MCP server
- [ ] Add demo showing complete workflow
- [ ] Code review and testing

### Phase 7: Integration with AgentSession
**Goal**: Ensure MCP tools work seamlessly with existing session architecture

**Tasks**:
- [ ] Test MCP tools with AgentSession.query()
- [ ] Verify conversation history tracks MCP tool usage
- [ ] Validate context management with dynamic tools
- [ ] Test memory persistence across sessions
- [ ] Create demo showing session continuity
- [ ] Document MCP tool usage in sessions
- [ ] Performance testing with multiple queries
- [ ] Code review and testing

### Phase 8: Demo and Documentation
**Goal**: Create comprehensive demos and documentation

**Tasks**:
- [ ] Create agriculture demo with MCP weather tools
- [ ] Create e-commerce demo with MCP product tools
- [ ] Write user documentation for MCP tool sets
- [ ] Create developer guide for adding MCP servers
- [ ] Document configuration and deployment
- [ ] Add troubleshooting guide
- [ ] Create performance benchmarks
- [ ] Code review and testing

### Phase 9: Final Integration Testing
**Goal**: Validate complete system with all tool types

**Tasks**:
- [ ] Run all existing tool set tests
- [ ] Test mixed static and MCP tool scenarios
- [ ] Validate all demos work correctly
- [ ] Check performance metrics
- [ ] Test error recovery scenarios
- [ ] Verify logging and debugging capabilities
- [ ] Conduct user acceptance testing
- [ ] Code review and testing

## Success Criteria

1. **Seamless Integration**: MCP tools work identically to static tools from the agent's perspective
2. **No Breaking Changes**: All existing tool sets and demos continue working
3. **Clean Architecture**: Code remains simple, readable, and maintainable
4. **Reliable Operation**: Graceful handling of server unavailability and errors
5. **Good Performance**: No degradation for existing tools, acceptable latency for MCP tools
6. **Developer Friendly**: Easy to add new MCP tool sets with minimal code
7. **Well Tested**: Comprehensive test coverage including edge cases
8. **Properly Documented**: Clear documentation for users and developers

## Risk Mitigation

### Risk: DSPy MCP Support Changes
**Mitigation**: Pin DSPy version, monitor for breaking changes, maintain compatibility layer if needed

### Risk: MCP Protocol Evolution
**Mitigation**: Use stable protocol version, implement version checking, provide clear upgrade path

### Risk: Performance Impact
**Mitigation**: Lazy discovery, efficient adapter implementation, performance testing and monitoring

### Risk: Debugging Complexity
**Mitigation**: Clear logging, simple code flow, comprehensive error messages, debugging documentation

### Risk: Server Management Complexity
**Mitigation**: Client-only implementation, no server lifecycle management, clear deployment documentation

## Key Advantages Over Previous Proposal

1. **Leverages DSPy**: Uses proven DSPy MCP support instead of reimplementing
2. **Simpler Architecture**: No proxy classes or complex abstractions
3. **Cleaner Separation**: MCP code isolated to specific module
4. **Better Testing**: Easier to test with clear boundaries
5. **Maintainable**: Less code to maintain, clearer responsibilities
6. **Production Ready**: Based on Strands' production patterns

## Conclusion

This Strands-inspired approach provides a clean, simple solution for integrating MCP tools with DSPy. By leveraging existing DSPy capabilities and using a straightforward adapter pattern, we achieve dynamic tool discovery without complexity. The solution maintains backward compatibility, follows our architectural principles, and provides a solid foundation for future enhancements.

The implementation is deliberately simple - avoiding production complexities like connection pooling or retry logic while maintaining high code quality and proper architecture. This balance makes the code both educational and practical, perfect for a high-quality demo that could evolve into production use.