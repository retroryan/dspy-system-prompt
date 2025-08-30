"""
Pydantic models for demo execution functionality.

Provides type-safe models for demo execution, status tracking,
and output streaming.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class DemoType(str, Enum):
    """Available demo types."""
    AGRICULTURE = "agriculture"
    ECOMMERCE = "ecommerce"
    WEATHER = "weather"
    MEMORY = "memory"


class DemoStatus(str, Enum):
    """Demo execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DemoOutputType(str, Enum):
    """Types of demo output."""
    INFO = "info"
    COMMAND = "command"
    OUTPUT = "output"
    SUCCESS = "success"
    ERROR = "error"
    METRICS = "metrics"


class DemoStartRequest(BaseModel):
    """Request model for starting a demo."""
    model_config = ConfigDict(frozen=True)
    
    demo_type: DemoType = Field(
        ...,
        description="Type of demo to execute"
    )
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User identifier"
    )
    verbose: bool = Field(
        default=True,
        description="Enable verbose output"
    )


class DemoOutputLine(BaseModel):
    """Individual line of demo output."""
    model_config = ConfigDict(frozen=True)
    
    type: DemoOutputType = Field(
        ...,
        description="Type of output line"
    )
    text: str = Field(
        ...,
        description="Output text content"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Output timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class DemoResponse(BaseModel):
    """Response model for demo information."""
    model_config = ConfigDict(frozen=True)
    
    demo_id: str = Field(
        ...,
        description="Unique demo execution identifier"
    )
    demo_type: DemoType = Field(
        ...,
        description="Type of demo"
    )
    user_id: str = Field(
        ...,
        description="User identifier"
    )
    status: DemoStatus = Field(
        ...,
        description="Current demo status"
    )
    started_at: datetime = Field(
        ...,
        description="Demo start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Demo completion timestamp"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Associated session ID if created"
    )
    execution_time: Optional[float] = Field(
        default=None,
        description="Total execution time in seconds"
    )
    total_queries: Optional[int] = Field(
        default=None,
        description="Number of queries executed"
    )
    total_iterations: Optional[int] = Field(
        default=None,
        description="Total React iterations"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="Tools used during execution"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class DemoOutputResponse(BaseModel):
    """Response model for demo output."""
    model_config = ConfigDict(frozen=True)
    
    demo_id: str = Field(
        ...,
        description="Demo execution identifier"
    )
    output: List[DemoOutputLine] = Field(
        ...,
        description="List of output lines"
    )
    has_more: bool = Field(
        ...,
        description="Whether more output is available"
    )
    status: DemoStatus = Field(
        ...,
        description="Current demo status"
    )


class DemoListResponse(BaseModel):
    """Response model for listing demos."""
    model_config = ConfigDict(frozen=True)
    
    demos: List[DemoResponse] = Field(
        ...,
        description="List of demo executions"
    )
    total: int = Field(
        ...,
        description="Total number of demos"
    )