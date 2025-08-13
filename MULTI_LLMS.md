# Multi-LLM Support Improvement Suggestions

## Critical Goal

**IMPORTANT**: The goal is a **complete and total change** to the new approach. We will NOT add any compatibility wrappers, migration strategies, or backward compatibility layers. This is a clean break that fully embraces DSPy's native LiteLLM integration to maintain maximum simplicity.

## Executive Summary

After analyzing DSPy's sophisticated multi-model architecture and comparing it with the current `shared/llm_utils.py` implementation, I've identified several key areas for improvement. DSPy leverages LiteLLM as its underlying abstraction layer, providing seamless support for 100+ LLM providers while our current implementation uses hardcoded provider mappings. 

This document outlines a **two-phased approach**:
- **Phase 1 (Simple Demo)**: Complete replacement leveraging DSPy's native LiteLLM integration, synchronous-only, perfect for demos
- **Phase 2 (Future Production)**: Advanced features for production use cases

## Current State Analysis

### DSPy's Architecture Strengths

1. **Unified Provider Abstraction**: DSPy uses LiteLLM internally, which supports 100+ providers through a single unified interface
2. **Provider Discovery**: Automatic provider inference from model strings (e.g., "openai/gpt-4o", "anthropic/claude-3")
3. **Advanced Features**: Built-in support for callbacks, caching, retries, streaming, and async operations
4. **Provider-Specific Capabilities**: Extensible Provider class for fine-tuning, reinforcement learning, and model lifecycle management
5. **Comprehensive Error Handling**: Automatic retries with exponential backoff for transient failures
6. **Multi-Level Caching**: Disk cache, memory cache, and LiteLLM cache with configurable strategies

### Current Implementation Limitations

1. **Hardcoded Provider Logic**: Manual if/elif chains for each provider instead of leveraging DSPy's automatic routing
2. **Limited Provider Support**: Only 4 providers explicitly supported vs DSPy's 100+ through LiteLLM
3. **No Async Support**: Missing async capabilities that DSPy provides out-of-the-box
4. **Basic Error Handling**: Simple try/catch without retry logic or sophisticated error recovery
5. **Missed Optimization Opportunities**: Not utilizing DSPy's advanced caching and performance features
6. **No Extensibility**: No mechanism for adding custom providers or middleware

## Phase 1: Simple Demo Implementation (Synchronous-Only)

Following DSPy's best practices and the CLAUDE.md guidelines for **maximum simplicity** and **synchronous-only development**, Phase 1 focuses on a minimal, clean implementation that leverages DSPy's native capabilities without any unnecessary complexity.

### Phase 1 Goals
- ✅ **Maximum Simplicity**: One simple function, no abstractions
- ✅ **Synchronous-Only**: No async patterns per DSPy best practices
- ✅ **Leverage DSPy**: Use DSPy's built-in LiteLLM routing
- ✅ **Clean Break**: Complete replacement with no backward compatibility
- ✅ **100+ Provider Support**: Automatic support through LiteLLM

### Phase 1 Implementation

**Current Approach (Hardcoded):**
```python
# Current implementation with hardcoded provider logic
if provider == "ollama":
    llm = dspy.LM(model=f"ollama/{model}", ...)
elif provider == "claude":
    llm = dspy.LM(model=f"anthropic/{model}", ...)
# ... more hardcoded providers
```

**Phase 1 Simple Approach (Recommended):**
```python
def setup_llm(model: str = None, **kwargs) -> dspy.LM:
    """
    Simple setup that leverages DSPy's automatic provider routing.
    No complex abstractions, just direct DSPy usage.
    
    Args:
        model: Full model string like "openai/gpt-4o" or "anthropic/claude-3-opus"
               If None, reads from LLM_MODEL env var
        **kwargs: Additional parameters passed directly to dspy.LM
    
    Returns:
        Configured dspy.LM instance
    
    Examples:
        # Use environment variable
        llm = setup_llm()
        
        # Explicit model
        llm = setup_llm("openai/gpt-4o-mini")
        llm = setup_llm("anthropic/claude-3-opus-20240229")
        llm = setup_llm("ollama/gemma3:27b")
        llm = setup_llm("gemini/gemini-1.5-pro")
    """
    # Load environment variables
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Get model from parameter or environment
    model = model or os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    
    # Simple configuration from environment
    config = {
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
        "num_retries": int(os.getenv("LLM_RETRIES", "3")),
        "cache": os.getenv("LLM_CACHE", "true").lower() == "true",
        **kwargs  # Allow overrides
    }
    
    # Optional debug logging
    if os.getenv("DSPY_DEBUG", "false").lower() == "true":
        print(f"🤖 Setting up LLM: {model}")
        print(f"   Temperature: {config['temperature']}")
        print(f"   Max Tokens: {config['max_tokens']}")
    
    # Create and configure the LLM
    llm = dspy.LM(model=model, **config)
    dspy.settings.configure(lm=llm)
    
    return llm
```

### Required .env.example Changes

Complete replacement of `.env.example` with new format only:

```bash
# ============================================
# LLM CONFIGURATION
# ============================================
# Direct model specification (provider/model format)
# Examples:
#   - openai/gpt-4o-mini
#   - anthropic/claude-3-opus-20240229  
#   - ollama/gemma3:27b
#   - gemini/gemini-1.5-pro
#   - cohere/command-r-plus
#   - replicate/meta/llama-2-70b-chat
LLM_MODEL=openai/gpt-4o-mini

# LLM Generation Settings
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024
LLM_RETRIES=3
LLM_CACHE=true

# Ollama Base URL (only needed for Ollama models)
# OLLAMA_BASE_URL=http://localhost:11434

# ============================================
# API KEYS (required based on provider)
# ============================================
# OpenAI (required for openai/* models)
# OPENAI_API_KEY=your-openai-api-key-here

# Anthropic Claude (required for anthropic/* models)
# ANTHROPIC_API_KEY=your-claude-api-key-here

# Google Gemini (required for gemini/* models)
# GOOGLE_API_KEY=your-gemini-api-key-here

# Cohere (required for cohere/* models)
# COHERE_API_KEY=your-cohere-api-key-here

# Replicate (required for replicate/* models)
# REPLICATE_API_TOKEN=your-replicate-token-here

# ============================================
# DEBUG & MONITORING
# ============================================
# Debug Mode - Shows DSPy prompts and LLM responses
DSPY_DEBUG=false

# Agent Loop Configuration
AGENT_MAX_ITERATIONS=5
AGENT_TIMEOUT_SECONDS=60.0
```

### Phase 1 Benefits

1. **Immediate 100+ Provider Support**: All LiteLLM providers work automatically
2. **Cleaner Code**: Complete removal of 50+ lines of hardcoded provider logic
3. **Consistent Interface**: Same model string format as LiteLLM/DSPy docs
4. **Self-Documenting**: Model strings clearly show provider and model (e.g., "openai/gpt-4o")
5. **Easier Testing**: Switch providers by just changing model string
6. **Future-Proof**: New providers work automatically when LiteLLM adds them
7. **No Technical Debt**: Clean implementation with no legacy code to maintain

## Phase 2: Future Production Enhancements

**Note**: Phase 2 features are for future production use cases. They add complexity and should only be implemented when needed for specific requirements beyond demo purposes.

### 2.1 Advanced Caching Strategy

Leverage DSPy's multi-level caching system:

```python
from pathlib import Path
import dspy.clients

def configure_advanced_caching(
    cache_dir: Path = None,
    memory_cache_size: int = 1000,
    disk_cache_size_gb: int = 10
):
    """Configure DSPy's advanced caching system."""
    cache_dir = cache_dir or Path.home() / ".dspy_cache"
    
    dspy.clients.configure_cache(
        enable_disk_cache=True,
        enable_memory_cache=True,
        enable_litellm_cache=True,
        disk_cache_dir=cache_dir,
        memory_cache_size=memory_cache_size,
        disk_cache_size_gb=disk_cache_size_gb
    )
    
    # Configure cache invalidation strategy
    dspy.clients.cache.set_ttl(hours=24)  # Cache TTL
    dspy.clients.cache.set_max_age(days=7)  # Max cache age
```

### 2.2 Middleware and Callbacks

Implement a middleware system for cross-cutting concerns:

```python
from dspy.utils.callback import BaseCallback
from typing import Optional
import time

class LatencyCallback(BaseCallback):
    """Track and log LLM latency."""
    
    def on_request_start(self, request: Dict[str, Any]):
        request["_start_time"] = time.time()
    
    def on_request_end(self, request: Dict[str, Any], response: Any):
        latency = time.time() - request.pop("_start_time", 0)
        print(f"LLM latency: {latency:.2f}s")

class CostTrackingCallback(BaseCallback):
    """Track estimated costs across providers."""
    
    def __init__(self):
        self.total_cost = 0.0
        self.provider_costs = {}
    
    def on_request_end(self, request: Dict[str, Any], response: Any):
        # Extract cost from response metadata
        cost = getattr(response, "_hidden_params", {}).get("response_cost", 0)
        self.total_cost += cost
        
        model = request.get("model", "unknown")
        provider = model.split("/")[0] if "/" in model else "unknown"
        self.provider_costs[provider] = self.provider_costs.get(provider, 0) + cost

def create_llm_with_middleware(
    model: str,
    track_latency: bool = True,
    track_costs: bool = True,
    **kwargs
) -> dspy.LM:
    """Create LLM with optional middleware callbacks."""
    callbacks = []
    
    if track_latency:
        callbacks.append(LatencyCallback())
    if track_costs:
        callbacks.append(CostTrackingCallback())
    
    return dspy.LM(model=model, callbacks=callbacks, **kwargs)
```

### 2.3 Model Fallback and Load Balancing

Add resilience through fallback mechanisms:

```python
from typing import List, Optional
import random

class ResilientLLM:
    """LLM wrapper with fallback and load balancing capabilities."""
    
    def __init__(
        self, 
        primary_models: List[str],
        fallback_models: List[str] = None,
        load_balance: bool = False
    ):
        self.primary_llms = [dspy.LM(model=m) for m in primary_models]
        self.fallback_llms = [dspy.LM(model=m) for m in (fallback_models or [])]
        self.load_balance = load_balance
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """Execute with fallback logic."""
        # Try primary models
        models_to_try = self.primary_llms.copy()
        if self.load_balance:
            random.shuffle(models_to_try)
        
        for llm in models_to_try:
            try:
                return llm(prompt, **kwargs)
            except Exception as e:
                print(f"Primary model failed: {e}")
                continue
        
        # Fall back to secondary models
        for llm in self.fallback_llms:
            try:
                return llm(prompt, **kwargs)
            except Exception as e:
                print(f"Fallback model failed: {e}")
                continue
        
        raise RuntimeError("All models failed")
```

### 2.4 Enhanced Testing Support

Create utilities for testing with multiple models:

```python
import pytest
from unittest.mock import Mock
from typing import Dict, Any

class MockLLMProvider:
    """Mock provider for testing without API calls."""
    
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.call_history = []
    
    def create_mock_llm(self, model: str) -> dspy.LM:
        """Create a mock LLM for testing."""
        mock_llm = Mock(spec=dspy.LM)
        mock_llm.model = model
        
        def mock_call(prompt, **kwargs):
            self.call_history.append((model, prompt, kwargs))
            return self.responses.get(prompt, "Mock response")
        
        mock_llm.side_effect = mock_call
        return mock_llm

@pytest.fixture
def multi_model_test_env():
    """Fixture for testing with multiple model configurations."""
    return {
        "openai": MockLLMProvider({"test": "OpenAI response"}),
        "anthropic": MockLLMProvider({"test": "Anthropic response"}),
        "ollama": MockLLMProvider({"test": "Ollama response"})
    }
```

### 2.5 Configuration Management

Implement a comprehensive configuration system:

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
import yaml

@dataclass
class LLMConfig:
    """Configuration for LLM setup."""
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1024
    num_retries: int = 3
    cache: bool = True
    callbacks: List[str] = None
    fallback_models: List[str] = None
    
    @classmethod
    def from_yaml(cls, path: str) -> "LLMConfig":
        """Load configuration from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables."""
        return cls(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
            num_retries=int(os.getenv("LLM_RETRIES", "3")),
            cache=os.getenv("LLM_CACHE", "true").lower() == "true"
        )
    
    def to_dspy_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs for dspy.LM initialization."""
        model_string = f"{self.provider}/{self.model}"
        return {
            "model": model_string,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "num_retries": self.num_retries,
            "cache": self.cache
        }
```

## Implementation Roadmap

### Phase 1: Simple Demo Implementation (Immediate)
1. **Update `shared/llm_utils.py`**:
   - Complete replacement of hardcoded provider logic with simple `setup_llm()` function
   - Remove all legacy provider-specific code
   - No compatibility layers or wrappers

2. **Update `.env.example`**:
   - Replace with new `LLM_MODEL` variable format
   - Remove all legacy provider-specific variables
   - Clear documentation of provider/model format

3. **Update all demo code**:
   - Change all calls to use new `setup_llm()` function
   - Update any provider-specific logic to use model strings

4. **Testing**:
   - Test with different providers (OpenAI, Anthropic, Ollama, Gemini)
   - Verify all demos work with new approach
   - No backward compatibility testing needed

### Phase 2: Future Production Features (As Needed)
- Advanced caching strategies
- Middleware and callbacks
- Model fallback and load balancing
- Enhanced testing utilities
- Configuration management system

## Implementation Steps

### Step 1: Update `shared/llm_utils.py`

Complete replacement of the current implementation with the Phase 1 `setup_llm()` function shown above.

### Step 2: Update Environment Files

Replace `.env.example` with the new format (shown above).

### Step 3: Update All Code

Update all existing code to use the new approach:
```python
# New usage only
llm = setup_llm()  # Uses LLM_MODEL from environment
# or
llm = setup_llm("openai/gpt-4o-mini")  # Explicit model
```

## Phase 1 Testing Checklist

Before deploying Phase 1:

- [ ] Test with Ollama local models
- [ ] Test with OpenAI API
- [ ] Test with Anthropic Claude API  
- [ ] Test with Google Gemini API
- [ ] Verify all demos work with new approach
- [ ] Test environment variable configuration
- [ ] Test explicit model string configuration
- [ ] Verify error messages for missing API keys
- [ ] Test retry logic for transient failures
- [ ] Verify caching behavior

## Conclusion

The two-phased approach provides:

### Phase 1 (Immediate Benefits)
- **Simplicity**: One clean function following DSPy best practices
- **100+ Provider Support**: Automatic through LiteLLM
- **Clean Implementation**: No legacy code or compatibility layers
- **Synchronous-Only**: Adheres to DSPy's recommended patterns
- **Zero Technical Debt**: Fresh start with best practices

### Phase 2 (Future Capabilities)
- **Production Features**: When complexity is justified
- **Advanced Patterns**: For specific enterprise requirements
- **Performance Optimization**: When scale demands it

By implementing Phase 1 as a complete replacement, we immediately gain access to all LiteLLM providers while maintaining maximum simplicity and adhering to DSPy's synchronous-only best practices. The clean break ensures no technical debt and provides a solid foundation for any future Phase 2 enhancements.