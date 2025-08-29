"""
Global error handling middleware for the API.

Provides consistent error responses and logging for all exceptions.
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from api.core.models import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class SessionNotFoundException(APIException):
    """Exception raised when a session is not found."""
    
    def __init__(self, session_id: str):
        super().__init__(
            code="SESSION_NOT_FOUND",
            message=f"Session with ID '{session_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={
                "session_id": session_id,
                "suggestion": "Create a new session first"
            }
        )


class SessionExpiredException(APIException):
    """Exception raised when a session has expired."""
    
    def __init__(self, session_id: str):
        super().__init__(
            code="SESSION_EXPIRED",
            message=f"Session '{session_id}' has expired",
            status_code=status.HTTP_410_GONE,
            details={
                "session_id": session_id,
                "suggestion": "Create a new session"
            }
        )


class QueryTimeoutException(APIException):
    """Exception raised when a query execution times out."""
    
    def __init__(self, timeout_seconds: int):
        super().__init__(
            code="QUERY_TIMEOUT",
            message=f"Query execution exceeded {timeout_seconds} seconds",
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            details={
                "timeout_seconds": timeout_seconds,
                "suggestion": "Try a simpler query or increase timeout"
            }
        )


class ToolSetNotFoundException(APIException):
    """Exception raised when a tool set is not found."""
    
    def __init__(self, tool_set: str):
        super().__init__(
            code="TOOL_SET_NOT_FOUND",
            message=f"Tool set '{tool_set}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={
                "tool_set": tool_set,
                "available_tool_sets": ["agriculture", "ecommerce", "events"]
            }
        )


class MaxSessionsExceededException(APIException):
    """Exception raised when user exceeds max sessions."""
    
    def __init__(self, user_id: str, max_sessions: int):
        super().__init__(
            code="MAX_SESSIONS_EXCEEDED",
            message=f"User '{user_id}' has reached maximum of {max_sessions} sessions",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={
                "user_id": user_id,
                "max_sessions": max_sessions,
                "suggestion": "Close existing sessions before creating new ones"
            }
        )


def create_error_response(
    code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details
        ),
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode='json')
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle API exceptions."""
    logger.error(f"API Exception: {exc.code} - {exc.message}")
    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return create_error_response(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        status_code=exc.status_code,
        details={"path": str(request.url.path)}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation exceptions."""
    logger.error(f"Validation Error: {exc.errors()}")
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Invalid request data",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"errors": exc.errors()}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled Exception: {str(exc)}\n{traceback.format_exc()}")
    return create_error_response(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"type": type(exc).__name__} if logger.level == logging.DEBUG else None
    )