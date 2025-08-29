"""
FastAPI application entry point.

Sets up the API server with all routers, middleware, and configuration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from api.utils.config import config
from api.middleware.logging import LoggingMiddleware, setup_logging
from api.middleware.error_handler import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from api.routers import health, sessions, queries, tools
from api.core.sessions import session_manager

# Setup logging
setup_logging(config.log_level, config.debug_mode)

# Create FastAPI application
app = FastAPI(
    title=config.api_title,
    description=config.api_description,
    version=config.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "Health", "description": "Health checks and metrics"},
        {"name": "Sessions", "description": "Session management operations"},
        {"name": "Queries", "description": "Query execution within sessions"},
        {"name": "Tools", "description": "Tool set information and discovery"}
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=config.cors_allow_credentials,
    allow_methods=config.cors_allow_methods,
    allow_headers=config.cors_allow_headers,
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Register exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(queries.router)
app.include_router(tools.router)

# Root endpoint
@app.get("/", tags=["Root"])
def root():
    """
    API Information and Navigation.
    
    Returns information about the API and links to key endpoints.
    """
    return {
        "name": config.api_title,
        "version": config.api_version,
        "description": config.api_description,
        "endpoints": {
            "documentation": {
                "interactive": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json"
            },
            "health": "/health",
            "metrics": "/metrics",
            "sessions": "/sessions",
            "tool_sets": "/tool-sets"
        },
        "quick_start": {
            "1_create_session": "POST /sessions with tool_set and user_id",
            "2_execute_query": "POST /sessions/{session_id}/query with query text",
            "3_cleanup": "DELETE /sessions/{session_id}"
        }
    }

# Startup event
@app.on_event("startup")
def startup_event():
    """Initialize the application on startup."""
    import logging
    from shared import setup_llm
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {config.api_title} v{config.api_version}")
    logger.info(f"Debug mode: {config.debug_mode}")
    logger.info(f"Server will listen on {config.api_host}:{config.api_port}")
    
    # Configure LLM for DSPy
    logger.info("Configuring LLM for DSPy...")
    try:
        setup_llm()
        logger.info("LLM configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure LLM: {e}")
        logger.warning("API will run but query execution may fail without LLM")

# Shutdown event
@app.on_event("shutdown")
def shutdown_event():
    """Clean up on shutdown."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Shutting down API server")
    # Shutdown session manager
    session_manager.shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug_mode
    )