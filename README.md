# DSPy Agentic Loop Demo

A comprehensive example demonstrating how to use DSPy with an agentic loop architecture for multi-tool selection and execution. This project showcases a manually controlled React-style agent loop using DSPy's Chain-of-Thought reasoning, where we explicitly control the React → Extract workflow pattern. This architecture is designed to enable future integration with durable execution frameworks while maintaining full control over the reasoning and action selection process.

The implementation features:
- Type-safe tool registry with Pydantic models for structured input/output
- Manual control over the React (reason → act → observe) loop using DSPy
- Activity management for execution control and metrics
- Support for multiple LLM providers (Ollama, Claude, OpenAI, Gemini)
- Tool sets for different domains (e-commerce, events, treasure hunt, productivity)

## Quick Start

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- [Ollama](https://ollama.ai/) installed and running locally (or API keys for cloud providers)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/retroryan/dspy-system-prompt
cd dspy-system-prompt

# 2. Install dependencies
poetry install

# 3. Copy environment file
cp .env.sample .env
# Edit .env to add your API keys if using cloud providers

# 4. (Optional) For Ollama: pull the model
ollama pull gemma3:27b
```

### Run the Demo

```bash
# Run the React agent demo
poetry run python agentic_loop/demo_react_agent.py

# Run with debug mode to see DSPy prompts
DSPY_DEBUG=true poetry run python agentic_loop/demo_react_agent.py
```

## What is the Agentic Loop?

The agentic loop in this project demonstrates a manually controlled implementation of the React (Reason, Act, Observe) pattern using DSPy. Unlike typical ReAct implementations where the LLM generates interleaved thoughts and actions in a single prompt, we've decomposed the process into explicit, controllable steps:

1. **React Phase (Reasoning)**: The agent uses DSPy's Chain-of-Thought to analyze the user request, current state, and available tools to decide what action to take next
2. **Extract Phase (Action Selection)**: The reasoning output is extracted into structured tool calls that can be executed
3. **Observe Phase (Result Integration)**: Tool execution results are fed back into the conversation state for the next iteration

This manual control approach provides several advantages:
- **Durable Execution Ready**: Each phase can be checkpointed and resumed, making it suitable for integration with workflow engines like Temporal
- **Explicit State Management**: The conversation state is fully observable and can be persisted between executions
- **Fine-grained Control**: You can modify reasoning strategies, add custom validation, or inject business logic between phases
- **Debugging & Monitoring**: Clear separation of concerns makes it easier to debug issues and monitor agent behavior

The implementation uses:
- **AgentReasoner**: DSPy module that performs the reasoning step with Chain-of-Thought
- **ManualAgentLoop**: Orchestrates the React loop, converting reasoning into actions
- **ActivityManager**: External control layer that manages iterations, timeouts, and metrics

This architecture is specifically designed to bridge the gap between LLM reasoning and production systems that require reliability, observability, and durability.

## Detailed Usage

### E-commerce Tool Set

The e-commerce tool set provides tools for online shopping scenarios:

```bash
# Run e-commerce demo
poetry run python agentic_loop/demo_react_agent.py

# Example interactions:
# - "Search for laptops under $1000"
# - "Add the first laptop to my cart"
# - "Track order #12345"
# - "Return the laptop from order #12345"
```

Available tools:
- `search_products`: Search for products by query and filters
- `add_to_cart`: Add items to shopping cart
- `list_orders`: View customer orders
- `get_order`: Get details of a specific order
- `track_order`: Track shipping status
- `return_item`: Process returns

### Events Tool Set

The events tool set provides tools for event management:

```bash
# Run with events tools
poetry run python agentic_loop/demo_react_agent.py

# Example interactions:
# - "Find tech events in San Francisco"
# - "Create a team meeting for next Monday at 2pm"
# - "Cancel the event with ID EVT-123"
```

Available tools:
- `find_events`: Search for events by type, location, and date
- `create_event`: Create new events with details
- `cancel_event`: Cancel existing events

### Output and Results

The demo provides:
- Real-time execution progress with reasoning traces
- Tool execution results and state updates
- Performance metrics for each iteration
- Visual progress indicators
- JSON results saved to `test_results/` directory

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

## Testing

### Unit Tests
```bash
# Test individual components
poetry run pytest tests/test_phase3_manual_agent_loop.py -v
poetry run pytest tests/test_phase4_activity_manager.py -v
```

### Integration Tests
```bash
# Test full workflows
poetry run pytest integration_tests/test_simple_workflow.py -v
poetry run pytest integration_tests/test_full_workflow.py -v
```

## Troubleshooting

- **Ollama not running**: Start with `ollama serve`
- **Model not found**: Pull with `ollama pull gemma3:27b`
- **Import errors**: Ensure you're using `poetry run` or activated the virtual environment
- **API key errors**: Check your `.env` file has the correct API keys
- **Timeout errors**: Increase `AGENT_TIMEOUT_SECONDS` in `.env`

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