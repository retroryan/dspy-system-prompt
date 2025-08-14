# DSPy Agentic Loop Demo

A comprehensive example demonstrating how to use DSPy with an agentic loop architecture for multi-tool selection and execution. This project showcases a manually controlled React-style agent loop using DSPy's Chain-of-Thought reasoning, where we explicitly control the React → Extract workflow pattern. This architecture is designed to enable future integration with durable execution frameworks while maintaining full control over the reasoning and action selection process.

The implementation features:
- Type-safe tool registry with Pydantic models for structured input/output
- Manual control over the React (reason → act → observe) loop using DSPy
- Activity management for execution control and metrics
- Support for multiple LLM providers (Ollama, Claude, OpenAI, Gemini)
- Tool sets for different domains (e-commerce, events, treasure hunt, productivity, weather)
- Weather tool set currently uses [Open Meteo](https://open-meteo.com/) (shout out for the great API!) with MCP server integration coming soon

## Quick Start

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- [Ollama](https://ollama.ai/) installed and running locally (or API keys for cloud providers)

### Setup

```bash
# 1. Install dependencies
poetry install

# 2. Copy environment file
cp .env.sample .env
# Edit .env to add your API keys if using cloud providers

# 3. (Optional) For Ollama: pull the model
ollama pull gemma3:27b
```

### Run the Demo

The project provides a unified `run_demo.sh` script that supports both test cases and custom queries:

```bash
# Run default test cases (agriculture tool set)
./run_demo.sh

# Run specific tool set test cases
./run_demo.sh ecommerce              # Run all e-commerce test cases
./run_demo.sh agriculture            # Run all agriculture test cases
./run_demo.sh events                 # Run all events test cases

# Run a specific test case
./run_demo.sh ecommerce 3            # Run test case #3 from e-commerce
./run_demo.sh agriculture 5          # Run test case #5 from agriculture

# Run custom queries
./run_demo.sh --query agriculture "What's the weather in NYC?"
./run_demo.sh --query ecommerce "Find laptops under $1000"
echo "Track order 12345" | ./run_demo.sh --query ecommerce

# Verbose mode (shows agent thoughts and tool execution details)
./run_demo.sh --verbose              # Verbose test cases
./run_demo.sh -v ecommerce          # Verbose e-commerce tests
./run_demo.sh --verbose --query agriculture "Compare weather in Tokyo and Paris"

# Debug mode (shows full DSPy prompts and LLM responses)
./run_demo.sh --debug                # Full debug output
./run_demo.sh -d --query ecommerce "Search for gaming keyboards"
```

### Conversation History Demo

The project includes a demonstration of conversation history management that shows how to maintain context across multiple interactions:

```bash
# Run the conversation demo (shows context awareness across queries)
poetry run python demo_conversation_history.py --demo conversation

# Run the memory management demo (shows sliding window in action)
poetry run python demo_conversation_history.py --demo memory
```

The conversation demo demonstrates:
- **Context awareness**: Later queries build on information from earlier ones
- **Intelligent summaries**: Extract agent creates summaries of removed trajectories
- **Memory management**: Sliding window maintains recent interactions
- **Clean integration**: Context passed as simple InputFields to existing agents

## What is the Agentic Loop?

The agentic loop in this project demonstrates a manually controlled implementation of the DSPy React pattern, where we explicitly separate the React, Extract, and Observe phases for maximum control over execution:

### Flow Diagram

```
User Query
    ↓
┌─────────────────────────────────────┐
│ React Phase (ReactAgent)            │
│ - Uses dspy.Predict                 │
│ - Returns: thought, tool_name, args │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ External Controller                 │
│ (demo_react_agent.py)               │
│ - Execute selected tool             │
│ - Add results to trajectory         │
│ - Decide: continue or finish?       │
└─────────────────────────────────────┘
    ↓ (if tool_name != "finish")
    ↑ (loop until "finish")
    ↓ (when "finish" selected)
┌─────────────────────────────────────┐
│ Extract Phase (ReactExtract)        │
│ - Uses dspy.ChainOfThought          │
│ - Analyzes complete trajectory      │
│ - Synthesizes final answer          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Observe Phase                       │
│ - Returns final observer output     │
└─────────────────────────────────────┘
    ↓
Final Answer
```

### React Phase (Tool Selection)
The React agent uses `dspy.Predict` to reason about the user's request and available tools, then returns:
- **next_thought**: The agent's reasoning about what to do next
- **next_tool_name**: Which tool to execute (or "finish" to complete the task)
- **next_tool_args**: Arguments for the selected tool in JSON format

The React phase builds a trajectory dictionary containing all thoughts, tool calls, and observations across iterations.

### External Tool Execution Control
Unlike traditional ReAct where tool execution happens inside the agent, the external controller (`demo_react_agent.py`) decides whether to:
- Execute the selected tool and add results to the trajectory
- Continue the React loop for another iteration
- Handle errors and timeouts
- Manage the overall workflow

### Extract Phase (Answer Synthesis)
After the React loop completes, the Extract agent uses `dspy.ChainOfThought` to:
- Analyze the complete trajectory of thoughts, tool calls, and results
- Synthesize a final answer based on all gathered information
- Provide reasoning for the final response

### Observe Phase (Final Output)
The Extract phase returns an observer that provides the final output, completing the React → Extract → Observe pattern.

### Key Advantages

This manual control approach provides several advantages:
- **Durable Execution Ready**: Each phase can be checkpointed and resumed, making it suitable for integration with workflow engines like Temporal
- **External Control**: The orchestrating code has full control over tool execution, error handling, and flow decisions
- **Explicit State Management**: The trajectory is fully observable and can be persisted between executions
- **Fine-grained Control**: You can inject business logic, validation, or custom handling between any step
- **Debugging & Monitoring**: Clear separation makes it easier to debug issues and monitor agent behavior

The implementation follows DSPy's React → Extract → Observe pattern but with external orchestration:
- **ReactAgent**: DSPy module that performs reasoning and tool selection using `dspy.Predict`
- **External Controller**: Manages the loop, executes tools, and decides when to continue or finish
- **ReactExtract**: DSPy module that synthesizes final answers using `dspy.ChainOfThought`
- **Observer**: Final output phase that returns the completed result

This architecture bridges the gap between LLM reasoning and production systems that require reliability, observability, and durability.

## Detailed Usage

### Running Test Cases

Each tool set includes predefined test cases that demonstrate various scenarios:

```bash
# View all test cases for a tool set
./run_demo.sh ecommerce              # Shows all 22 test cases including complex scenarios
./run_demo.sh agriculture            # Shows all 9 weather-related test cases

# Run specific test cases
./run_demo.sh ecommerce 1            # Basic product search
./run_demo.sh ecommerce 13           # Complex multi-step purchase with budget
./run_demo.sh agriculture 7          # Multi-city weather comparison
```

### Running Custom Queries

Use the `--query` flag to run your own queries:

```bash
# Weather queries
./run_demo.sh --query agriculture "What's the weather forecast for Los Angeles this week?"
./run_demo.sh --query agriculture "Are conditions good for planting tomatoes in Chicago?"
./run_demo.sh --query agriculture "Compare the weather in Tokyo and Paris"

# E-commerce queries
./run_demo.sh --query ecommerce "Search for wireless headphones under $100"
./run_demo.sh --query ecommerce "Add product LAPTOP-15 to my cart"
./run_demo.sh --query ecommerce "Track order ORD-123"

# Complex e-commerce scenarios
./run_demo.sh --query ecommerce "I have a budget of $1500. Find and add a laptop and mouse to my cart"
./run_demo.sh --query ecommerce "Compare gaming keyboards under $150 and add the best one to cart"

# Event management queries
./run_demo.sh --query events "Find tech conferences in San Francisco next month"
./run_demo.sh --query events "Create a team meeting for next Friday at 2pm"
```

### Tool Sets Available

#### Agriculture/Weather Tool Set

Provides comprehensive weather information for agricultural and general use:

Available tools:
- `get_agricultural_conditions`: Current conditions with agricultural metrics (soil moisture, UV index)
- `get_weather_forecast`: Multi-day weather forecasts with temperature and precipitation
- `get_historical_weather`: Historical weather data for past date ranges

Example test scenarios:
- Weather forecasts with umbrella recommendations
- Agricultural planting condition assessments
- Multi-city weather comparisons
- Historical weather analysis

#### E-commerce Tool Set

Complete shopping and order management system:

Available tools:
- `search_products`: Search with filters (price, category, brand)
- `add_to_cart`: Add items with quantity management
- `get_cart`: View current cart contents
- `update_cart_item`: Modify quantities in cart
- `remove_from_cart`: Remove items from cart
- `clear_cart`: Empty the cart
- `checkout`: Complete purchase with shipping details
- `get_order`: Get specific order details
- `list_orders`: View order history
- `track_order`: Check shipping status
- `return_item`: Process returns with reasons

Example test scenarios (22 total):
- Basic: Product search, cart operations, order tracking
- Complex: Multi-step purchases with budgets, comparative shopping, conditional returns, inventory-aware cart optimization, gift shopping scenarios

#### Events Tool Set

Event planning and management:

Available tools:
- `find_events`: Search by type, location, and date range
- `create_event`: Create with title, date, location, and description
- `cancel_event`: Cancel with reason

Example test scenarios:
- Finding events by location and type
- Creating events with specific details
- Multi-step event planning workflows

### Output Modes

#### Standard Output
By default, shows only the final answer:
```bash
./run_demo.sh --query agriculture "What's the weather in NYC?"
# Output: Current conditions and forecast summary
```

#### Verbose Mode
Use `--verbose` or `-v` to see agent reasoning and tool execution:
```bash
./run_demo.sh --verbose --query ecommerce "Find laptops"
# Shows: Agent thoughts, tool selections, execution times, and results
```

#### Debug Mode  
Use `--debug` or `-d` for full DSPy prompts and LLM responses:
```bash
./run_demo.sh --debug agriculture
# Shows: Complete prompts, LLM responses, and internal processing
```

### Performance Metrics

Test results include:
- Execution time per iteration
- Total iterations used
- Tools invoked
- Success/failure status
- Tool matching validation (for test cases)

### Using Different LLM Providers

Configure your LLM provider in the `.env` file:

#### Ollama (Local - Default)
```bash
DSPY_PROVIDER=ollama
OLLAMA_MODEL=gemma3:27b
```

#### Claude (Anthropic)
```bash
DSPY_PROVIDER=claude
ANTHROPIC_API_KEY=your-api-key-here
```

#### OpenAI
```bash
DSPY_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

## Python API Usage

You can also use the modules directly in Python:

```python
from agentic_loop.run_query import run_query

# Run a custom query
run_query(
    query="What's the weather in Paris?",
    tool_set_name="agriculture",
    max_iterations=10
)
```

```python
from agentic_loop.demo_react_agent import run_test_cases

# Run test cases programmatically
run_test_cases(tool_set_name="ecommerce", test_case_index=3)
```

## Troubleshooting

- **Ollama not running**: Start with `ollama serve`
- **Model not found**: Pull with `ollama pull gemma3:27b`
- **Import errors**: Ensure you're using `poetry run` or `./run_demo.sh`
- **API key errors**: Check your `.env` file has the correct API keys
- **Timeout errors**: Increase `AGENT_TIMEOUT_SECONDS` in `.env`
- **Tool not found**: Verify tool set name is correct (agriculture, ecommerce, events)

## Environment Variables

See `.env.sample` for all available configuration options. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DSPY_PROVIDER` | LLM provider (`ollama`, `claude`, `openai`) | `ollama` |
| `OLLAMA_MODEL` | Ollama model name | `gemma3:27b` |
| `LLM_TEMPERATURE` | Generation temperature | `0.7` |
| `LLM_MAX_TOKENS` | Maximum tokens | `1024` |
| `DSPY_DEBUG` | Show DSPy prompts/responses | `false` |
| `AGENT_MAX_ITERATIONS` | Maximum agent loop iterations | `5` |
| `AGENT_TIMEOUT_SECONDS` | Maximum execution time | `60.0` |

## Next Steps

- Explore different tool sets and their capabilities
- Create custom tools for your use case
- Experiment with different LLM providers
- Integrate with durable execution frameworks
- Build complex multi-step workflows