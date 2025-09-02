"""
Logging configuration for the API.

Provides structured logging setup for the application.
"""

import logging

logger = logging.getLogger(__name__)


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