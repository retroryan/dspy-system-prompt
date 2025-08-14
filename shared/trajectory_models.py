"""
Type-safe Pydantic models for the trajectory system.

This module implements a clean, type-safe trajectory system using Pydantic models,
replacing the legacy dictionary-based approach with structured, validated data models.
Following the React pattern, the trajectory tracks agent thoughts, tool invocations,
and observations through each iteration.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class ToolStatus(str, Enum):
    """Status of a tool execution."""
    SUCCESS = "success"
    ERROR = "error"


class ThoughtStep(BaseModel):
    """Represents the agent's reasoning at a specific moment."""
    model_config = ConfigDict(frozen=True)
    
    content: str = Field(
        ..., 
        description="The agent's reasoning about the current state and next action"
    )


class ToolInvocation(BaseModel):
    """Represents a tool call made by the agent."""
    model_config = ConfigDict(frozen=True)
    
    tool_name: str = Field(
        ...,
        description="Name of the tool to invoke"
    )
    tool_args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the tool"
    )


class ToolObservation(BaseModel):
    """Represents the result of a tool execution."""
    model_config = ConfigDict(frozen=True)
    
    tool_name: str = Field(
        ...,
        description="Name of the tool that was executed"
    )
    status: ToolStatus = Field(
        ...,
        description="Status of the tool execution"
    )
    result: Optional[Any] = Field(
        None,
        description="The result returned by the tool if successful"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if the tool failed"
    )
    execution_time_ms: float = Field(
        0.0,
        description="Time taken to execute the tool in milliseconds"
    )


class TrajectoryStep(BaseModel):
    """A single step in the agent's trajectory."""
    model_config = ConfigDict(frozen=True)
    
    iteration: int = Field(
        ...,
        ge=1,
        description="Iteration number (1-based)"
    )
    thought: ThoughtStep = Field(
        ...,
        description="The agent's reasoning for this step"
    )
    tool_invocation: Optional[ToolInvocation] = Field(
        None,
        description="Tool call made in this step (including 'finish' pseudo-tool)"
    )
    observation: Optional[ToolObservation] = Field(
        None,
        description="Result of the tool execution (None for 'finish' tool)"
    )
    
    @property
    def is_finish(self) -> bool:
        """
        Check if this step represents the agent's decision to finish.
        
        The 'finish' tool is a special pseudo-tool that signals the agent
        has gathered sufficient information to answer the user's query.
        """
        return (
            self.tool_invocation is not None and 
            self.tool_invocation.tool_name == "finish"
        )
    
    @property
    def has_error(self) -> bool:
        """Check if this step encountered an error."""
        return self.observation is not None and self.observation.status == ToolStatus.ERROR


class Trajectory(BaseModel):
    """Complete trajectory of an agent's execution."""
    
    user_query: str = Field(
        ...,
        description="The original user query that started this trajectory"
    )
    steps: List[TrajectoryStep] = Field(
        default_factory=list,
        description="Ordered list of steps taken by the agent"
    )
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="When this trajectory was started"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="When this trajectory was completed"
    )
    tool_set_name: str = Field(
        ...,
        description="Name of the tool set used for this trajectory"
    )
    max_iterations: int = Field(
        default=5,
        description="Maximum allowed iterations"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata for storing conversation context and other information"
    )
    
    @property
    def is_complete(self) -> bool:
        """
        Check if the trajectory is complete.
        
        A trajectory is complete when either:
        - The agent selected the 'finish' tool
        - Maximum iterations have been reached
        """
        if not self.steps:
            return False
        return self.steps[-1].is_finish or len(self.steps) >= self.max_iterations
    
    @property
    def iteration_count(self) -> int:
        """Get the current iteration count."""
        return len(self.steps)
    
    @property
    def last_observation(self) -> Optional[ToolObservation]:
        """Get the most recent observation."""
        for step in reversed(self.steps):
            if step.observation:
                return step.observation
        return None
    
    @property
    def tools_used(self) -> List[str]:
        """
        Get list of unique tools used in this trajectory.
        
        Excludes the 'finish' pseudo-tool as it's not a real tool execution.
        """
        tools = []
        for step in self.steps:
            if (step.tool_invocation and 
                step.tool_invocation.tool_name != "finish" and
                step.tool_invocation.tool_name not in tools):
                tools.append(step.tool_invocation.tool_name)
        return tools
    
    @property
    def total_execution_time_ms(self) -> float:
        """Calculate total execution time across all tools."""
        return sum(
            step.observation.execution_time_ms 
            for step in self.steps 
            if step.observation
        )
    
    def add_step(
        self,
        thought: str,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None
    ) -> TrajectoryStep:
        """
        Add a new step to the trajectory.
        
        Args:
            thought: The agent's reasoning for this step
            tool_name: Name of the tool to invoke (including 'finish')
            tool_args: Arguments for the tool (empty dict for 'finish')
            
        Returns:
            The newly created TrajectoryStep
        """
        step = TrajectoryStep(
            iteration=self.iteration_count + 1,
            thought=ThoughtStep(content=thought),
            tool_invocation=ToolInvocation(
                tool_name=tool_name,
                tool_args=tool_args or {}
            ) if tool_name else None
        )
        self.steps.append(step)
        return step
    
    def add_observation(
        self,
        tool_name: str,
        status: ToolStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        execution_time_ms: float = 0
    ) -> None:
        """Add an observation to the most recent step."""
        if not self.steps:
            raise ValueError("Cannot add observation without any steps")
        
        if self.steps[-1].observation is not None:
            raise ValueError("Step already has an observation")
        
        # Create a new step with the observation (Pydantic models are immutable)
        last_step = self.steps[-1]
        updated_step = TrajectoryStep(
            iteration=last_step.iteration,
            thought=last_step.thought,
            tool_invocation=last_step.tool_invocation,
            observation=ToolObservation(
                tool_name=tool_name,
                status=status,
                result=result,
                error=error,
                execution_time_ms=execution_time_ms
            )
        )
        self.steps[-1] = updated_step
    
    def to_llm_format(self) -> str:
        """Format trajectory for LLM consumption."""
        lines = [f"User Query: {self.user_query}\n"]
        
        for step in self.steps:
            lines.append(f"Iteration {step.iteration}:")
            lines.append(f"  Thought: {step.thought.content}")
            
            if step.tool_invocation:
                lines.append(f"  Tool: {step.tool_invocation.tool_name}")
                if step.tool_invocation.tool_args:
                    lines.append(f"  Args: {step.tool_invocation.tool_args}")
            
            if step.observation:
                if step.observation.status == ToolStatus.SUCCESS:
                    lines.append(f"  Result: {step.observation.result}")
                else:
                    lines.append(f"  Error: {step.observation.error}")
            elif step.is_finish:
                # The finish tool doesn't produce an observation
                lines.append("  Status: Task complete, ready for answer extraction")
        
        return "\n".join(lines)


class ExtractResult(BaseModel):
    """Result from the Extract agent."""
    model_config = ConfigDict(frozen=True)
    
    answer: str = Field(
        ...,
        description="The final answer extracted from the trajectory"
    )
    reasoning: str = Field(
        default="",
        description="The reasoning process used to extract the answer"
    )