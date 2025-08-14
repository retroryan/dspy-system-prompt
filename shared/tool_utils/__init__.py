"""
Tool utilities for DSPy tool management.

This module contains core tool interfaces, registries, and tool set management
functionality used throughout the DSPy system.
"""

from .base_tool import BaseTool, ToolArgument, ToolTestCase
from .registry import ToolRegistry
from .base_tool_sets import (
    ToolSet,
    ToolSetTestCase,
    ToolSetConfig
)
from .error_handling import (
    ToolError,
    ToolExecutionError,
    ToolValidationError,
    ToolDataError,
    safe_tool_execution,
    handle_tool_error,
    validate_required_data
)

__all__ = [
    # Core tool interface
    'BaseTool',
    'ToolArgument', 
    'ToolTestCase',
    
    # Registry
    'ToolRegistry',
    
    # Tool sets
    'ToolSet',
    'ToolSetTestCase',
    'ToolSetConfig',
    
    # Error handling
    'ToolError',
    'ToolExecutionError',
    'ToolValidationError',
    'ToolDataError',
    'safe_tool_execution',
    'handle_tool_error',
    'validate_required_data'
]