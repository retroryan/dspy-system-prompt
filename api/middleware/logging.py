"""
Request and response logging middleware.

Provides structured logging for all API requests and responses.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process and log the request/response cycle."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Add request ID to request state for use in other parts of the app
        request.state.request_id = request_id
        
        # Track request count
        from api.routers.health import metrics
        metrics.increment_requests()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"[{request_id}] Response {response.status_code} "
                f"in {duration:.3f}s"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"[{request_id}] Request failed after {duration:.3f}s: {str(e)}"
            )
            
            # Re-raise the exception to be handled by error middleware
            raise


def setup_logging(log_level: str = "INFO", debug_mode: bool = False):
    """Configure logging for the application."""
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure format
    if debug_mode:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    else:
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    
    logger.info(f"Logging configured with level: {log_level}")