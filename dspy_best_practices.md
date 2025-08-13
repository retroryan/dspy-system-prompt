# DSPy Best Practices

This document captures key learnings and best practices discovered while implementing DSPy-based systems, based on thorough analysis of the DSPy codebase and real-world implementation experience.

## Table of Contents
1. [Multi-Model Support](#multi-model-support)
2. [API Configuration](#api-configuration)
3. [Code Principles](#code-principles)
4. [Testing Strategies](#testing-strategies)
5. [Common Pitfalls](#common-pitfalls)

## Multi-Model Support

### Use DSPy's Native LiteLLM Integration

DSPy leverages LiteLLM internally, providing automatic support for 100+ LLM providers. The key insight is to use DSPy's native capabilities rather than building custom abstractions.

**✅ DO: Use provider/model format directly**
```python
import dspy

# Cloud providers - just the model string
llm = dspy.LM("openai/gpt-4o-mini")
llm = dspy.LM("anthropic/claude-3-opus-20240229")
llm = dspy.LM("gemini/gemini-1.5-pro")

# Local models - explicit api_base
llm = dspy.LM("ollama_chat/llama3.2", api_base="http://localhost:11434", api_key="")
```

**❌ DON'T: Create provider-specific handling**
```python
# Avoid this pattern
if provider == "ollama":
    llm = setup_ollama()
elif provider == "claude":
    llm = setup_claude()
# This adds unnecessary complexity
```

### Model String Format

DSPy uses a consistent `provider/model` format that maps directly to LiteLLM's conventions:

- **OpenAI**: `openai/gpt-4o-mini`
- **Anthropic**: `anthropic/claude-3-opus-20240229`
- **Google**: `gemini/gemini-1.5-pro`
- **Ollama Chat**: `ollama_chat/llama3.2`
- **Ollama Completion**: `ollama/llama3.2`
- **Cohere**: `cohere/command-r-plus`
- **Replicate**: `replicate/meta/llama-2-70b-chat`
- **OpenRouter**: `openrouter/<provider>/<model>` (e.g., `openrouter/google/palm-2-chat-bison`)

### Ollama-Specific Considerations

For Ollama models, use `ollama_chat` for chat models and `ollama` for completion models:

```python
# Chat models (most common)
llm = dspy.LM("ollama_chat/gemma3:27b", api_base="http://localhost:11434", api_key="")

# Completion models
llm = dspy.LM("ollama/codellama", api_base="http://localhost:11434", api_key="")
```

### OpenRouter Integration

OpenRouter provides access to multiple LLM providers through a single API endpoint. DSPy supports OpenRouter through LiteLLM's native integration:

```python
import dspy
import os

# Set your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "your-api-key"

# Use any model available on OpenRouter
llm = dspy.LM("openrouter/google/palm-2-chat-bison")
llm = dspy.LM("openrouter/anthropic/claude-3-opus")
llm = dspy.LM("openrouter/meta-llama/llama-3-70b-instruct")

# Optional: Set custom API base (defaults to https://openrouter.ai/api/v1)
os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

# Optional: Set site URL and app name for OpenRouter analytics
os.environ["OR_SITE_URL"] = "https://yourapp.com"
os.environ["OR_APP_NAME"] = "YourAppName"
```

**Key Benefits of OpenRouter:**
- Access to multiple providers with one API key
- Automatic fallback between models
- Built-in rate limiting and load balancing
- Cost tracking across different models

**Model Format:**
- Always use `openrouter/<provider>/<model>` format
- The provider name is extracted as `OPENROUTER` for environment variables
- Check [OpenRouter's model list](https://openrouter.ai/models) for available models

## API Configuration

### Environment Variable Patterns

DSPy automatically checks for provider-specific environment variables using the pattern `{PROVIDER}_API_KEY` and `{PROVIDER}_API_BASE`:

```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=sk-or-...

# API Base URLs (for local models or custom endpoints)
OLLAMA_CHAT_API_BASE=http://localhost:11434
OPENAI_API_BASE=https://custom-endpoint.com/v1
OPENROUTER_API_BASE=https://openrouter.ai/api/v1  # Optional, this is the default

# OpenRouter-specific optional settings
OR_SITE_URL=https://yourapp.com
OR_APP_NAME=YourAppName
```

### API Base Configuration

There are three ways to configure API base URLs, in order of precedence:

1. **Explicit parameter** (highest priority):
   ```python
   llm = dspy.LM("ollama_chat/llama3.2", api_base="http://localhost:11434")
   ```

2. **Environment variable** (automatic fallback):
   ```bash
   export OLLAMA_CHAT_API_BASE=http://localhost:11434
   ```

3. **LiteLLM defaults** (lowest priority)

### Key Discovery: Provider Name Extraction

DSPy extracts the provider name from the model string before the first `/`:
- `ollama_chat/llama3.2` → Provider: `OLLAMA_CHAT`
- `openai/gpt-4` → Provider: `OPENAI`
- `anthropic/claude-3` → Provider: `ANTHROPIC`
- `openrouter/google/palm-2` → Provider: `OPENROUTER`

This provider name is then used to construct environment variable names.

## Code Principles

### 1. Synchronous-Only Design

DSPy emphasizes synchronous operations for simplicity and debuggability:

```python
# ✅ Good: Synchronous operations
result = llm("What is the capital of France?")

# ❌ Avoid: Async patterns in core logic
# async def process():
#     result = await llm.acall(...)
```

### 2. Direct Use of dspy.LM

Always use `dspy.LM` directly rather than creating wrapper classes:

```python
# ✅ Good: Direct instantiation
llm = dspy.LM("openai/gpt-4o-mini", temperature=0.7)
dspy.configure(lm=llm)

# ❌ Avoid: Unnecessary wrapper classes
# class MyLLMWrapper:
#     def __init__(self, provider):
#         self.llm = self._setup_provider(provider)
```

### 3. Configuration via dspy.configure

Use `dspy.configure()` to set the default LM for all DSPy operations:

```python
import dspy

llm = dspy.LM("openai/gpt-4o-mini")
dspy.configure(lm=llm)  # Sets as default for all DSPy modules

# Now all DSPy modules use this LM
predictor = dspy.Predict("question -> answer")
```

### 4. Explicit is Better Than Implicit

Be explicit about configuration rather than hiding it:

```python
# ✅ Good: Explicit configuration
def setup_llm(model: str = None, **kwargs):
    model = model or os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    return dspy.LM(model=model, **kwargs)

# ❌ Avoid: Hidden magic
def setup_llm():
    # Automatically detecting and configuring based on hidden logic
    if check_ollama_running():
        return setup_ollama_automatically()
```

## Testing Strategies

### 1. Multi-Provider Testing

Test with different providers to ensure compatibility:

```python
def test_providers():
    providers = [
        ("openai/gpt-4o-mini", {}),
        ("anthropic/claude-3-opus", {}),
        ("ollama_chat/llama3.2", {"api_base": "http://localhost:11434"}),
    ]
    
    for model, kwargs in providers:
        llm = dspy.LM(model, **kwargs)
        result = llm("test", max_tokens=10)
        assert result  # Basic smoke test
```

### 2. Environment-Based Configuration

Use environment variables for easy provider switching:

```python
# .env.test.ollama
LLM_MODEL=ollama_chat/llama3.2
OLLAMA_CHAT_API_BASE=http://localhost:11434

# .env.test.openai
LLM_MODEL=openai/gpt-4o-mini
OPENAI_API_KEY=sk-test-key
```

### 3. Connection Testing

Always test the connection before running main logic:

```python
def setup_llm(model: str = None, **kwargs):
    llm = dspy.LM(model=model, **kwargs)
    
    # Test connection
    try:
        llm("test", max_tokens=5)
    except Exception as e:
        # Provide helpful error messages
        if "api_key" in str(e).lower():
            provider = model.split("/")[0]
            print(f"Missing API key for {provider}")
        raise
    
    return llm
```

## Common Pitfalls

### 1. Incorrect Ollama Model Prefix

**Problem**: Using `ollama/` instead of `ollama_chat/` for chat models.

```python
# ❌ Wrong - will fail for chat operations
llm = dspy.LM("ollama/gemma3:27b")

# ✅ Correct - for chat models
llm = dspy.LM("ollama_chat/gemma3:27b")
```

### 2. Missing API Base for Local Models

**Problem**: Forgetting to specify api_base for local models.

```python
# ❌ Wrong - will try to connect to default endpoint
llm = dspy.LM("ollama_chat/llama3.2")

# ✅ Correct - explicit api_base
llm = dspy.LM("ollama_chat/llama3.2", api_base="http://localhost:11434")
```

### 3. Provider-Specific Logic

**Problem**: Adding special cases for each provider.

```python
# ❌ Wrong - unnecessary complexity
if model.startswith("ollama/"):
    # Special handling for Ollama
    config["api_base"] = get_ollama_base()
elif model.startswith("anthropic/"):
    # Special handling for Anthropic
    config["special_param"] = get_anthropic_param()

# ✅ Correct - let DSPy/LiteLLM handle it
llm = dspy.LM(model, **config)  # DSPy handles provider differences
```

### 4. Not Using dspy.configure

**Problem**: Passing LM to every module individually.

```python
# ❌ Wrong - repetitive
llm = dspy.LM("openai/gpt-4")
predictor1 = dspy.Predict("q -> a", lm=llm)
predictor2 = dspy.ChainOfThought("q -> a", lm=llm)

# ✅ Correct - configure once
llm = dspy.LM("openai/gpt-4")
dspy.configure(lm=llm)
predictor1 = dspy.Predict("q -> a")  # Uses configured LM
predictor2 = dspy.ChainOfThought("q -> a")  # Uses configured LM
```

## Key Insights

### 1. LiteLLM Does the Heavy Lifting

DSPy delegates all provider-specific logic to LiteLLM. This means:
- No need to handle provider differences
- Automatic support for new providers
- Consistent interface across all models

### 2. Environment Variables Follow a Pattern

The pattern `{PROVIDER}_API_KEY` and `{PROVIDER}_API_BASE` is consistent:
- Provider name comes from model string (before `/`)
- Uppercase and underscores replace hyphens
- Examples: `OLLAMA_CHAT_API_BASE`, `OPENAI_API_KEY`

### 3. Simplicity Wins

The simpler the implementation, the better:
- Direct use of dspy.LM
- No custom abstractions
- Let DSPy handle the complexity

### 4. Synchronous by Design

DSPy's synchronous-only approach:
- Simplifies debugging
- Reduces complexity
- Makes code easier to understand
- Follows Python's "There should be one obvious way to do it"

## Recommended Setup Pattern

Here's the recommended pattern for setting up LLMs in DSPy projects:

```python
import os
import dspy
from pathlib import Path
from dotenv import load_dotenv

def setup_llm(model: str = None, **kwargs):
    """
    Simple, clean LLM setup following DSPy best practices.
    """
    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Get model from parameter or environment
    model = model or os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    
    # Build configuration
    config = {
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
        "num_retries": int(os.getenv("LLM_RETRIES", "3")),
        "cache": os.getenv("LLM_CACHE", "true").lower() == "true",
        **kwargs  # Allow overrides
    }
    
    # Create and configure
    llm = dspy.LM(model=model, **config)
    dspy.configure(lm=llm)
    
    return llm
```

This pattern:
- ✅ Uses DSPy's native capabilities
- ✅ Supports all providers automatically
- ✅ Allows environment configuration
- ✅ Permits explicit overrides
- ✅ Stays simple and maintainable

## Conclusion

The key to working effectively with DSPy is to embrace its design philosophy:
1. **Leverage built-in capabilities** - DSPy and LiteLLM handle the complexity
2. **Keep it simple** - Avoid unnecessary abstractions
3. **Be explicit** - Clear configuration is better than magic
4. **Trust the framework** - DSPy has been designed with best practices in mind

By following these practices, you can build robust, maintainable DSPy applications that work seamlessly across multiple LLM providers.