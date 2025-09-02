# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Goals & Objectives

**IMPORTANT: Claude must always follow these goals and principles when working on this codebase.**

1. **Session-Based Architecture**: Use `AgentSession` as THE single entry point for all agent interactions
2. **Always-On Conversation History**: Context management is automatic and non-optional
3. **One Way to Do Everything**: No wrappers, no multiple APIs, just `session.query()`
4. **Unified Demo Runner**: All demos go through `demo_runner.py` - no duplication
5. **Plain Pydantic I/O**: Use simple Pydantic models for structured input and output
6. **Follow Best Practices**: Adhere to DSPy's emphasis on synchronous-only development
7. **No Unnecessary Complexity**: Avoid async patterns, complex abstractions, or heavy frameworks

## Key Principles

Claude must adhere to these principles:

- **Synchronous-Only**: All code is synchronous for clarity and simplicity
- **API Server is Fully Sync**: The API server and frontend must be completely synchronous
- **Always use `dspy.ChainOfThought`**: For improved reasoning in the agentic loop
- **Type Safety**: Pydantic models provide clear data structures
- **Minimal Dependencies**: Just DSPy, Pydantic, and python-dotenv
- **Easy to Understand**: The entire implementation can be grasped in minutes
- **No Workarounds or Hacks**: Never implement compatibility layers, workarounds, or hacks. Always ask the user to handle edge cases, version conflicts, or compatibility issues directly
- **Leverage LLM Intelligence**: Never create coordinate databases or mappings. The whole point of using an LLM is that it's smart enough to know geographic coordinates and extract them from place names
- **Preserve Custom React Implementation**: The custom React implementation provides manual control over each iteration, external tool execution, and detailed observability. **Never suggest replacing it with DSPy's built-in ReAct**
- **Preserve Tool Integration System**: The current tool system with `BaseTool`, `ToolArgument`, and the registry pattern must be preserved. It provides type safety, validation, test cases, and external execution control

**IMPORTANT: If there is a question about something or a request requires a complex hack, always ask the user before implementing. Maintain simplicity over clever solutions.**

## Complete Cut-Over Requirements

**CRITICAL: ALL CHANGES MUST FOLLOW THESE REQUIREMENTS**

When making any changes to the codebase:

* **ALWAYS FIX THE CORE ISSUE!**
* **COMPLETE CHANGE**: All occurrences must be changed in a single, atomic update
* **CLEAN IMPLEMENTATION**: Simple, direct replacements only
* **NO MIGRATION PHASES**: Do not create temporary compatibility periods
* **NO PARTIAL UPDATES**: Change everything or change nothing
* **NO COMPATIBILITY LAYERS**: Do not maintain old and new paths simultaneously
* **NO BACKUPS OF OLD CODE**: Do not comment out old code "just in case"
* **NO CODE DUPLICATION**: Do not duplicate functions to handle both patterns
* **NO WRAPPER FUNCTIONS**: Direct replacements only, no abstraction layers
* **DO NOT CALL FUNCTIONS ENHANCED or IMPROVED**: Do not create separate ImprovedPropertyIndex - update the actual PropertyIndex
* **ALWAYS USE PYDANTIC**: Use Pydantic models for all data structures
* **USE MODULES AND CLEAN CODE!**
* **Never name things after phases or steps**: No test_phase_2_bronze_layer.py etc.
* **if hasattr should never be used**: And never use isinstance
* **Never cast variables**: No variable casting, casting variable names, or adding variable aliases
* **If you are using a union type something is wrong**: Go back and evaluate the core issue
* **If it doesn't work don't hack and mock**: Fix the core issue
* **If there are questions please ask**: Update with the new API server and frontend

## Project Overview

This is a DSPy demo project that demonstrates an agentic loop architecture with:
- **Session-based interactions** via `AgentSession` 
- **Always-on conversation history** with sliding window memory management
- **Test case validation** with 22+ ecommerce scenarios including complex multi-step workflows
- **Performance metrics** tracking execution time, iterations, and tool usage
- **Two focused demos** showing complete agricultural and e-commerce workflows

## Key Commands

### Running Demos

```bash
# Two complete workflow demos
./run_demo.sh agriculture            # Complete farming workflow (weather → planting decision)
./run_demo.sh ecommerce             # Complete shopping workflow (orders → checkout)
```

Each demo tells a complete, realistic story that naturally demonstrates:
- Tool usage and integration
- Context building across queries  
- Memory management and conversation continuity
- Real-world workflows and decision-making

### Development Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run with debug output  
export DSPY_DEBUG=true
./run_demo.sh ecommerce
```

## Architecture Overview

### Core Components

1. **agentic_loop/session.py**: `AgentSession` class - THE single entry point
   - Manages conversation history automatically
   - Provides context to React and Extract agents
   - Returns type-safe `SessionResult` objects
   - **This is THE way to interact with agents**

2. **agentic_loop/core_loop.py**: Core React loop implementation
   - `run_react_loop()`: Executes the React pattern with context
   - `extract_final_answer()`: Synthesizes final answer from trajectory
   - Requires `context_prompt` parameter (always-on context)

3. **agentic_loop/react_agent.py**: Custom React implementation
   - Uses `dspy.Predict` for tool selection
   - Accepts conversation context
   - Returns structured output: thought, tool_name, tool_args

4. **agentic_loop/demos/**: Simple focused demos
   - `agriculture_demo.py`: Complete farming workflow demonstration
   - `ecommerce_demo.py`: Complete shopping workflow demonstration
   - Each demo shows realistic usage with natural context building

5. **shared/conversation_history.py**: Conversation history management
   - Automatic sliding window with configurable size
   - Intelligent summarization of older trajectories
   - Memory-efficient scaling for long conversations

6. **shared/trajectory_models.py**: Type-safe trajectory tracking
   - Pydantic models for steps, observations, and trajectories
   - Metadata field for conversation tracking
   - Clean separation of concerns

### Key Design Patterns

1. **Session-Based Architecture**:
   ```python
   session = AgentSession("ecommerce")
   result = session.query("Find laptops")
   # That's it - context, history, everything is automatic
   ```

2. **Always-On Context**: 
   - No conditional context handling
   - Every query has context (empty string for first query)
   - Simplifies the entire codebase

3. **Unified Demo Runner**:
   - One `DemoRunner` class for all demo types
   - No duplicate implementations
   - Consistent interface across all modes

4. **Type Safety Throughout**:
   - Pydantic models for all data structures
   - `SessionResult` for query responses
   - `Trajectory` for execution tracking

## Development Guidelines

### Code Search Best Practices

**IMPORTANT**: When searching the codebase, always exclude the `.venv` directory:
- Use `--glob "!.venv/**"` with Grep
- Focus searches on: `agentic_loop/`, `tools/`, `shared/`

### Working with the Agentic Loop

1. **All interactions go through AgentSession**:
   - Never create React agents directly
   - Never call core_loop functions directly
   - Always use `session.query()`

2. **Adding New Tools**:
   - Create tool class inheriting from `BaseTool`
   - Add to tool set class in `tools/*/tool_set.py`
   - Include test cases with expected tools

3. **Creating Test Cases**:
   - Use `ToolSetTestCase` in tool set's `get_test_cases()`
   - Specify `expected_tools` for validation
   - Include both basic and complex scenarios

4. **Modifying the Demo Runner**:
   - All changes in `demo_runner.py`
   - Maintain support for all modes (test, query, basic, conversation, memory)
   - Keep the unified architecture

## Configuration

Environment variables in `.env`:
- `DSPY_PROVIDER`: LLM provider (ollama, claude, openai, gemini)
- `OLLAMA_MODEL`: Ollama model to use (default: gemma3:27b)
- `LLM_TEMPERATURE`: Generation temperature (default: 0.7)
- `LLM_MAX_TOKENS`: Maximum tokens (default: 1024)
- `DSPY_DEBUG`: Enable debug output
- `DEMO_VERBOSE`: Enable verbose demo output

## Test Results and Metrics

When running test cases with `--verbose`:
- **Iteration details**: Thought, tool selection, execution time
- **Tool validation**: Compares actual vs expected tools
- **Performance metrics**: Total time, average per test
- **Success tracking**: Pass/fail rates for test suites

## Important Implementation Details

### Conversation History is Always On
- Not optional, not configurable in core_loop
- `context_prompt` parameter is required (can be empty string)
- Simplifies the entire architecture

### No Duplicate React Loops
- ONE implementation in `core_loop.py`
- Used by `AgentSession` for all interactions
- Never create alternate implementations

### Simple Demo System
- Two focused demos: agriculture and ecommerce
- Single entry point via `run_demo.sh`
- Each demo is a simple, standalone Python script

### Workflow Demonstrations
- Complete agricultural workflow (weather analysis → planting decisions)
- Complete e-commerce workflow (order history → checkout)
- Natural context building and memory management
- Run with: `./run_demo.sh agriculture` or `./run_demo.sh ecommerce`

## Common Pitfalls to Avoid

1. **Don't create wrapper functions** - Use AgentSession directly
2. **Don't make context optional** - It's always-on by design
3. **Don't duplicate demo code** - Use the unified runner
4. **Don't create alternate React loops** - Use the one in core_loop
5. **Don't add async code** - Keep everything synchronous
6. **Don't create coordinate mappings** - LLMs know geography
7. **Don't replace custom React** - We need the manual control
8. **Don't simplify the tool system** - Type safety is essential

## Current State Summary

The codebase now has:
- **ONE React loop** in `core_loop.py`
- **ONE way to interact** via `AgentSession.query()`
- **TWO focused demos** showing complete workflows
- **Always-on conversation history** (no conditionals)
- **Realistic workflow demonstrations** with agriculture and e-commerce
- **Natural context building** through connected queries
- **Ultra-simple architecture** with no complex demo infrastructure

This is the final, clean state that should be maintained.