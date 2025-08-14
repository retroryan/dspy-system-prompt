# DSPy Project Notes

## Quick Start

### Running Demos

```bash
# Install dependencies
poetry install

# Run agriculture demo (weather tools)
poetry run python -m agentic_loop.demo_react_agent agriculture

# Run ecommerce demo (shopping cart tools)
poetry run python -m agentic_loop.demo_react_agent ecommerce

# Run events demo (event management tools)
poetry run python -m agentic_loop.demo_react_agent events

# Run specific test case
poetry run python -m agentic_loop.demo_react_agent ecommerce 2
```

### Configuration

Set these environment variables in `.env`:

```bash
LLM_MODEL=openai/gpt-4o-mini  # Or anthropic/claude-3, ollama_chat/llama3.2, etc.
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024
```

## DSPy Documentation

For DSPy usage, patterns, and best practices, see the official documentation:
- **Official Docs**: https://dspy-docs.vercel.app/
- **GitHub**: https://github.com/stanfordnlp/dspy

## Project Architecture

This project uses a custom React implementation (not DSPy's built-in ReAct) to provide:
- Manual control over each iteration
- External tool execution with validation
- Type-safe trajectory management
- Full observability of the agent loop

See `CLAUDE.md` for architectural guidelines.