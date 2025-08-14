"""
Standardized error handling for tools.

This module provides consistent error handling patterns for all tools
to ensure uniform behavior across the system.
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
import logging
import traceback

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Base exception for tool execution errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class ToolExecutionError(ToolError):
    """Raised when a tool fails during execution."""
    pass


class ToolValidationError(ToolError):
    """Raised when tool arguments fail validation."""
    pass


class ToolDataError(ToolError):
    """Raised when required data is not available."""
    pass


def handle_tool_error(error: Exception, tool_name: str) -> Dict[str, Any]:
    """
    Convert an exception to a standardized error response.
    
    Args:
        error: The exception that occurred
        tool_name: Name of the tool that failed
        
    Returns:
        Standardized error dictionary
    """
    error_response = {
        "status": "error",
        "error": str(error),
        "tool": tool_name
    }
    
    if isinstance(error, ToolError):
        # Add specific error details for ToolError subclasses
        error_response["error_code"] = error.error_code
        error_response["details"] = error.details
    else:
        # For unexpected errors, log the full traceback
        logger.error(f"Unexpected error in {tool_name}: {error}", exc_info=True)
        error_response["error_code"] = "UNEXPECTED_ERROR"
        
    return error_response


def safe_tool_execution(func):
    """
    Decorator for safe tool execution with standardized error handling.
    
    Usage:
        @safe_tool_execution
        def execute(self, **kwargs):
            # tool logic here
            return result
    """
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            
            # Ensure result is a dictionary or Pydantic model
            if isinstance(result, BaseModel):
                return result.model_dump(exclude_none=True)
            elif isinstance(result, dict):
                return result
            else:
                # Convert other types to standard response
                return {
                    "status": "success",
                    "result": result
                }
                
        except ToolError as e:
            # Handle known tool errors
            return handle_tool_error(e, self.NAME)
        except Exception as e:
            # Handle unexpected errors
            return handle_tool_error(e, self.NAME)
    
    return wrapper


def validate_required_data(data: Any, field_name: str, tool_name: str) -> Any:
    """
    Validate that required data exists.
    
    Args:
        data: The data to validate
        field_name: Name of the field being validated
        tool_name: Name of the tool for error reporting
        
    Returns:
        The validated data
        
    Raises:
        ToolDataError: If data is None or empty
    """
    if data is None:
        raise ToolDataError(
            f"Required field '{field_name}' is missing",
            error_code="MISSING_REQUIRED_FIELD",
            details={"field": field_name, "tool": tool_name}
        )
    
    if isinstance(data, (list, dict, str)) and len(data) == 0:
        raise ToolDataError(
            f"Required field '{field_name}' is empty",
            error_code="EMPTY_REQUIRED_FIELD",
            details={"field": field_name, "tool": tool_name}
        )
    
    return data