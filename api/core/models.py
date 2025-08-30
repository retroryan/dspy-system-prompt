"""
Pydantic models for API request and response types.

This module defines all the data structures used by the API,
ensuring type safety and validation throughout.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class SessionConfig(BaseModel):
    """Configuration for conversation history management."""
    model_config = ConfigDict(frozen=True)
    
    max_messages: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum messages to keep in memory"
    )
    summarize_removed: bool = Field(
        default=True,
        description="Whether to summarize removed messages"
    )


class SessionCreateRequest(BaseModel):
    """Request model for creating a new session."""
    model_config = ConfigDict(frozen=True)
    
    tool_set: str = Field(
        ...,
        description="Tool set to use (ecommerce, agriculture, events)"
    )
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the user"
    )
    config: Optional[SessionConfig] = Field(
        default=None,
        description="Optional conversation history configuration"
    )


class SessionResponse(BaseModel):
    """Response model for session information."""
    model_config = ConfigDict(frozen=True)
    
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    tool_set: str = Field(
        ...,
        description="The selected tool set"
    )
    user_id: str = Field(
        ...,
        description="The user identifier"
    )
    created_at: datetime = Field(
        ...,
        description="Session creation timestamp"
    )
    status: str = Field(
        ...,
        description="Session status (active, expired)"
    )
    conversation_turns: int = Field(
        default=0,
        description="Number of conversation turns"
    )


class QueryRequest(BaseModel):
    """Request model for executing a query."""
    model_config = ConfigDict(frozen=True)
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language query text"
    )
    max_iterations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum React loop iterations"
    )


class QueryResponse(BaseModel):
    """Response model for query execution results."""
    model_config = ConfigDict(frozen=True)
    
    answer: str = Field(
        ...,
        description="The synthesized answer from the agent"
    )
    execution_time: float = Field(
        ...,
        ge=0,
        description="Total execution time in seconds"
    )
    iterations: int = Field(
        ...,
        ge=0,
        description="Number of React iterations performed"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools that were executed"
    )
    conversation_turn: int = Field(
        ...,
        ge=1,
        description="Current turn number in conversation"
    )
    had_context: bool = Field(
        ...,
        description="Whether previous context was available"
    )
    session_id: str = Field(
        ...,
        description="Associated session identifier"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )


class ErrorDetail(BaseModel):
    """Detailed error information."""
    model_config = ConfigDict(frozen=True)
    
    code: str = Field(
        ...,
        description="Error code identifier"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context and suggestions"
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""
    model_config = ConfigDict(frozen=True)
    
    error: ErrorDetail = Field(
        ...,
        description="Error information"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    model_config = ConfigDict(frozen=True)
    
    status: str = Field(
        ...,
        description="Service status (healthy, degraded, unhealthy)"
    )
    version: str = Field(
        ...,
        description="API version"
    )
    uptime_seconds: float = Field(
        ...,
        ge=0,
        description="Service uptime in seconds"
    )
    active_sessions: int = Field(
        default=0,
        ge=0,
        description="Number of active sessions"
    )


class ToolSetInfo(BaseModel):
    """Information about a tool set."""
    model_config = ConfigDict(frozen=True)
    
    name: str = Field(
        ...,
        description="Tool set name"
    )
    description: str = Field(
        ...,
        description="Tool set description"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of available tools"
    )
    example_queries: List[str] = Field(
        default_factory=list,
        description="Example queries for this tool set"
    )


class MetricsResponse(BaseModel):
    """Server metrics response."""
    model_config = ConfigDict(frozen=True)
    
    total_requests: int = Field(
        default=0,
        ge=0,
        description="Total API requests"
    )
    total_queries: int = Field(
        default=0,
        ge=0,
        description="Total queries processed"
    )
    active_sessions: int = Field(
        default=0,
        ge=0,
        description="Currently active sessions"
    )
    average_query_time: float = Field(
        default=0.0,
        ge=0,
        description="Average query execution time"
    )
    uptime_seconds: float = Field(
        ...,
        ge=0,
        description="Service uptime"
    )


class ProgressStep(BaseModel):
    """Single step in agent execution progress."""
    model_config = ConfigDict(frozen=True)
    
    thought: str = Field(
        ...,
        description="Agent's reasoning for this step"
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Name of tool to execute"
    )
    tool_args: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Arguments for tool execution"
    )
    observation: Optional[str] = Field(
        default=None,
        description="Result from tool execution"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this step occurred"
    )
    step_number: int = Field(
        ...,
        ge=1,
        description="Step number in sequence"
    )


class ProgressResponse(BaseModel):
    """Response for progress endpoint."""
    model_config = ConfigDict(frozen=True)
    
    session_id: str = Field(
        ...,
        description="Session identifier"
    )
    is_processing: bool = Field(
        ...,
        description="Whether query is still being processed"
    )
    steps: List[ProgressStep] = Field(
        default_factory=list,
        description="Completed steps so far"
    )
    elapsed_seconds: float = Field(
        default=0.0,
        ge=0,
        description="Time elapsed since query started"
    )
    current_query: Optional[str] = Field(
        default=None,
        description="The query being processed"
    )