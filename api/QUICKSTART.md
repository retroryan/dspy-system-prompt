# Quick Start Guide - Agentic Loop API

Get up and running with the Agentic Loop API in 5 minutes.

## Prerequisites

- Python 3.10+
- Poetry installed
- Git repository cloned

## Step 1: Install Dependencies

```bash
cd /path/to/dspy-system-prompt
poetry install
```

## Step 2: Configure Environment

Create a `.env` file with your LLM configuration:

```bash
# LLM Configuration (required for query execution)
# Option 1: OpenRouter (recommended for testing)
LLM_MODEL=openrouter/openai/gpt-4o-mini
OPENROUTER_API_KEY=your-api-key-here

# Option 2: Local Ollama
# LLM_MODEL=ollama_chat/llama3.2:3b
# OLLAMA_CHAT_API_BASE=http://localhost:11434

# Option 3: OpenAI
# LLM_MODEL=openai/gpt-4o-mini
# OPENAI_API_KEY=your-api-key-here

# API Configuration (optional)
API_PORT=8000
SESSION_TTL_MINUTES=30
QUERY_TIMEOUT_SECONDS=60
DEBUG_MODE=false
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024
```

## Step 3: Start the Server

```bash
./run_api.sh
```

The server will start at http://localhost:8000

## Step 4: Verify Installation

Open your browser and navigate to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Step 5: Your First API Call

### Using curl:
```bash
# Check server health
curl http://localhost:8000/health
```

### Using Python:
```python
import requests

# Check server health
response = requests.get("http://localhost:8000/health")
print(response.json())
```

## Step 6: Complete Workflow Example

Here's a complete example of creating a session and executing a query:

### 1. Create a Session
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "tool_set": "ecommerce",
    "user_id": "quickstart_user"
  }'
```

Save the `session_id` from the response.

### 2. Execute a Query
```bash
curl -X POST http://localhost:8000/sessions/YOUR_SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me laptops under $1000"
  }'
```

### 3. Clean Up
```bash
curl -X DELETE http://localhost:8000/sessions/YOUR_SESSION_ID
```

## Available Tool Sets

The API provides three specialized tool sets:

### 1. **E-commerce** (`ecommerce`)
- Order management
- Product search
- Shopping cart
- Checkout processing

**Example queries:**
- "Show me my recent orders"
- "Find gaming keyboards under $200"
- "Add item to cart"
- "Process checkout"

### 2. **Agriculture** (`agriculture`)
- Weather forecasting
- Soil analysis
- Crop recommendations
- Irrigation scheduling

**Example queries:**
- "What's the weather forecast?"
- "Check soil conditions"
- "What crops should I plant?"
- "Schedule irrigation"

### 3. **Events** (`events`)
- Event discovery
- Venue management
- Registration handling
- Schedule management

**Example queries:**
- "What events are this weekend?"
- "Find tech conferences"
- "Register for event"
- "Check venue availability"

## Python Client Example

For a more pythonic approach, use our example client:

```python
from api.examples.client_example import AgenticLoopClient

# Initialize client
client = AgenticLoopClient()

# Create session
session_id = client.create_session(
    tool_set="ecommerce",
    user_id="my_user"
)

# Execute query
result = client.query("Find the best laptop for programming")
print(f"Answer: {result['answer']}")
print(f"Tools used: {result['tools_used']}")

# Clean up
client.delete_session()
```

## Interactive Documentation

The API includes interactive Swagger documentation:

1. Navigate to http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out" to test the endpoint
4. Fill in the parameters
5. Click "Execute" to see the response

## Common Patterns

### Multi-turn Conversations
Sessions maintain context across queries:

```python
# First query
client.query("Show me gaming keyboards")

# Follow-up uses context
client.query("Compare the top 3 options")

# Another follow-up
client.query("Add the best one to my cart")
```

### Error Handling
```python
try:
    result = client.query("Your query here")
except requests.HTTPError as e:
    error = e.response.json()
    print(f"Error: {error['error']['message']}")
```

### Session Management
```python
# Create with custom config
session_id = client.create_session(
    tool_set="agriculture",
    user_id="farmer",
    max_messages=100,  # Keep more history
    summarize_removed=True  # Summarize old messages
)

# Reset conversation midway
client.reset_session()

# Delete when done
client.delete_session()
```

## Monitoring

### Check Server Metrics
```bash
curl http://localhost:8000/metrics
```

### View Logs
The server logs all requests and responses. Run with debug mode for detailed logs:

```bash
DEBUG_MODE=true ./run_api.sh
```

## Testing

### Run Unit Tests
```bash
# Run the unit test suite
poetry run python -m pytest api/tests -v
```

### Run Integration Tests
The integration tests validate the API against a live server with real LLM calls:

```bash
# Run all integration tests (starts server automatically)
./api/run_integration_tests.sh

# Run quick tests only (excludes slow tests)
./api/run_integration_tests.sh quick

# Run with verbose output
./api/run_integration_tests.sh verbose

# Run specific test categories
./api/run_integration_tests.sh workflows  # Test multi-step workflows
```

**Integration Test Coverage:**
- ✅ Conversation context preservation
- ✅ Pronoun resolution across queries
- ✅ Session reset functionality
- ✅ Long conversation handling (15+ queries)
- ✅ Cross-query state management
- ✅ Multi-step e-commerce workflows
- ✅ Agricultural planning workflows
- ✅ Error handling and validation
- ✅ Performance benchmarks

**Note:** Integration tests require a configured LLM (OpenRouter, Ollama, etc.) in your `.env` file.

### Run Client Examples
```bash
# Full client example with all features
python api/examples/client_example.py
```

## Troubleshooting

### Server Won't Start
- Check if port 8000 is already in use
- Verify poetry dependencies are installed
- Check Python version (3.10+ required)

### Session Expired
- Sessions expire after 30 minutes by default
- Create a new session or adjust `SESSION_TTL_MINUTES`

### Query Timeout
- Complex queries may timeout (default 60s)
- Increase `QUERY_TIMEOUT_SECONDS` if needed
- Simplify queries or reduce `max_iterations`

### Connection Refused
- Ensure server is running: `./run_api.sh`
- Check firewall settings
- Verify correct host/port

### Integration Tests Failing
- Verify LLM is configured in `.env` file
- Check API key is valid and has credits
- For OpenRouter: Ensure API key has access to the model
- For Ollama: Ensure Ollama is running and model is pulled
- Run with verbose mode for detailed output: `./api/run_integration_tests.sh verbose`

## Next Steps

1. **Explore the API**: http://localhost:8000/docs
2. **Read Examples**: `api/examples/`
3. **Review Models**: `api/models.py`
4. **Customize Config**: `api/utils/config.py`

## Support

For issues or questions:
1. Check the [API documentation](http://localhost:8000/docs)
2. Review [curl examples](api/examples/curl_examples.md)
3. See [client examples](api/examples/client_example.py)
4. Read the [full documentation](API.md)