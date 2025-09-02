# API Server Proposal for Agentic Loop

## Executive Summary

This proposal outlines the design and implementation of a FastAPI-based REST API server that exposes the agentic loop functionality to external clients. The API will provide a simple, stateless interface for interacting with the DSPy-based agent system, following the same patterns established in the demo applications while maintaining high quality and simplicity.

## Core Requirements

### Functional Requirements

1. **Session Management**
   - Create new agent sessions with specific tool sets
   - Execute queries within a session context
   - Maintain conversation history per session
   - Support session reset and cleanup
   - Session expiry and resource management

2. **Query Processing**
   - Accept natural language queries
   - Process queries through the agentic loop
   - Return structured responses with execution metadata
   - Support configurable iteration limits
   - Handle long-running queries gracefully

3. **Tool Set Support**
   - Support all existing tool sets (agriculture, ecommerce, events)
   - Allow tool set selection at session creation
   - Provide tool set discovery endpoint
   - Return tool usage information in responses

4. **Response Structure**
   - Return comprehensive execution results
   - Include answer, execution time, iterations, and tools used
   - Provide conversation context information
   - Support both synchronous and streaming responses

5. **Error Handling**
   - Graceful error responses with meaningful messages
   - Timeout handling for long-running queries
   - Resource limit enforcement
   - Clear validation error messages

### Non-Functional Requirements

1. **Simplicity**
   - Clean, intuitive API design
   - Minimal endpoints focused on core functionality
   - Clear request/response models
   - No unnecessary complexity

2. **Performance**
   - Efficient session management
   - Configurable timeouts
   - Resource pooling for LLM connections
   - Memory-efficient conversation history

3. **Observability**
   - Request/response logging
   - Execution metrics collection
   - Health check endpoints
   - Debug mode support

4. **Developer Experience**
   - Auto-generated OpenAPI documentation
   - Interactive API explorer (Swagger UI)
   - Clear error messages
   - Example requests in documentation

## API Design

### Endpoints

#### Core Endpoints

1. **POST /sessions**
   - Create a new agent session
   - Request: tool_set, user_id, config options
   - Response: session_id, session metadata

2. **POST /sessions/{session_id}/query**
   - Execute a query within a session
   - Request: query text, max_iterations
   - Response: answer, execution details, metadata

3. **GET /sessions/{session_id}**
   - Get session information and status
   - Response: session metadata, history summary

4. **DELETE /sessions/{session_id}**
   - Terminate and cleanup a session
   - Response: confirmation

5. **POST /sessions/{session_id}/reset**
   - Reset conversation history while keeping session
   - Response: confirmation

#### Utility Endpoints

6. **GET /tool-sets**
   - List available tool sets
   - Response: tool set names and descriptions

7. **GET /tool-sets/{name}**
   - Get detailed information about a tool set
   - Response: tools, capabilities, example queries

8. **GET /health**
   - Health check endpoint
   - Response: status, version, uptime

9. **GET /metrics**
   - Get server metrics
   - Response: request counts, average times, active sessions

### Request/Response Models

#### Session Creation Request
- tool_set: Name of the tool set to use (ecommerce, agriculture, events)
- user_id: Unique identifier for the user
- config: Optional conversation history configuration (max_messages, summarize_removed)

#### Session Creation Response
- session_id: Unique session identifier
- tool_set: The selected tool set
- user_id: The user identifier
- created_at: Session creation timestamp
- status: Session status (active, expired)

#### Query Request
- query: Natural language query text
- max_iterations: Maximum React loop iterations (optional, default 5)

#### Query Response
- answer: The synthesized answer from the agent
- execution_time: Total time in seconds
- iterations: Number of React iterations performed
- tools_used: List of tools that were executed
- conversation_turn: Current turn number in conversation
- had_context: Whether previous context was available
- session_id: Associated session identifier
- timestamp: Response timestamp

### Session Management Strategy

1. **In-Memory Storage**
   - Store active sessions in memory dictionary
   - Fast access for demo purposes
   - Simple implementation

2. **Session Lifecycle**
   - Sessions created on demand
   - Configurable TTL (default 30 minutes)
   - Automatic cleanup of expired sessions
   - Manual deletion supported

3. **Concurrency**
   - Thread-safe session access
   - Queue queries per session
   - Prevent concurrent modifications

## Implementation Plan

### Phase 1: Core Infrastructure ✅ COMPLETED

**Goal**: Set up the basic FastAPI application structure and foundational components.

**Todo List**:
- [x] Create project structure with api/ directory
- [x] Set up FastAPI application with CORS and middleware
- [x] Define Pydantic models for all request/response types
- [x] Implement basic error handling middleware
- [x] Create configuration management using environment variables
- [x] Set up logging infrastructure
- [x] Add health check endpoint
- [x] Create basic OpenAPI documentation configuration

**Implementation Summary**:
- Created clean modular structure with separate directories for routers, middleware, and utils
- Implemented comprehensive Pydantic models for all request/response types in `api/models.py`
- Built robust error handling with custom exceptions and standardized error responses
- Set up configuration management with environment variables and defaults
- Added request/response logging middleware with request IDs
- Implemented health and metrics endpoints
- FastAPI app configured with automatic OpenAPI documentation

### Phase 2: Session Management ✅ COMPLETED

**Goal**: Implement robust session management with lifecycle control.

**Todo List**:
- [x] Create SessionManager class for in-memory storage
- [x] Implement session creation with unique IDs
- [x] Add session retrieval and validation
- [x] Implement session expiry with TTL
- [x] Create background task for session cleanup
- [x] Add thread-safe session access
- [x] Implement session reset functionality
- [x] Create session deletion endpoint

**Implementation Summary**:
- Built comprehensive SessionManager with thread-safe operations
- Implemented SessionInfo container with lifecycle tracking
- Added automatic cleanup of expired sessions via background thread
- Created full session CRUD endpoints in sessions router
- Integrated with AgentSession from core agentic loop
- Added per-user session limits and TTL-based expiry
- Implemented session reset to clear conversation history

### Phase 3: Query Processing ✅ COMPLETED

**Goal**: Integrate the agentic loop and process queries through sessions.

**Todo List**:
- [x] Create query processor that uses AgentSession
- [x] Implement query routing to correct session
- [x] Add timeout handling for long queries
- [x] Create response builder from SessionResult
- [x] Implement error recovery for failed queries
- [x] Add query queueing per session
- [x] Create execution metrics collection
- [x] Add debug mode support for detailed logs

**Implementation Summary**:
- Built QueryProcessor with thread-safe query execution
- Implemented timeout handling using threading context manager
- Created queries router with POST endpoint for query execution
- Integrated directly with AgentSession.query() method
- Added session locking to prevent concurrent queries
- Implemented metrics tracking for query performance
- Added comprehensive error handling and recovery
- Created tools router for tool set discovery and information

### Phase 4: Tool Set Integration ✅ COMPLETED

**Goal**: Expose tool set functionality and information through the API.

**Todo List**:
- [x] Create tool set discovery endpoints
- [x] Implement tool set validation at session creation
- [x] Add tool usage tracking in responses
- [x] Create tool set documentation generator
- [x] Implement example query suggestions per tool set
- [x] Add tool set capability descriptions
- [x] Create tool execution visibility
- [x] Add tool error handling and reporting

**Implementation Summary**:
- Created tools router with GET /tool-sets endpoints
- Implemented tool set validation in SessionManager
- Tool usage automatically tracked in QueryResponse
- Added comprehensive tool set descriptions and examples
- Tool execution visible through QueryResponse.tools_used
- Error handling for invalid tool sets and tool execution failures

### Phase 5: Documentation and Examples ✅ COMPLETED

**Goal**: Create documentation and usage examples for the demo API.

**Todo List**:
- [x] Write basic API usage documentation
- [x] Create example client code in Python
- [x] Add curl command examples
- [x] Configure Swagger UI for interactive testing
- [x] Document all endpoints and responses
- [x] Create quick start guide

**Implementation Summary**:
- Created comprehensive Python client example with AgenticLoopClient class
- Built extensive curl examples documentation covering all endpoints
- Developed quick start guide with step-by-step instructions
- Enhanced Swagger UI configuration with proper tags and descriptions
- Improved root endpoint with navigation and quick start information
- Added README.md for API with architecture overview
- Created examples directory with executable demo scripts

### Phase 6: Code Review and Testing ✅ COMPLETED

**Goal**: Ensure code quality and demo readiness.

**Todo List**:
- [x] Write basic tests for all endpoints
- [x] Create integration test for complete workflow
- [x] Review error handling
- [x] Validate all response formats
- [x] Test session lifecycle
- [x] Test all tool sets with example queries
- [x] Review code for DSPy best practices
- [x] Ensure Pydantic models are properly used
- [x] Validate no async code per requirements
- [x] Check for proper type hints throughout
- [x] Perform final code review and cleanup

**Implementation Summary**:
- Created comprehensive test suite with 40+ test cases in test_endpoints.py
- Built pytest configuration with fixtures for session management
- Implemented test runner script with coverage options
- Verified all endpoints return correct response formats
- Validated session lifecycle including creation, query, reset, and deletion
- Tested all three tool sets with appropriate queries
- Confirmed synchronous-only implementation (async only in FastAPI middleware)
- Verified Pydantic models used throughout with proper validation
- Ensured proper type hints in all functions
- Code is clean, modular, and follows all CLAUDE.md requirements

### Phase 7: Advanced Features (Optional)

**Goal**: Add advanced features if time permits.

**Todo List**:
- [ ] Implement Server-Sent Events for streaming responses
- [ ] Add basic metrics endpoint
- [ ] Implement simple request logging
- [ ] Add basic rate limiting
- [ ] Create simple API key support

## Technical Architecture

### Component Structure

- **api/main.py**: FastAPI application entry point
- **api/core/**: Core business logic
  - models.py: Pydantic request/response models
  - sessions.py: Session management
  - query_processor.py: Query execution logic
- **api/routers/**: Endpoint routers
  - sessions.py: Session-related endpoints
  - queries.py: Query execution endpoints
  - tools.py: Tool set endpoints
  - health.py: Health and metrics endpoints
- **api/middleware/**: Middleware components
  - error_handler.py: Global error handling
  - logging.py: Request/response logging
- **api/utils/**: Utility modules
  - config.py: Configuration management
- **api/examples/**: Usage examples
  - client_example.py: Python client examples
  - curl_examples.md: Curl command reference
- **api/tests/**: Test suite
  - test_endpoints.py: Comprehensive endpoint tests
  - test_simple_demo.py: Simple demo tests

### Key Design Decisions

1. **Synchronous Processing**
   - All operations are synchronous per DSPy requirements
   - No async/await patterns
   - Simple, predictable execution flow

2. **Stateless API Design**
   - Sessions stored server-side
   - Clients only need session_id
   - Clean REST principles

3. **Direct AgentSession Usage**
   - No wrappers around AgentSession
   - Direct integration following demo patterns
   - Maintains simplicity

4. **Pydantic Throughout**
   - All request/response models use Pydantic
   - Type safety and validation
   - Auto-generated documentation

5. **In-Memory Session Storage**
   - Simple dictionary-based storage
   - Appropriate for demo purposes
   - Easy to extend if needed

## Error Handling Strategy

### Error Categories

1. **Validation Errors (400)**
   - Invalid request format
   - Missing required fields
   - Invalid parameter values

2. **Not Found Errors (404)**
   - Session not found
   - Tool set not found
   - Invalid endpoint

3. **Timeout Errors (408)**
   - Query execution timeout
   - LLM response timeout

4. **Server Errors (500)**
   - LLM connection failures
   - Tool execution errors
   - Unexpected exceptions

### Error Response Format

- error.code: Error code identifier (e.g., SESSION_NOT_FOUND)
- error.message: Human-readable error message
- error.details: Additional context and suggestions
- timestamp: When the error occurred

## Security Considerations

### Input Validation
- Sanitize all user inputs
- Validate query length limits
- Check session ID format
- Validate tool set names

### Resource Limits
- Maximum sessions per user
- Query rate limiting
- Maximum iterations per query
- Session timeout enforcement

### Authentication (Simplified)
- Optional API key support
- Basic rate limiting per key
- No complex auth for demo

## Performance Optimization

### Caching Strategy
- Cache tool set information
- Reuse LLM connections
- Session lookup optimization

### Resource Management
- Lazy loading of tool sets
- Efficient memory usage
- Background cleanup tasks

### Monitoring
- Request duration tracking
- LLM call metrics
- Memory usage monitoring
- Active session counting

## Deployment Considerations

### Development Setup
- Install dependencies: fastapi, uvicorn, python-multipart
- Run development server with uvicorn on port 8000

### Production Deployment
- Use Gunicorn with Uvicorn workers
- Configure appropriate timeouts
- Set up reverse proxy (nginx)
- Enable CORS for client access

### Environment Variables
- API_PORT: Server port (default 8000)
- API_HOST: Server host (default 0.0.0.0)
- SESSION_TTL_MINUTES: Session timeout (default 30)
- MAX_SESSIONS_PER_USER: Per-user limit (default 10)
- QUERY_TIMEOUT_SECONDS: Query timeout (default 60)
- DEBUG_MODE: Enable debug logging (default false)

## Success Metrics

1. **Functionality**
   - All endpoints working correctly
   - Sessions properly managed
   - Queries processed successfully

2. **Performance**
   - Average query response < 5 seconds
   - Session creation < 100ms
   - Health check < 50ms

3. **Reliability**
   - Graceful error handling
   - No memory leaks
   - Proper timeout handling

4. **Developer Experience**
   - Clear API documentation
   - Helpful error messages
   - Easy to test and debug

## Future Enhancements (Out of Scope)

These items are noted for potential future work but are explicitly out of scope for this demo implementation:

- Persistent session storage (Redis/database)
- WebSocket support for real-time updates
- Multi-tenant isolation
- Advanced authentication (OAuth, JWT)
- Horizontal scaling support
- Message queue integration
- Batch query processing
- Response caching layer

## Implementation Status

### ✅ COMPLETED - All Core Phases (1-6) Implemented

The API server has been successfully implemented with complete functionality, documentation, and testing:

**Completed Components:**
- ✅ **Phase 1: Core Infrastructure** - FastAPI app with middleware, error handling, and configuration
- ✅ **Phase 2: Session Management** - Full CRUD operations with TTL and cleanup
- ✅ **Phase 3: Query Processing** - Thread-safe execution with timeout handling
- ✅ **Phase 4: Tool Set Integration** - Discovery endpoints and validation
- ✅ **Phase 5: Documentation** - Comprehensive docs, examples, and quick start guide
- ✅ **Phase 6: Testing** - Complete test suite with 40+ test cases

**Key Files Created:**
- `api/main.py` - FastAPI application entry point
- `api/core/models.py` - Comprehensive Pydantic models
- `api/core/sessions.py` - Thread-safe session management
- `api/core/query_processor.py` - Query execution with timeouts
- `api/routers/` - All endpoint implementations (sessions, queries, tools, health)
- `api/middleware/` - Error handling and logging middleware
- `api/utils/config.py` - Environment-based configuration
- `api/examples/client_example.py` - Python client with full examples
- `api/examples/curl_examples.md` - Complete curl command reference
- `api/tests/test_endpoints.py` - Comprehensive test suite
- `api/tests/test_simple_demo.py` - Simple demo test script
- `api/QUICKSTART.md` - Quick start guide for developers
- `run_api.sh` - Server startup script
- `api/run_tests.sh` - Test runner script

**Architecture Highlights:**
- Clean modular structure with clear separation of concerns
- Direct integration with AgentSession (no wrappers)
- Thread-safe operations with proper locking
- Comprehensive error handling with custom exceptions
- Type safety throughout with Pydantic models
- Synchronous-only implementation per DSPy requirements

**To Run the API:**
- Install dependencies with poetry install
- Start the server with ./run_api.sh
- Access documentation at http://localhost:8000/docs

## Integration Testing Status

### ✅ COMPLETED - Phase 7: Integration Testing

Successfully implemented and executed comprehensive integration tests against the live API server:

**Test Infrastructure:**
- Created `api/integration_tests/` directory with comprehensive test suites
- Built `api/run_integration_tests.sh` script for automated server lifecycle management
- Configured DSPy with OpenRouter LLM for real query execution

**Test Coverage (21+ tests):**
- ✅ **Conversation Context**: Tests verify context preservation across queries
- ✅ **Pronoun Resolution**: Validates pronouns are resolved using conversation history
- ✅ **Session Reset**: Confirms reset clears conversation while maintaining session
- ✅ **Long Conversations**: Tests memory management with 15+ query sequences
- ✅ **Context Relevance**: Validates context helps with ambiguous queries
- ✅ **Cart State Persistence**: Tests e-commerce state across multiple queries
- ✅ **Multi-Step Workflows**: Validates complex agricultural planning workflows

**Key Achievements:**
- All tests execute with real LLM calls via OpenRouter API
- Proper tool selection and execution validated
- Context management working correctly across conversation turns
- Session state properly maintained throughout workflows
- Performance acceptable with API response times

## Conclusion

The API server implementation successfully provides a clean, simple interface to the agentic loop functionality while maintaining all core principles from the codebase. The implementation is modular, type-safe, and follows DSPy best practices without unnecessary complexity. With comprehensive integration testing now complete, the API is production-ready for demonstration and deployment.