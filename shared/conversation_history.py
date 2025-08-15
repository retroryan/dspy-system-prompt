"""
Conversation history management for multi-trajectory agent interactions.

This module provides the ConversationHistory class that manages multiple trajectories
across user interactions, implementing intelligent summarization and sliding window
memory management. It enables agents to maintain context across conversations while
managing memory efficiently.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import dspy

from shared.conversation_models import ConversationSummary, ConversationHistoryConfig
from shared.trajectory_models import Trajectory
from agentic_loop.extract_agent import ReactExtract

logger = logging.getLogger(__name__)


class ConversationHistory:
    """
    Manages complete conversation history across multiple agent interactions.
    
    This class maintains a list of trajectories, where each trajectory represents
    one complete user query and agent response cycle. It provides:
    
    - Memory management through sliding window on trajectories
    - Intelligent summarization of removed trajectories using Extract agent
    - Context building for agents to maintain conversation continuity
    - Full conversation history visualization
    
    Attributes:
        config: Configuration for history management
        trajectories: List of active trajectories in memory
        summaries: List of summaries for removed trajectories
        total_trajectories_processed: Total count of trajectories ever processed
    """
    
    def __init__(self, config: Optional[ConversationHistoryConfig] = None):
        """
        Initialize conversation history with configuration.
        
        Args:
            config: Optional configuration for history management.
                   Uses default ConversationHistoryConfig if not provided.
        """
        self.config = config or ConversationHistoryConfig()
        self.trajectories: List[Trajectory] = []
        self.summaries: List[ConversationSummary] = []
        self.total_trajectories_processed = 0
        
        logger.debug(f"Initialized ConversationHistory with config: {self.config}")
    
    def add_trajectory(self, trajectory: Trajectory) -> None:
        """
        Add a new trajectory to the conversation history.
        
        This method:
        1. Adds the trajectory to the active list
        2. Increments the total processed counter
        3. Applies sliding window management if needed
        4. Creates summaries of removed trajectories if configured
        
        Args:
            trajectory: The completed trajectory to add to history
        """
        # Add to history
        self.trajectories.append(trajectory)
        self.total_trajectories_processed += 1
        
        logger.debug(f"Added trajectory #{self.total_trajectories_processed} to history")
        
        # Apply trajectory-level management
        self._apply_trajectory_window()
    
    def _apply_trajectory_window(self) -> None:
        """
        Apply sliding window to the trajectory list.
        
        This removes old trajectories when the list exceeds max_trajectories,
        optionally creating intelligent summaries of removed content using
        the Extract agent.
        """
        if len(self.trajectories) <= self.config.max_trajectories:
            return
        
        logger.debug(f"Applying trajectory window: {len(self.trajectories)} > {self.config.max_trajectories}")
        
        # Calculate how many to remove
        excess = len(self.trajectories) - self.config.max_trajectories
        
        # Determine what to preserve
        preserve_first = min(self.config.preserve_first_trajectories, len(self.trajectories))
        preserve_last = min(self.config.preserve_last_trajectories, len(self.trajectories))
        
        # Ensure we don't preserve more than max
        if preserve_first + preserve_last > self.config.max_trajectories:
            preserve_first = self.config.max_trajectories // 2
            preserve_last = self.config.max_trajectories - preserve_first
            logger.warning(f"Adjusted preservation: first={preserve_first}, last={preserve_last}")
        
        # Identify trajectories to remove (from the middle)
        if preserve_first + preserve_last < len(self.trajectories):
            # Calculate range to remove
            remove_start = preserve_first
            remove_end = len(self.trajectories) - preserve_last
            to_remove = self.trajectories[remove_start:remove_end]
            
            logger.debug(f"Removing {len(to_remove)} trajectories from position {remove_start} to {remove_end}")
            
            # Create summary if configured
            if self.config.summarize_removed and to_remove:
                summary = self._create_summary(to_remove)
                self.summaries.append(summary)
                logger.info(f"Created summary of {len(to_remove)} trajectories")
            
            # Keep only preserved trajectories
            self.trajectories = (
                self.trajectories[:preserve_first] + 
                self.trajectories[-preserve_last:]
            )
    
    def _create_summary(self, trajectories: List[Trajectory]) -> ConversationSummary:
        """
        Create an intelligent summary of trajectories being removed using Extract agent.
        
        This uses DSPy's Extract agent to synthesize a natural language summary
        of the removed trajectories, providing better context preservation than
        simple concatenation.
        
        Args:
            trajectories: List of trajectories to summarize
            
        Returns:
            ConversationSummary object with intelligent summary
        """
        # Aggregate basic information
        total_steps = sum(len(t.steps) for t in trajectories)
        
        # Collect all unique tools used
        all_tools = set()
        for trajectory in trajectories:
            for step in trajectory.steps:
                if step.tool_invocation and step.tool_invocation.tool_name != "finish":
                    all_tools.add(step.tool_invocation.tool_name)
        
        # Format trajectories for summarization
        trajectories_text = self._format_trajectories_for_summary(trajectories)
        
        try:
            # Use Extract agent to create intelligent summary
            class SummarySignature(dspy.Signature):
                """Create a concise summary of conversation trajectories."""
                trajectories_text = dspy.InputField(desc="Text representation of trajectories")
                summary = dspy.OutputField(desc="Concise summary of key interactions and outcomes")
            
            # Create and run Extract agent
            extract = ReactExtract(signature=SummarySignature)
            result = extract(trajectories_text=trajectories_text)
            
            summary_text = result.summary
            logger.debug(f"Extract agent created summary: {summary_text[:100]}...")
            
        except Exception as e:
            # Fallback to simple summary if Extract agent fails
            logger.warning(f"Extract agent failed, using fallback summary: {e}")
            queries = [t.user_query for t in trajectories]
            summary_text = (
                f"Summarized {len(trajectories)} interactions: "
                f"Queries included {', '.join(queries[:3])}" + 
                ("..." if len(queries) > 3 else "")
            )
        
        return ConversationSummary(
            trajectory_count=len(trajectories),
            total_steps=total_steps,
            tools_used=sorted(list(all_tools)),
            summary_text=summary_text
        )
    
    def _format_trajectories_for_summary(self, trajectories: List[Trajectory]) -> str:
        """
        Format trajectories into text for summarization by Extract agent.
        
        Args:
            trajectories: List of trajectories to format
            
        Returns:
            Formatted text representation of trajectories
        """
        lines = []
        for i, traj in enumerate(trajectories, 1):
            lines.append(f"Interaction {i}:")
            lines.append(f"  User Query: {traj.user_query}")
            
            # Include key tool usage
            tools_used = []
            for step in traj.steps:
                if step.tool_invocation and step.tool_invocation.tool_name != "finish":
                    tools_used.append(step.tool_invocation.tool_name)
            
            if tools_used:
                lines.append(f"  Tools Used: {', '.join(set(tools_used))}")
            
            # Include final observation if available
            if traj.last_observation and traj.last_observation.result:
                result_str = str(traj.last_observation.result)
                if len(result_str) > 100:
                    result_str = result_str[:100] + "..."
                lines.append(f"  Key Result: {result_str}")
            
            lines.append("")  # Blank line between interactions
        
        return "\n".join(lines)
    
    def get_context_for_agent(self) -> Dict[str, Any]:
        """
        Get the conversation context formatted for the agent.
        
        Returns a dictionary containing current trajectories, summaries,
        and metadata about the conversation history.
        
        Returns:
            Dictionary with conversation context including:
            - trajectories: Current trajectories in memory
            - trajectory_count: Number of active trajectories
            - total_processed: Total trajectories ever processed
            - summaries: List of summaries for removed trajectories
            - has_summaries: Boolean indicating if summaries exist
            - summary_info: Aggregated information about summaries
        """
        context = {
            "trajectories": self.trajectories,
            "trajectory_count": len(self.trajectories),
            "total_processed": self.total_trajectories_processed,
            "summaries": self.summaries,
            "has_summaries": len(self.summaries) > 0
        }
        
        # Add summary information if available
        if self.summaries:
            context["summary_info"] = {
                "total_summarized_trajectories": sum(s.trajectory_count for s in self.summaries),
                "total_summarized_steps": sum(s.total_steps for s in self.summaries),
                "all_tools_used": list(set().union(*[set(s.tools_used) for s in self.summaries]))
            }
        
        return context
    
    def get_full_history_text(self) -> str:
        """
        Get a text representation of the full conversation history.
        
        This is useful for debugging, logging, or displaying to users.
        Includes both summaries and active trajectories with key information.
        
        Returns:
            Formatted string with conversation history
        """
        lines = []
        
        # Add summaries if present
        if self.summaries:
            lines.append("=== SUMMARIZED HISTORY ===")
            for i, summary in enumerate(self.summaries, 1):
                lines.append(f"\nSummary {i} (created {summary.created_at.strftime('%H:%M:%S')}):")
                lines.append(f"  {summary.summary_text}")
                lines.append(f"  - Trajectories: {summary.trajectory_count}")
                lines.append(f"  - Total Steps: {summary.total_steps}")
                if summary.tools_used:
                    lines.append(f"  - Tools Used: {', '.join(summary.tools_used)}")
            lines.append("")
        
        # Add current trajectories
        lines.append("=== ACTIVE CONVERSATION ===")
        for i, trajectory in enumerate(self.trajectories, 1):
            lines.append(f"\nInteraction {i}:")
            lines.append(f"  Query: {trajectory.user_query}")
            lines.append(f"  Steps: {len(trajectory.steps)}")
            lines.append(f"  Started: {trajectory.started_at.strftime('%H:%M:%S')}")
            
            if trajectory.completed_at:
                lines.append(f"  Completed: {trajectory.completed_at.strftime('%H:%M:%S')}")
            else:
                lines.append(f"  Status: In Progress")
            
            # Show tool usage
            if trajectory.tools_used:
                lines.append(f"  Tools: {', '.join(trajectory.tools_used)}")
            
            # Show first few steps
            for step in trajectory.steps[:2]:  # Show first 2 steps
                tool = step.tool_invocation.tool_name if step.tool_invocation else "thinking"
                lines.append(f"    - Step {step.iteration}: {tool}")
            
            if len(trajectory.steps) > 2:
                lines.append(f"    ... and {len(trajectory.steps) - 2} more steps")
        
        # Add statistics
        lines.append("\n=== STATISTICS ===")
        lines.append(f"Total Interactions Processed: {self.total_trajectories_processed}")
        lines.append(f"Active Trajectories: {len(self.trajectories)}")
        lines.append(f"Summarized Groups: {len(self.summaries)}")
        
        if self.summaries:
            total_summarized = sum(s.trajectory_count for s in self.summaries)
            lines.append(f"Total Summarized Trajectories: {total_summarized}")
        
        return "\n".join(lines)
    
    def build_context_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build a context prompt string for passing to agents.
        
        Creates a structured context string that includes summaries of past
        interactions and recent trajectory information, formatted for agent
        consumption.
        
        Args:
            context: Optional pre-computed context dictionary.
                    If not provided, calls get_context_for_agent().
        
        Returns:
            Formatted context string for agent input
        """
        if context is None:
            context = self.get_context_for_agent()
        
        if not context["trajectories"] and not context["summaries"]:
            return "No previous conversation history."
        
        lines = []
        
        # Add summary context if available
        if context["summaries"]:
            lines.append("Previous Conversation Summary:")
            for summary in context["summaries"][-2:]:  # Last 2 summaries
                lines.append(f"- {summary.summary_text}")
            lines.append("")
        
        # Add recent trajectory information
        if context["trajectories"]:
            recent_trajectories = context["trajectories"][-3:]  # Last 3 interactions
            
            if recent_trajectories:
                lines.append("Recent Interactions:")
                for i, traj in enumerate(recent_trajectories, 1):
                    query_preview = traj.user_query[:50] + "..." if len(traj.user_query) > 50 else traj.user_query
                    
                    tools = ", ".join(traj.tools_used) if traj.tools_used else "reasoning only"
                    lines.append(f"{i}. Query: {query_preview} (Used: {tools})")
        
        return "\n".join(lines) if lines else "Starting new conversation."
    
    def clear_history(self, keep_last: int = 0) -> None:
        """
        Clear conversation history, optionally keeping recent trajectories.
        
        Args:
            keep_last: Number of recent trajectories to preserve (default: 0)
        """
        if keep_last > 0:
            self.trajectories = self.trajectories[-keep_last:]
        else:
            self.trajectories = []
        
        self.summaries = []
        self.total_trajectories_processed = len(self.trajectories)
        
        logger.info(f"Cleared history, kept {len(self.trajectories)} trajectories")