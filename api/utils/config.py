"""
Configuration management for the API server.

Centralizes all configuration settings using environment variables
with sensible defaults for demo purposes.
"""

import os
from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    """API server configuration."""
    
    # Server settings
    api_port: int = Field(
        default=8000,
        description="API server port"
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    
    # Session settings
    session_ttl_minutes: int = Field(
        default=30,
        description="Session timeout in minutes"
    )
    max_sessions_per_user: int = Field(
        default=10,
        description="Maximum concurrent sessions per user"
    )
    cleanup_interval_seconds: int = Field(
        default=60,
        description="Interval for session cleanup task"
    )
    
    # Query settings
    query_timeout_seconds: int = Field(
        default=60,
        description="Maximum query execution time"
    )
    default_max_iterations: int = Field(
        default=5,
        description="Default max iterations for React loop"
    )
    
    # Logging settings
    debug_mode: bool = Field(
        default=False,
        description="Enable debug logging"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # API settings
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    api_title: str = Field(
        default="Agentic Loop API",
        description="API title for documentation"
    )
    api_description: str = Field(
        default="REST API for interacting with the DSPy-based agentic loop",
        description="API description"
    )
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    cors_allow_methods: list[str] = Field(
        default=["*"],
        description="Allowed HTTP methods"
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed HTTP headers"
    )
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create configuration from environment variables."""
        return cls(
            api_port=int(os.getenv("API_PORT", "8000")),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            session_ttl_minutes=int(os.getenv("SESSION_TTL_MINUTES", "30")),
            max_sessions_per_user=int(os.getenv("MAX_SESSIONS_PER_USER", "10")),
            cleanup_interval_seconds=int(os.getenv("CLEANUP_INTERVAL_SECONDS", "60")),
            query_timeout_seconds=int(os.getenv("QUERY_TIMEOUT_SECONDS", "60")),
            default_max_iterations=int(os.getenv("DEFAULT_MAX_ITERATIONS", "5")),
            debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            api_version=os.getenv("API_VERSION", "1.0.0"),
            api_title=os.getenv("API_TITLE", "Agentic Loop API"),
            api_description=os.getenv(
                "API_DESCRIPTION",
                "REST API for interacting with the DSPy-based agentic loop"
            ),
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
            cors_allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
            cors_allow_methods=os.getenv("CORS_ALLOW_METHODS", "*").split(","),
            cors_allow_headers=os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
        )


# Global config instance
config = APIConfig.from_env()