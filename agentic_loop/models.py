"""Pydantic models for the agentic loop."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Represents a single tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class Trajectory(BaseModel):
    """Represents the complete trajectory of an agent execution."""
    user_query: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, completed, failed, max_iterations_reached


class AgentLoopResult(BaseModel):
    """Result from the agent loop execution."""
    status: str  # success, error
    trajectory: Optional[Trajectory] = None
    tools_used: List[str] = Field(default_factory=list)
    execution_time: float = 0.0
    answer: Optional[str] = None
    reasoning: Optional[str] = None
    total_iterations: int = 0
    error: Optional[str] = None


class ExtractResult(BaseModel):
    """Result from the extract agent."""
    answer: str
    reasoning: Optional[str] = None