"""
Pydantic models for configuration management.

Provides type-safe models for system configuration sections.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class LLMConfig(BaseModel):
    """LLM configuration settings."""
    model_config = ConfigDict(frozen=True)
    
    provider: str = Field(
        default="ollama",
        description="LLM provider (ollama, claude, openai, gemini)"
    )
    model: str = Field(
        default="llama3.2:3b",
        description="Model name/identifier"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Generation temperature"
    )
    max_tokens: int = Field(
        default=1024,
        ge=1,
        le=8192,
        description="Maximum tokens per generation"
    )


class AgentConfig(BaseModel):
    """Agent configuration settings."""
    model_config = ConfigDict(frozen=True)
    
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum React loop iterations"
    )
    timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Query timeout in seconds"
    )
    memory_size: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Conversation memory size"
    )
    debug_mode: bool = Field(
        default=False,
        description="Enable debug output"
    )


class ToolsConfig(BaseModel):
    """Tool management configuration."""
    model_config = ConfigDict(frozen=True)
    
    weather_enabled: bool = Field(
        default=True,
        description="Enable weather tools"
    )
    search_enabled: bool = Field(
        default=True,
        description="Enable search tools"
    )
    calculator_enabled: bool = Field(
        default=True,
        description="Enable calculator tools"
    )
    memory_enabled: bool = Field(
        default=True,
        description="Enable memory tools"
    )


class APIConfig(BaseModel):
    """API server configuration."""
    model_config = ConfigDict(frozen=True)
    
    endpoint: str = Field(
        default="http://localhost:8000",
        description="API endpoint URL"
    )
    timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds"
    )
    retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts"
    )


class SystemHealthStatus(BaseModel):
    """System health status information."""
    model_config = ConfigDict(frozen=True)
    
    status: str = Field(
        ...,
        description="Overall system status (healthy, warning, error)"
    )
    uptime: str = Field(
        ...,
        description="System uptime string"
    )
    memory: Dict[str, float] = Field(
        ...,
        description="Memory usage information"
    )
    cpu: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="CPU usage percentage"
    )
    active_connections: int = Field(
        ...,
        ge=0,
        description="Number of active connections"
    )
    last_check: str = Field(
        ...,
        description="Last health check timestamp"
    )


class SystemMetrics(BaseModel):
    """Enhanced system metrics."""
    model_config = ConfigDict(frozen=True)
    
    # Basic metrics (from existing /metrics endpoint)
    total_requests: int = Field(default=0, ge=0)
    total_queries: int = Field(default=0, ge=0)
    active_sessions: int = Field(default=0, ge=0)
    average_query_time: float = Field(default=0.0, ge=0.0)
    uptime_seconds: float = Field(..., ge=0.0)
    
    # Enhanced metrics
    memory_usage_mb: float = Field(default=0.0, ge=0.0)
    cpu_usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    disk_usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    active_demos: int = Field(default=0, ge=0)
    completed_demos: int = Field(default=0, ge=0)
    failed_demos: int = Field(default=0, ge=0)
    tool_executions: Dict[str, int] = Field(default_factory=dict)


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    model_config = ConfigDict(frozen=True)
    
    section: str = Field(
        ...,
        description="Configuration section to update"
    )
    config: Dict[str, Any] = Field(
        ...,
        description="Configuration values to update"
    )


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    model_config = ConfigDict(frozen=True)
    
    section: str = Field(
        ...,
        description="Configuration section name"
    )
    config: Dict[str, Any] = Field(
        ...,
        description="Configuration values"
    )
    updated_at: str = Field(
        ...,
        description="Last update timestamp"
    )


class SystemAction(str, Enum):
    """Available system actions."""
    RESTART_SERVICES = "restart_services"
    CLEAR_CACHE = "clear_cache"
    EXPORT_DIAGNOSTICS = "export_diagnostics"
    VIEW_LOGS = "view_logs"


class SystemActionRequest(BaseModel):
    """Request model for system actions."""
    model_config = ConfigDict(frozen=True)
    
    action: SystemAction = Field(
        ...,
        description="System action to perform"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional action parameters"
    )


class SystemActionResponse(BaseModel):
    """Response model for system actions."""
    model_config = ConfigDict(frozen=True)
    
    action: SystemAction = Field(
        ...,
        description="Performed action"
    )
    success: bool = Field(
        ...,
        description="Whether action succeeded"
    )
    message: str = Field(
        ...,
        description="Action result message"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional result data"
    )