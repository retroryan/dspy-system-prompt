"""Centralized configuration for DSPy project."""
import os
from pydantic import BaseModel


class Config(BaseModel):
    """Project configuration."""
    model: str = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", os.getenv("LLM_MAX_ITERATIONS", "5")))


config = Config()