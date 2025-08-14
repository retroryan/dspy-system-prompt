"""
Conversation history models for managing multi-trajectory conversations.

This module provides type-safe Pydantic models for conversation history management,
enabling agents to maintain context across multiple interactions. The models support
intelligent summarization of removed trajectories and configurable memory management.

Following DSPy best practices, all models are immutable (frozen=True) to ensure
data integrity and prevent accidental state mutations.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ConversationSummary(BaseModel):
    """
    Represents an intelligent summary of removed trajectories.
    
    When trajectories are removed from active history due to memory constraints,
    they are summarized using the Extract agent to preserve key information.
    This allows the agent to maintain awareness of earlier interactions without
    keeping the full trajectory data in memory.
    
    Attributes:
        trajectory_count: Number of trajectories included in this summary
        total_steps: Total number of steps across all summarized trajectories
        tools_used: List of unique tool names used in the summarized trajectories
        summary_text: Natural language summary created by Extract agent
        created_at: Timestamp when this summary was created
    """
    model_config = ConfigDict(frozen=True)
    
    trajectory_count: int = Field(
        ...,
        ge=1,
        description="Number of trajectories summarized"
    )
    total_steps: int = Field(
        ...,
        ge=0,
        description="Total steps across summarized trajectories"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools used in summarized trajectories"
    )
    summary_text: str = Field(
        ...,
        min_length=1,
        description="Natural language summary of removed trajectories"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this summary was created"
    )


class ConversationHistoryConfig(BaseModel):
    """
    Configuration for conversation history management.
    
    Controls how the conversation history manager maintains trajectories,
    creates summaries, and manages memory. The sliding window approach
    preserves recent and initial trajectories while summarizing removed ones.
    
    Attributes:
        max_trajectories: Maximum number of complete trajectories to keep in memory
        summarize_removed: Whether to create summaries of removed trajectories
        preserve_first_trajectories: Number of initial trajectories to always keep
        preserve_last_trajectories: Number of recent trajectories to always keep
    """
    model_config = ConfigDict(frozen=True)
    
    max_trajectories: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of complete trajectories to keep in memory"
    )
    summarize_removed: bool = Field(
        default=True,
        description="Whether to create summaries of removed trajectories"
    )
    preserve_first_trajectories: int = Field(
        default=1,
        ge=0,
        description="Always keep first N trajectories for context continuity"
    )
    preserve_last_trajectories: int = Field(
        default=7,
        ge=1,
        description="Always keep last N trajectories (most recent interactions)"
    )
    
    def model_post_init(self, __context):
        """Validate that preservation settings are coherent."""
        if self.preserve_first_trajectories + self.preserve_last_trajectories > self.max_trajectories:
            raise ValueError(
                f"Sum of preserve_first ({self.preserve_first_trajectories}) and "
                f"preserve_last ({self.preserve_last_trajectories}) cannot exceed "
                f"max_trajectories ({self.max_trajectories})"
            )