"""
LLM utilities for DSPy demo project.

This module provides a clean, simple interface for setting up LLMs using DSPy's native
capabilities and LiteLLM's automatic provider routing. It follows DSPy best practices:
- Direct use of dspy.LM() with provider/model format
- Synchronous-only operations
- No unnecessary abstractions or compatibility layers
- Leverages LiteLLM's 100+ provider support
"""

import logging
from typing import Optional

import dspy

from shared.config import config


# Configure logging
logger = logging.getLogger(__name__)


def setup_llm(model: Optional[str] = None, **kwargs) -> dspy.LM:
    """Simple LLM setup."""
    model = model or config.model
    llm_config = {
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        **kwargs
    }
    llm = dspy.LM(model=model, **llm_config)
    dspy.configure(lm=llm)
    return llm


