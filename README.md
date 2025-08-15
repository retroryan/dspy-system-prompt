# DSPy Agentic Loop Demo

A comprehensive example demonstrating how to use DSPy with an agentic loop architecture for multi-tool selection and execution. This project showcases a manually controlled React-style agent loop using DSPy's Chain-of-Thought reasoning, where we explicitly control the React → Extract workflow pattern with always-on conversation history management.

The implementation features:
- **Session-based architecture** with `AgentSession` as the single entry point for all agent interactions
- **Always-on conversation history** with automatic context management and sliding window memory
- **Unified demo runner** supporting test cases, custom queries, and interactive demos
- **Type-safe tool registry** with Pydantic models for structured input/output
- **Manual control** over the React (reason → act → observe) loop using DSPy
- **Performance metrics** tracking execution time, iterations, and tool usage
- **Support for multiple LLM providers** (Ollama, Claude, OpenAI, Gemini)
- **Tool sets for different domains** (agriculture/weather, e-commerce with 22 test cases, events)

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

The project provides a unified `run_demo.sh` script that supports multiple modes:

#### Test Mode (Default) - Run Predefined Test Cases

```bash
# Run all test cases for a tool set
./run_demo.sh                        # Agriculture test cases (default)
./run_demo.sh ecommerce              # All 22 ecommerce test cases
./run_demo.sh events                 # Events test cases

# Run specific test case
./run_demo.sh ecommerce 13           # Complex multi-step purchase scenario
./run_demo.sh agriculture 5          # Specific agriculture test

# With verbose output (shows agent thoughts and iterations)
./run_demo.sh --verbose ecommerce 2
./run_demo.sh -v ecommerce 13        # See detailed reasoning for complex scenario
```

#### Query Mode - Custom Queries

```bash
# Run custom queries
./run_demo.sh --query agriculture "What's the weather in NYC?"
./run_demo.sh -q ecommerce "Find laptops under $1000"
echo "Track order 12345" | ./run_demo.sh --query ecommerce

# With verbose output
./run_demo.sh --verbose --query ecommerce "Compare gaming keyboards"
```

#### Demo Modes - Interactive Demonstrations

```bash
# Basic single-query demos
./run_demo.sh basic                  # Agriculture tools (default)
./run_demo.sh basic ecommerce        # Ecommerce tools
./run_demo.sh basic events           # Events tools

# Conversation demo (multi-turn with context)
./run_demo.sh conversation           # Agriculture (default)
./run_demo.sh conversation ecommerce # Ecommerce context demo

# Memory management demo (sliding window)
./run_demo.sh memory                 # Shows memory management in action
```

#### Options

```bash
--verbose, -v    Show detailed agent thoughts, tool execution, and iteration details
--debug, -d      Enable full DSPy debug output (very verbose!)
--help, -h       Show comprehensive help with all options
```

### Important Notes

**DSPy Warning**: You may see warnings like:
```
WARNING dspy.predict.predict: Not all input fields were provided to module. Present: ['user_query', 'trajectory']. Missing: ['conversation_context'].
```
This is expected behavior when the conversation context is empty (e.g., for the first query in a session). The warning comes from DSPy's internal validation and can be safely ignored - the system handles empty context correctly.

## Architecture Overview

### Session-Based Architecture

The project uses `AgentSession` as the single, unified interface for all agent interactions:

```python
from agentic_loop.session import AgentSession

# Create a session - always-on conversation history
session = AgentSession("ecommerce")

# Simple, consistent API
result = session.query("Find laptops under $1000")
print(f"Answer: {result.answer}")
print(f"Time: {result.execution_time:.2f}s")
print(f"Tools used: {', '.join(result.tools_used)}")
```

**Key Benefits:**
- **ONE way to interact** - no multiple APIs or wrappers
- **Automatic context management** - conversation history just works
- **Type-safe results** - `SessionResult` provides structured output
- **Memory management** - sliding window with intelligent summarization

### The Agentic Loop

The agentic loop implements the React → Extract → Observe pattern with manual control:

```
User Query
    ↓
┌─────────────────────────────────────┐
│ AgentSession                        │
│ - Manages conversation history      │
│ - Provides context to agents        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ React Phase (ReactAgent)            │
│ - Uses dspy.Predict                 │
│ - Considers conversation context    │
│ - Returns: thought, tool, args      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ External Tool Execution             │
│ - Execute selected tool             │
│ - Add results to trajectory         │
│ - Continue or finish?               │
└─────────────────────────────────────┘
    ↓ (loop until "finish")
┌─────────────────────────────────────┐
│ Extract Phase                       │
│ - Uses dspy.ChainOfThought          │
│ - Synthesizes final answer          │
│ - Considers full context            │
└─────────────────────────────────────┘
    ↓
Final Answer
```

## Tool Sets and Test Cases

### Agriculture/Weather Tool Set
- **Tools**: Weather forecast, current conditions, historical data, agricultural conditions
- **Test Cases**: 9 scenarios including multi-city comparisons and planting recommendations

### E-commerce Tool Set (22 Test Cases)
- **Tools**: Product search, cart management, checkout, order tracking, returns
- **Basic Scenarios** (1-12): Simple operations like search, add to cart, track orders
- **Complex Scenarios** (13-22): 
  - Multi-step purchases with budget constraints
  - Comparative shopping with price optimization
  - Conditional returns based on order analysis
  - Cart recovery with inventory management
  - Personalized recommendations based on history

### Events Tool Set
- **Tools**: Event search, creation, cancellation
- **Test Cases**: Event planning and management scenarios

## Performance Features

When running with `--verbose`, the system provides detailed metrics:

- **Iteration Details**: See each step of the agent's reasoning
- **Tool Execution**: Track which tools were called and their results
- **Performance Metrics**: 
  - Execution time per iteration
  - Total completion time
  - Number of iterations used
  - Tools invoked and their sequence

## Advanced Features

### Conversation History Management

The system maintains conversation history automatically:
- **Sliding Window**: Configurable window size for active trajectories
- **Intelligent Summarization**: Older trajectories are summarized to preserve context
- **Memory Efficiency**: Scales to long conversations without memory explosion

### Test Case Validation

Test mode validates agent behavior:
- **Expected Tools**: Verify the agent uses the correct tools
- **Performance Tracking**: Monitor execution times across test cases
- **Success Metrics**: Track pass/fail rates for test suites

## Environment Variables

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DSPY_PROVIDER` | LLM provider (`ollama`, `claude`, `openai`) | `ollama` |
| `OLLAMA_MODEL` | Ollama model name | `gemma3:27b` |
| `LLM_TEMPERATURE` | Generation temperature | `0.7` |
| `LLM_MAX_TOKENS` | Maximum tokens | `1024` |
| `DSPY_DEBUG` | Show DSPy prompts/responses | `false` |
| `DEMO_VERBOSE` | Show detailed execution logs | `false` |

## Project Structure

```
.
├── agentic_loop/
│   ├── session.py           # AgentSession - THE way to interact with agents
│   ├── core_loop.py         # Core React loop implementation
│   ├── react_agent.py       # React agent with tool selection
│   ├── extract_agent.py     # Extract agent for answer synthesis
│   └── demos/
│       └── demo_runner.py   # Unified demo runner for all modes
├── shared/
│   ├── conversation_history.py  # Conversation history management
│   ├── trajectory_models.py     # Type-safe trajectory tracking
│   └── tool_utils/              # Tool registry and base classes
├── tools/
│   ├── ecommerce/           # E-commerce tool implementations
│   ├── precision_agriculture/  # Weather and agriculture tools
│   └── events/              # Event management tools
└── run_demo.sh              # Main demo runner script
```

## Development

### Adding New Tools

1. Create a tool class inheriting from `BaseTool`
2. Add to appropriate tool set in `tools/*/tool_set.py`
3. Include test cases with expected tools
4. Test with: `./run_demo.sh your_tool_set`

### Creating Custom Tool Sets

1. Subclass `ToolSet` in your tool directory
2. Define tool classes and test cases
3. Register in `demo_runner.py` TOOL_SETS
4. Test with the demo runner

## Troubleshooting

- **Ollama not running**: Start with `ollama serve`
- **Model not found**: Pull with `ollama pull gemma3:27b`
- **Import errors**: Ensure you're using `poetry run` or activating the virtual environment
- **API key errors**: Check your `.env` file has the correct API keys
- **Tool not found**: Verify tool set name is correct (agriculture, ecommerce, events)

## Next Steps

- Explore the 22 ecommerce test cases including complex scenarios
- Try verbose mode to understand agent reasoning: `./run_demo.sh --verbose ecommerce 13`
- Build multi-turn conversations with the conversation demo
- Create custom tool sets for your use case
- Integrate with durable execution frameworks like Temporal