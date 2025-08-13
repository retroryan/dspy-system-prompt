# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Goals & Objectives

**IMPORTANT: Claude must always follow these goals and principles when working on this codebase.**

1. **Maximum Simplicity**: Create the most basic possible synchronous example of using DSPy with agentic loops
2. **Agentic Loop Focus**: Demonstrate how agents can reason, select tools, and iterate to complete tasks
3. **Plain Pydantic I/O**: Use simple Pydantic models for structured input and output
4. **Follow Best Practices**: Adhere to DSPy's emphasis on synchronous-only development
5. **No Unnecessary Complexity**: Avoid async patterns, complex abstractions, or heavy frameworks

## Key Principles

Claude must adhere to these principles:

- **Synchronous-Only**: All code is synchronous for clarity and simplicity
- **Always use `dspy.ChainOfThought`**: For improved reasoning in the agentic loop
- **Type Safety**: Pydantic models provide clear data structures
- **Minimal Dependencies**: Just DSPy, Pydantic, and python-dotenv
- **Easy to Understand**: The entire implementation can be grasped in minutes
- **No Workarounds or Hacks**: Never implement compatibility layers, workarounds, or hacks. Always ask the user to handle edge cases, version conflicts, or compatibility issues directly
- **Leverage LLM Intelligence**: Never create coordinate databases or mappings. The whole point of using an LLM is that it's smart enough to know geographic coordinates and extract them from place names. Creating explicit city-to-coordinate mappings is an anti-pattern that adds unnecessary complexity and defeats the purpose of using an intelligent model

**IMPORTANT: If there is a question about something or a request requires a complex hack, always ask the user before implementing. Maintain simplicity over clever solutions.**

**IMPORTANT: Never implement workarounds, compatibility layers, or hacks to handle edge cases or version conflicts. Instead, always inform the user of the issue and ask them how they would like to proceed. This keeps the codebase clean and maintainable.**

## Project Overview

This is a DSPy demo project that demonstrates an agentic loop architecture for multi-tool selection and execution. The project showcases how AI agents can reason about tasks, select appropriate tools, execute them, and iterate based on results - all using DSPy's Chain-of-Thought reasoning with type-safe Pydantic models.

## Key Commands

### Development Commands

```bash
# Install dependencies (using Poetry)
poetry install

# Run the agentic loop evaluation
poetry run python -m agentic_loop.demo_react_agent

# Run with specific tool set
poetry run python -m agentic_loop.demo_react_agent agriculture

# Run tests
poetry run pytest

# Run integration tests with specific tools
poetry run python -m tools.precision_agriculture.test_weather
```

### Testing & Development

```bash
# Run with debug output to see DSPy prompts and LLM responses
export DSPY_DEBUG=true
poetry run python -m agentic_loop.demo_react_agent

# Run a simple workflow test
poetry run python -m agentic_loop.demo_react_agent ecommerce
```

## Architecture Overview

### Core Components

1. **agentic_loop/demo_react_agent.py**: Main demo script that orchestrates the React → Extract → Observe pattern with external control.

2. **agentic_loop/react_agent.py**: Core DSPy module implementing the React pattern:
   - Uses `dspy.Predict` for tool selection reasoning
   - Returns structured output with next_thought, next_tool_name, next_tool_args
   - Builds and maintains trajectory of all actions and observations

3. **agentic_loop/extract_agent.py**: DSPy module for final answer synthesis:
   - Uses `dspy.ChainOfThought` to analyze complete trajectory
   - Synthesizes coherent final answer from all tool results
   - Returns reasoning and final answer

4. **shared/models.py**: Core data models for the system:
   - `ToolCall`: Structure for tool invocation
   - `ToolExecutionResult`: Tool execution outcomes
   - `ToolTestCase`: Test case definitions for validation

5. **shared/tool_utils/registry.py**: Tool registry for managing available tools:
   - Dynamic tool registration
   - Type-safe tool execution
   - Error handling and validation

6. **shared/tool_utils/base_tool_sets.py**: Base classes for tool sets:
   - `ToolSet`: Base class for collections of related tools
   - `ToolSetTestCase`: Test case structure for tool sets
   - Provides test cases for validation

7. **Tool Sets** (in shared/tool_utils/):
   - `AgricultureToolSet`: Weather tools (current, forecast, historical)
   - `EcommerceToolSet`: Shopping tools (search, cart, orders, tracking)
   - `EventsToolSet`: Event management tools (find, create, cancel)

### Key Design Patterns

1. **React → Extract → Observe Pattern**: 
   - React agent reasons and selects tools iteratively
   - External controller executes tools and manages state
   - Extract agent synthesizes final answer from complete trajectory
   - Observer returns final result to user

2. **External Control**: The demo script maintains full control over:
   - Tool execution
   - Error handling
   - Iteration limits
   - State management

3. **Trajectory-Based State**: All reasoning, actions, and observations stored in a simple dictionary for full observability

4. **Type Safety**: Pydantic models ensure all data structures are validated and type-safe

5. **Tool Set Organization**: Related tools grouped into sets with their own test cases

### DSPy Concepts Used

- **dspy.Predict**: For React agent tool selection
- **dspy.ChainOfThought**: For Extract agent answer synthesis
- **Signatures**: Define input/output contracts
- **Pydantic Integration**: Type-safe structured outputs
- **Synchronous Execution**: Following DSPy best practices

## Development Guidelines

### Code Search Best Practices

**IMPORTANT**: When searching the codebase using tools like Grep, Glob, or Task, always exclude the `.venv` directory to avoid searching through Python system files and dependencies. This prevents:
- Slow search performance
- Irrelevant results from third-party packages
- Confusion between project code and system libraries

Use patterns like:
- `--glob "!.venv/**"` with Grep
- Exclude `.venv` in search paths
- Focus searches on project directories: `agentic_loop/`, `tools/`, `shared/`

### Working with the Agentic Loop

When working with the agentic loop:

1. **Adding New Tools**:
   - Create tool class inheriting from `BaseTool` in appropriate directory
   - Add to tool set class in `shared/tool_utils/`
   - Include test cases in the tool set

2. **Creating Tool Sets**:
   - Subclass `ToolSet` in `shared/tool_utils/`
   - Define tool classes and test cases
   - Register in `demo_react_agent.py` TOOL_SET_MAP

3. **Modifying the Loop**:
   - Keep external control in `demo_react_agent.py`
   - Maintain trajectory structure for observability
   - Use DSPy modules for all LLM interactions

4. **Testing**:
   - Each tool set includes test cases
   - Run demo with specific tool sets to validate
   - Use DSPY_DEBUG=true to see prompts and responses

## Configuration

The project uses environment variables configured in `.env`:
- `DSPY_PROVIDER`: LLM provider (ollama, claude, openai, gemini)
- `OLLAMA_MODEL`: The Ollama model to use (default: gemma3:27b)
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `LLM_TEMPERATURE`: Generation temperature (default: 0.7)
- `LLM_MAX_TOKENS`: Maximum tokens (default: 1024)
- `DSPY_DEBUG`: Enable debug output to see prompts and LLM responses

### Agent Loop Configuration
- `AGENT_MAX_ITERATIONS`: Maximum iterations for React loop (default: 5)
- `AGENT_TIMEOUT_SECONDS`: Timeout for agent execution (default: 60.0)

## Prerequisites

- Python 3.10+
- Poetry for dependency management
- Ollama installed and running locally (or API keys for cloud providers)
- Appropriate models pulled (e.g., `ollama pull gemma3:27b`)

## Test Results

Test results from demo runs are saved to `prompts_out/` directory with format:
`{tool_set}_extract_{iteration}_{timestamp}.json`

This directory contains execution traces for debugging and analysis.