# Agentic Loop API

A clean, simple FastAPI-based REST API for interacting with the DSPy-based agentic loop.

## Quick Start

### 1. Install Dependencies

```bash
poetry install
```

### 2. Start the Server

```bash
# Using the run script
./run_api.sh

# Or directly with uvicorn
poetry run uvicorn api.main:app --reload
```

The server will start on http://localhost:8000

### 3. Explore the API

- **Interactive Documentation**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## API Workflow

### Basic Usage Example

```python
import requests

# 1. Create a session
session_response = requests.post("http://localhost:8000/sessions", json={
    "tool_set": "ecommerce",
    "user_id": "demo_user"
})
session_id = session_response.json()["session_id"]

# 2. Execute a query
query_response = requests.post(
    f"http://localhost:8000/sessions/{session_id}/query",
    json={
        "query": "Show me my recent orders",
        "max_iterations": 5
    }
)
answer = query_response.json()["answer"]
print(answer)

# 3. Clean up
requests.delete(f"http://localhost:8000/sessions/{session_id}")
```

## Key Endpoints

### Sessions
- `POST /sessions` - Create new session
- `GET /sessions/{session_id}` - Get session info
- `DELETE /sessions/{session_id}` - Delete session
- `POST /sessions/{session_id}/reset` - Reset conversation

### Queries
- `POST /sessions/{session_id}/query` - Execute query

### Tool Sets
- `GET /tool-sets` - List available tool sets
- `GET /tool-sets/{name}` - Get tool set details

### Health & Metrics
- `GET /health` - Health check
- `GET /metrics` - Server metrics

## Testing

Run the test suite:

```bash
# Start the server first
./run_api.sh

# In another terminal, run tests
python api/test_api.py
```

## Configuration

Set environment variables to configure the server:

- `API_PORT` - Server port (default: 8000)
- `API_HOST` - Server host (default: 0.0.0.0)
- `SESSION_TTL_MINUTES` - Session timeout (default: 30)
- `QUERY_TIMEOUT_SECONDS` - Query timeout (default: 60)
- `DEBUG_MODE` - Enable debug logging (default: false)

## Architecture

The API follows a clean, modular architecture:

- **api/main.py** - FastAPI application entry point
- **api/models.py** - Pydantic request/response models
- **api/sessions.py** - Session management
- **api/query_processor.py** - Query execution logic
- **api/routers/** - Endpoint implementations
- **api/middleware/** - Error handling and logging
- **api/utils/** - Configuration and utilities

## Design Principles

1. **Synchronous Only** - No async/await patterns per DSPy requirements
2. **Type Safety** - Pydantic models throughout
3. **Direct Integration** - Uses AgentSession directly, no wrappers
4. **Simple & Clean** - Minimal complexity for demo purposes
5. **Thread-Safe** - Proper locking for concurrent operations