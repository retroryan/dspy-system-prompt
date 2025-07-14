"""
Shared models and utilities for DSPy tool selection and agentic loop.

This module contains the shared models, utilities, and metrics used throughout
the DSPy system for tool selection, agentic loops, and evaluation.
"""

# Import models
from .models import (
    # Tool selection models
    ToolCall,
    MultiToolDecision,
    
    # Evaluation models
    ToolSelectionEvaluation,
    TestResult,
    TestSummary,
    ModelComparisonResult
)

from .console_utils import ConsoleFormatter
from .llm_utils import setup_llm
from .metrics import ToolSelectionMetrics, evaluate_tool_selection

__all__ = [
    # Tool selection models
    'ToolCall',
    'MultiToolDecision',
    
    # Evaluation models
    'ToolSelectionEvaluation',
    'TestResult',
    'TestSummary',
    'ModelComparisonResult',
    
    # Utilities
    'ConsoleFormatter',
    'setup_llm',
    'ToolSelectionMetrics',
    'evaluate_tool_selection'
]