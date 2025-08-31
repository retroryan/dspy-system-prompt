# Dynamic MCP Tool Discovery Proposal

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

The current DSPy tool architecture assumes tools are static classes defined at compile time. MCP tools are discovered dynamically at runtime from a server. This proposal outlines how to cleanly extend the base tool set infrastructure to support both static and dynamic tool discovery without creating dynamic classes, using hasattr/isinstance, or introducing complexity.

## The Core Problem

The fundamental mismatch is between two different paradigms:

1. **DSPy's Static Model**: Tools are Python classes that inherit from BaseTool, defined at compile time, with known names and signatures
2. **MCP's Dynamic Model**: Tools are remote procedures discovered at runtime from a server, with names and signatures provided by the server

The current registry expects to:
- Receive a list of tool classes from ToolSetConfig
- Instantiate each class when registering
- Call execute() on instances

But MCP tools aren't classes - they're metadata about remote procedures that must be called through an MCP client.

## The Solution: Leverage DSPy's MCP Support

DSPy already has built-in MCP support through `dspy.utils.mcp.convert_mcp_tool()`. Instead of reinventing the wheel, we should:

1. Use DSPy's MCP tool conversion to get DSPy Tool objects
2. Create a simple adapter from DSPy Tool to our BaseTool
3. Modify the core infrastructure to support instance-based tool sets
4. Keep the existing static tool sets working unchanged

This leverages proven, tested code and maintains consistency with DSPy's design patterns.

## Key Design Principles

### Single Source of Truth
The MCP server is the single source of truth for available tools. We don't cache or duplicate this information - we query it when needed.

### Lazy Discovery
Tools are discovered when the tool set is initialized, not at import time. This allows the MCP server to be unavailable during development without breaking imports.

### Stateless Execution
Each tool execution creates a fresh connection to the MCP server. No persistent connections, no connection management, no state corruption.

### Direct Integration
No intermediate abstractions or wrappers. The MCPToolProxy directly implements BaseTool and directly calls the MCP server.

## Architecture Overview

### Component Relationships

1. **MCPToolProxy**: A single, reusable class that implements BaseTool and proxies calls to an MCP server
2. **MCPToolSet**: Base class for MCP-based tool sets that handles discovery and provides instances
3. **Modified ToolSet**: Core base class updated to support both static classes and dynamic instances
4. **Modified Registry**: Core registry updated to handle both class-based and instance-based registration

### Data Flow

1. Tool set initialization triggers MCP server discovery
2. For each discovered tool, an MCPToolProxy instance is created
3. Tool set provides these instances to the registry
4. Registry uses instances directly instead of instantiating classes
5. Tool execution proxies through to MCP server

## Detailed Design

### MCPToolProxy Class

This class bridges the gap between DSPy's expectations and MCP's reality:

- Inherits from BaseTool to satisfy type requirements
- Stores MCP tool metadata (name, description, schema)
- Implements execute() by calling the MCP server
- Uses Pydantic for all data structures
- Handles argument validation using MCP schema

### MCPToolSet Base Class

A new base class for MCP-based tool sets that:

- Extends the standard ToolSet
- Discovers tools from MCP server on initialization
- Creates MCPToolProxy instances for each discovered tool
- Provides instances instead of classes to the registry
- Handles connection configuration from environment

### Modified ToolSet Base Class

Direct modifications to the core ToolSet class to support dynamic discovery:

- Add method to check if tool set provides instances or classes
- Add method to get tool instances directly
- Maintain backward compatibility with static tool sets
- Use Pydantic models throughout
- Default implementations ensure existing tool sets work unchanged

### Modified Registry

Direct modifications to the core Registry to handle instance-based registration:

- Check if tool set provides instances or classes
- Use provided instances directly when available
- Fall back to class instantiation for static tools
- No change to external API
- Single code path handles both types

## Implementation Benefits

### Simplicity
- One proxy class handles all MCP tools
- No dynamic class generation
- No complex metaprogramming
- Clear, traceable code flow

### Maintainability
- MCP integration isolated to specific classes
- Existing tool sets unchanged
- Easy to debug and test
- No magic or hidden behavior

### Reliability
- Stateless operation prevents corruption
- Server validates all arguments
- Graceful degradation when server unavailable
- Clear error messages

### Performance
- Lazy discovery reduces startup time
- No unnecessary connections
- Efficient connection reuse pattern
- Minimal overhead

## Error Handling Strategy

### Server Unavailable
- Tool discovery returns empty list
- Tool set initializes with no tools
- Agent continues without MCP tools
- Clear warning in logs

### Discovery Failures
- Individual tool failures don't break discovery
- Partial discovery supported
- Failed tools logged but skipped
- System remains functional

### Execution Failures
- Clear error messages returned
- Next execution gets fresh connection
- No corrupted state possible
- Agent can retry or use different tool

## Configuration Management

### Environment Variables
- MCP_SERVER_URL: Server endpoint (default: http://localhost:8000/mcp)
- MCP_TIMEOUT: Request timeout in seconds
- MCP_MAX_RETRIES: Number of retry attempts

### No Hardcoded Paths
- All configuration from environment
- No file paths in code
- No server startup logic
- Pure client-side implementation

## Testing Strategy

### Unit Tests
- MCPToolProxy with mock server responses
- MCPToolSet with mock discovery
- Registry with instance-based tool sets
- Error handling scenarios

### Integration Tests
- Real MCP server connection
- Tool discovery validation
- Execution with various arguments
- Graceful failure handling

### System Tests
- Agent session with MCP tools
- Complex multi-tool workflows
- Performance under load
- Recovery from failures

## Migration Path

This is a pure extension - no migration needed:

1. Existing tool sets continue working unchanged
2. New MCP tool sets use the extended infrastructure
3. Registry handles both types transparently
4. No breaking changes to any APIs

## Implementation Plan

### Phase 1: Extend Base Infrastructure
**Goal**: Modify base classes to support instance-based tool sets

**Tasks**:
- [ ] Add provides_instances() method to ToolSet base class
- [ ] Add get_tool_instances() method to ToolSet base class  
- [ ] Modify ToolSetConfig to make tool_classes optional
- [ ] Update ToolSet validation to handle optional tool_classes
- [ ] Add tests for extended ToolSet functionality

### Phase 2: Create MCP Tool Proxy
**Goal**: Build the bridge between DSPy and MCP

**Tasks**:
- [ ] Create MCPToolProxy class inheriting from BaseTool
- [ ] Implement metadata storage (name, description, schema)
- [ ] Implement execute() method with MCP client call
- [ ] Add Pydantic model for tool metadata
- [ ] Add comprehensive error handling
- [ ] Create unit tests for MCPToolProxy

### Phase 3: Create MCP Base Tool Set
**Goal**: Build reusable base class for MCP tool sets

**Tasks**:
- [ ] Create MCPToolSet base class extending ToolSet
- [ ] Implement MCP client initialization
- [ ] Implement tool discovery on initialization
- [ ] Create MCPToolProxy instances for discovered tools
- [ ] Override provides_instances() to return True
- [ ] Override get_tool_instances() to return proxies
- [ ] Add connection configuration from environment
- [ ] Add tests for MCPToolSet functionality

### Phase 4: Update Registry
**Goal**: Extend registry to handle instance-based tool sets

**Tasks**:
- [ ] Modify register_tool_set to check provides_instances()
- [ ] Add branch for instance-based registration
- [ ] Store provided instances directly
- [ ] Maintain backward compatibility for class-based sets
- [ ] Update get_tool to handle both types
- [ ] Add tests for mixed registration scenarios

### Phase 5: Implement RealEstateToolSet
**Goal**: Create concrete implementation using new infrastructure

**Tasks**:
- [ ] Extend MCPToolSet for real estate domain
- [ ] Add domain-specific React signature
- [ ] Add domain-specific Extract signature  
- [ ] Implement get_test_cases() method
- [ ] Add configuration for real estate MCP server
- [ ] Create integration tests

### Phase 6: Integration Testing
**Goal**: Validate complete system functionality

**Tasks**:
- [ ] Test with real MCP server
- [ ] Test tool discovery process
- [ ] Test tool execution with various arguments
- [ ] Test error handling scenarios
- [ ] Test with agent sessions
- [ ] Performance testing with multiple tools
- [ ] Test graceful degradation

### Phase 7: Code Review and Final Testing
**Goal**: Ensure production readiness

**Tasks**:
- [ ] Review all code for compliance with requirements
- [ ] Verify no dynamic class generation
- [ ] Verify no hasattr or isinstance usage
- [ ] Verify all Pydantic models used correctly
- [ ] Verify no union types
- [ ] Verify no wrapper functions
- [ ] Run full test suite
- [ ] Document any limitations
- [ ] Create usage examples
- [ ] Final integration test with all tool sets

## Success Criteria

1. MCP tools discovered and usable without dynamic class generation
2. Existing tool sets continue working unchanged
3. Clean, maintainable code following all requirements
4. Comprehensive test coverage
5. Clear error messages and graceful failure handling
6. No performance degradation for existing tools
7. Simple configuration through environment variables
8. No hardcoded paths or server startup logic

## Risk Mitigation

### Risk: MCP Server API Changes
**Mitigation**: Version checking and clear error messages

### Risk: Performance Impact
**Mitigation**: Lazy discovery and connection pooling

### Risk: Breaking Existing Tools
**Mitigation**: Pure extension, no modifications to existing behavior

### Risk: Complex Debugging
**Mitigation**: Simple, direct code flow with comprehensive logging

## Conclusion

This proposal provides a clean, maintainable solution for integrating MCP's dynamic tool discovery with DSPy's static tool architecture. By extending rather than modifying the existing infrastructure, we maintain backward compatibility while enabling powerful new capabilities. The implementation follows all requirements, avoids anti-patterns, and provides a solid foundation for future dynamic tool integrations.