"""
LLM utilities for DSPy demo project.

This module provides a clean, simple interface for setting up LLMs using DSPy's native
capabilities and LiteLLM's automatic provider routing. It follows DSPy best practices:
- Direct use of dspy.LM() with provider/model format
- Synchronous-only operations
- No unnecessary abstractions or compatibility layers
- Leverages LiteLLM's 100+ provider support
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import dspy
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


class TokenUsage(BaseModel):
    """Token usage statistics for a single LLM call."""
    input: int = Field(default=0, description="Number of input/prompt tokens")
    output: int = Field(default=0, description="Number of output/completion tokens") 
    total: int = Field(default=0, description="Total tokens used (input + output)")


class Message(BaseModel):
    """A single message in the conversation."""
    role: str = Field(description="Role of the message sender (user, assistant, system)")
    content: str = Field(description="Content of the message")


class LLMHistoryEntry(BaseModel):
    """Structured representation of a single LLM interaction."""
    timestamp: Optional[str] = Field(default=None, description="Timestamp of the interaction")
    model: Optional[str] = Field(default=None, description="Model used for the interaction")
    uuid: Optional[str] = Field(default=None, description="Unique identifier (first 8 chars)")
    conversation: List[Message] = Field(default_factory=list, description="List of messages in the conversation")
    tokens: TokenUsage = Field(default_factory=TokenUsage, description="Token usage statistics")
    cost: Optional[float] = Field(default=None, description="Cost of the API call if available")


class LLMHistory(BaseModel):
    """Collection of LLM history entries with aggregated statistics."""
    entries: List[LLMHistoryEntry] = Field(default_factory=list, description="List of history entries")
    total_tokens: TokenUsage = Field(default_factory=TokenUsage, description="Aggregated token usage")
    total_cost: float = Field(default=0.0, description="Total cost across all entries")
    
    def calculate_totals(self) -> None:
        """Calculate total token usage and cost across all entries."""
        self.total_tokens = TokenUsage(input=0, output=0, total=0)
        self.total_cost = 0.0
        
        for entry in self.entries:
            self.total_tokens.input += entry.tokens.input
            self.total_tokens.output += entry.tokens.output
            self.total_tokens.total += entry.tokens.total
            if entry.cost is not None:
                self.total_cost += entry.cost


def setup_llm(model: Optional[str] = None, **kwargs) -> dspy.LM:
    """
    Set up and configure a language model using DSPy's native LiteLLM integration.
    
    This function follows DSPy best practices by directly using dspy.LM() with
    the provider/model format, letting LiteLLM handle all provider routing automatically.
    
    Args:
        model: Full model string in provider/model format (e.g., "openai/gpt-4o-mini").
               If None, reads from LLM_MODEL environment variable.
        **kwargs: Additional parameters passed directly to dspy.LM (overrides defaults).
    
    Returns:
        Configured dspy.LM instance.
    
    Examples:
        # Use environment variable
        llm = setup_llm()
        
        # Explicit model specification
        llm = setup_llm("openai/gpt-4o-mini")
        llm = setup_llm("anthropic/claude-3-opus-20240229")
        llm = setup_llm("ollama/gemma3:27b")
        llm = setup_llm("gemini/gemini-1.5-pro")
    
    Environment Variables:
        LLM_MODEL: Default model to use (e.g., "openai/gpt-4o-mini")
        LLM_TEMPERATURE: Generation temperature (default: 0.7)
        LLM_MAX_TOKENS: Maximum tokens to generate (default: 1024)
        LLM_RETRIES: Number of retries for transient failures (default: 3)
        LLM_CACHE: Enable caching (default: true)
        DSPY_DEBUG: Enable debug logging (default: false)
    """
    # Load environment variables from .env file if it exists
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Get model from parameter or environment
    model = model or os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    
    # Build configuration from environment with kwargs overrides
    config = {
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
        "num_retries": int(os.getenv("LLM_RETRIES", "3")),
        "cache": os.getenv("LLM_CACHE", "true").lower() == "true",
    }
    
    # Apply any kwargs overrides (including api_base if provided)
    config.update(kwargs)
    
    # Debug logging if enabled
    debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"
    if debug_enabled:
        logging.getLogger("dspy").setLevel(logging.DEBUG)
        logger.info(f"🤖 Setting up LLM: {model}")
        logger.info(f"   Configuration: temperature={config['temperature']}, max_tokens={config['max_tokens']}")
        logger.info(f"   Retries: {config['num_retries']}, Cache: {config['cache']}")
    
    # Create and configure the LLM
    try:
        llm = dspy.LM(model=model, **config)
        dspy.settings.configure(lm=llm)
        
        # Test the connection with a minimal query
        if debug_enabled:
            logger.info(f"   Testing {model} connection...")
            llm("test", max_tokens=10)
            logger.info(f"   ✅ {model} connection successful")
        
        return llm
        
    except Exception as e:
        # Provide helpful error messages for common issues
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            provider = model.split("/")[0] if "/" in model else "unknown"
            api_key_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "gemini": "GOOGLE_API_KEY",
                "cohere": "COHERE_API_KEY",
                "replicate": "REPLICATE_API_TOKEN",
            }
            if provider in api_key_map:
                logger.error(f"❌ Authentication failed. Please set {api_key_map[provider]} in your environment or .env file")
            else:
                logger.error(f"❌ Authentication failed for {provider}. Please check your API key configuration")
        elif "connection" in error_msg.lower() and "ollama" in model.lower():
            logger.error(f"❌ Could not connect to Ollama. Make sure Ollama is running and OLLAMA_BASE_URL is set correctly")
        else:
            logger.error(f"❌ Failed to initialize {model}: {error_msg}")
        raise


def extract_messages(history_entries: List[Dict[str, Any]], n: Optional[int] = None) -> LLMHistory:
    """
    Extract DSPy history entries as structured Pydantic models.
    
    Args:
        history_entries: List from GLOBAL_HISTORY or lm.history
        n: Number of recent entries (None for all)
    
    Returns:
        LLMHistory object with structured message data and aggregated statistics
    """
    if not history_entries:
        return LLMHistory()
    
    # Get entries to process
    entries = history_entries[-n:] if n else history_entries
    history_entries_list = []
    
    for entry in entries:
        # Create conversation messages
        conversation = []
        
        # Input messages
        messages = entry.get("messages") or [{"role": "user", "content": entry.get("prompt", "")}]
        
        for msg in messages:
            content = msg.get("content", "")
            
            # Handle different content types
            if isinstance(content, str):
                message_text = content
            elif isinstance(content, list):
                # Extract text from complex content (images, audio, etc.)
                text_parts = []
                for item in content:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                message_text = " ".join(text_parts)
            else:
                message_text = str(content)
            
            conversation.append(Message(
                role=msg.get("role", "user"),
                content=message_text
            ))
        
        # Response/output
        outputs = entry.get("outputs", [])
        if outputs:
            # Handle different output formats
            if isinstance(outputs[0], dict):
                response_text = outputs[0].get("text", "")
            else:
                response_text = str(outputs[0])
            
            conversation.append(Message(
                role="assistant", 
                content=response_text
            ))
        
        # Token usage - handle different formats
        usage = entry.get("usage", {})
        if isinstance(usage, dict):
            tokens = TokenUsage(
                input=usage.get("prompt_tokens", 0),
                output=usage.get("completion_tokens", 0),
                total=usage.get("total_tokens", 0)
            )
        else:
            # Handle case where usage might be an integer or other type
            tokens = TokenUsage(
                input=0,
                output=0,
                total=int(usage) if isinstance(usage, (int, float)) else 0
            )
        
        # Create history entry
        history_entry = LLMHistoryEntry(
            timestamp=entry.get("timestamp"),
            model=entry.get("model"),
            uuid=entry.get("uuid")[:8] if entry.get("uuid") else None,
            conversation=conversation,
            tokens=tokens,
            cost=entry.get("cost")
        )
        
        history_entries_list.append(history_entry)
    
    # Create LLMHistory object and calculate totals
    history = LLMHistory(entries=history_entries_list)
    history.calculate_totals()
    
    return history


def save_dspy_history(
    tool_set_name: str,
    agent_type: str, 
    index: int,
    n_entries: Optional[int] = 1,
    output_dir: str = "prompts_out",
    history: Optional[LLMHistory] = None
) -> Optional[str]:
    """
    Extract and save the last N DSPy history entries to a JSON file.
    
    Args:
        tool_set_name: Name of the tool set being used
        agent_type: Type of agent ("react" or "extract")
        index: Index/iteration number
        n_entries: Number of recent entries to extract (default: 1 for last entry only)
        output_dir: Directory to save the JSON files
        history: Optional pre-extracted LLMHistory object. If not provided, will extract from GLOBAL_HISTORY
        
    Returns:
        Path to the saved JSON file, or None if no history to save
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Extract history if not provided
    if history is None:
        from dspy.clients.base_lm import GLOBAL_HISTORY
        history = extract_messages(GLOBAL_HISTORY, n=n_entries)
    
    if not history or not history.entries:
        return None
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{tool_set_name}_{agent_type}_{index}_{timestamp}.json"
    file_path = output_path / filename
    
    # Convert Pydantic model to dict and save
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(history.model_dump(), f, indent=2, ensure_ascii=False)
    
    return str(file_path)


def get_full_history() -> LLMHistory:
    """
    Get the full DSPy history from the current session.
    
    Returns:
        LLMHistory object with all entries and aggregated statistics
    """
    from dspy.clients.base_lm import GLOBAL_HISTORY
    return extract_messages(GLOBAL_HISTORY)