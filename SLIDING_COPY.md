# Sliding Window Conversation Manager for DSPy Agentic Loop

## Executive Summary

This document outlines a comprehensive conversation history management system for DSPy agentic loops. Unlike single-trajectory management, this system maintains a complete history of multiple trajectories across user interactions, inspired by AWS Strands' approach but adapted for DSPy's synchronous, type-safe architecture.

The key innovation is managing a list of trajectories (complete agent interactions) rather than just managing steps within a single trajectory. This provides full conversation context while intelligently managing memory through sliding window techniques.

### Implementation Decisions (Confirmed)
- **Context Passing**: Option A - Context via Signature Input Fields
- **Summary Generation**: Use Extract agent for intelligent summaries
- **Trajectory Metadata**: Add metadata field to Trajectory model
- **Test Cases**: Create custom conversation-oriented questions
- **Window Size**: max_trajectories=10 for demonstration
- **Extract Context**: Pass context to Extract agent for better synthesis

## Core Concept

Our system manages conversation history at two levels:

### Level 1: Trajectory Management (New)
- Maintains a list of complete `Trajectory` objects from multiple user interactions
- Each trajectory represents one complete React-Extract cycle
- Sliding window manages the number of trajectories in memory
- Preserves recent trajectories while summarizing or removing older ones

### Level 2: Step Management (Existing)
- Within each trajectory, manages individual `TrajectoryStep` objects
- Preserves complete steps (thought + tool invocation + observation)
- Truncates large observations when needed
- Maintains React pattern coherence

## Proposed Architecture

### 1. ConversationHistory Class (New)

This is the top-level manager that maintains multiple trajectories across the entire conversation:

```python
# File: shared/conversation_history.py

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from shared.trajectory_models import Trajectory
from shared.sliding_window import SlidingWindowManager, SlidingWindowConfig

class ConversationSummary(BaseModel):
    """Represents a summary of removed trajectories."""
    model_config = ConfigDict(frozen=True)
    
    trajectory_count: int = Field(
        description="Number of trajectories summarized"
    )
    total_steps: int = Field(
        description="Total steps across summarized trajectories"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools used in summarized trajectories"
    )
    summary_text: str = Field(
        description="Natural language summary of removed trajectories"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this summary was created"
    )

class ConversationHistoryConfig(BaseModel):
    """Configuration for conversation history management."""
    model_config = ConfigDict(frozen=True)
    
    max_trajectories: int = Field(
        default=10,
        ge=1,
        description="Maximum number of complete trajectories to keep in memory"
    )
    summarize_removed: bool = Field(
        default=True,
        description="Whether to create summaries of removed trajectories"
    )
    step_window_config: Optional[SlidingWindowConfig] = Field(
        default=None,
        description="Configuration for managing steps within each trajectory"
    )
    preserve_first_trajectories: int = Field(
        default=1,
        ge=0,
        description="Always keep first N trajectories for context continuity"
    )
    preserve_last_trajectories: int = Field(
        default=5,
        ge=1,
        description="Always keep last N trajectories (most recent interactions)"
    )

class ConversationHistory:
    """
    Manages complete conversation history across multiple agent interactions.
    
    This class maintains a list of trajectories, where each trajectory represents
    one complete user query and agent response cycle. It provides:
    
    - Memory management through sliding window on trajectories
    - Optional summarization of removed trajectories
    - Nested step management within each trajectory
    - Full conversation context for the agent
    """
    
    def __init__(self, config: Optional[ConversationHistoryConfig] = None):
        """Initialize conversation history with configuration."""
        self.config = config or ConversationHistoryConfig()
        self.trajectories: List[Trajectory] = []
        self.summaries: List[ConversationSummary] = []
        self.step_manager = SlidingWindowManager(self.config.step_window_config) if self.config.step_window_config else None
        self.total_trajectories_processed = 0
    
    def add_trajectory(self, trajectory: Trajectory) -> None:
        """
        Add a new trajectory to the conversation history.
        
        This method:
        1. Applies step-level window management to the trajectory
        2. Adds it to the trajectory list
        3. Applies trajectory-level window management
        4. Creates summaries if needed
        
        Args:
            trajectory: The completed trajectory to add
        """
        # Apply step-level management if configured
        if self.step_manager:
            trajectory = self.step_manager.apply_window(trajectory)
        
        # Add to history
        self.trajectories.append(trajectory)
        self.total_trajectories_processed += 1
        
        # Apply trajectory-level management
        self._apply_trajectory_window()
    
    def _apply_trajectory_window(self) -> None:
        """
        Apply sliding window to the trajectory list.
        
        This removes old trajectories when the list exceeds max_trajectories,
        optionally creating summaries of removed content.
        """
        if len(self.trajectories) <= self.config.max_trajectories:
            return
        
        # Calculate how many to remove
        excess = len(self.trajectories) - self.config.max_trajectories
        
        # Determine what to preserve
        preserve_first = min(self.config.preserve_first_trajectories, len(self.trajectories))
        preserve_last = min(self.config.preserve_last_trajectories, len(self.trajectories))
        
        # Ensure we don't preserve more than max
        if preserve_first + preserve_last > self.config.max_trajectories:
            preserve_first = self.config.max_trajectories // 2
            preserve_last = self.config.max_trajectories - preserve_first
        
        # Identify trajectories to remove (from the middle)
        to_remove = self.trajectories[preserve_first:len(self.trajectories)-preserve_last]
        
        # Create summary if configured
        if self.config.summarize_removed and to_remove:
            summary = self._create_summary(to_remove)
            self.summaries.append(summary)
        
        # Keep only preserved trajectories
        self.trajectories = (
            self.trajectories[:preserve_first] + 
            self.trajectories[-preserve_last:]
        )
    
    def _create_summary(self, trajectories: List[Trajectory]) -> ConversationSummary:
        """
        Create an intelligent summary of trajectories being removed using Extract agent.
        
        This uses DSPy's Extract agent to synthesize a natural language summary
        of the removed trajectories, providing better context preservation.
        
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
                if step.tool_invocation:
                    all_tools.add(step.tool_invocation.tool_name)
        
        # Use Extract agent to create intelligent summary
        class SummarySignature(dspy.Signature):
            """Create a concise summary of conversation trajectories."""
            trajectories_text = dspy.InputField(desc="Text representation of trajectories")
            summary = dspy.OutputField(desc="Concise summary of key interactions and outcomes")
        
        # Format trajectories for summarization
        trajectories_text = self._format_trajectories_for_summary(trajectories)
        
        # Create and run Extract agent
        from agentic_loop.extract_agent import ReactExtract
        extract = ReactExtract(signature=SummarySignature)
        result = extract(trajectories_text=trajectories_text)
        
        return ConversationSummary(
            trajectory_count=len(trajectories),
            total_steps=total_steps,
            tools_used=sorted(list(all_tools)),
            summary_text=result.summary
        )
    
    def _format_trajectories_for_summary(self, trajectories: List[Trajectory]) -> str:
        """Format trajectories into text for summarization."""
        lines = []
        for i, traj in enumerate(trajectories, 1):
            lines.append(f"Interaction {i}: {traj.user_query}")
            # Include key outcomes or tool results
            if traj.steps:
                tools = [s.tool_invocation.tool_name for s in traj.steps 
                        if s.tool_invocation and s.tool_invocation.tool_name != "finish"]
                if tools:
                    lines.append(f"  Tools used: {', '.join(tools)}")
        return "\n".join(lines)
    
    def get_context_for_agent(self) -> Dict[str, Any]:
        """
        Get the conversation context formatted for the agent.
        
        Returns a dictionary containing:
        - Current trajectories
        - Summaries of removed trajectories
        - Metadata about the conversation
        
        Returns:
            Dictionary with conversation context
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
        
        This is useful for debugging or displaying to users.
        
        Returns:
            Formatted string with conversation history
        """
        lines = []
        
        # Add summaries if present
        if self.summaries:
            lines.append("=== SUMMARIZED HISTORY ===")
            for i, summary in enumerate(self.summaries, 1):
                lines.append(f"\nSummary {i}: {summary.summary_text}")
                lines.append(f"  - Trajectories: {summary.trajectory_count}")
                lines.append(f"  - Total Steps: {summary.total_steps}")
                lines.append(f"  - Tools Used: {', '.join(summary.tools_used)}")
            lines.append("")
        
        # Add current trajectories
        lines.append("=== ACTIVE CONVERSATION ===")
        for i, trajectory in enumerate(self.trajectories, 1):
            lines.append(f"\nInteraction {i}:")
            lines.append(f"  Query: {trajectory.user_query}")
            lines.append(f"  Steps: {len(trajectory.steps)}")
            lines.append(f"  Status: {'Completed' if trajectory.completed_at else 'In Progress'}")
            
            # Show brief step summary
            for step in trajectory.steps[:3]:  # Show first 3 steps
                tool = step.tool_invocation.tool_name if step.tool_invocation else "thinking"
                lines.append(f"    - Step {step.iteration}: {tool}")
            
            if len(trajectory.steps) > 3:
                lines.append(f"    ... and {len(trajectory.steps) - 3} more steps")
        
        return "\n".join(lines)
    
    def clear_history(self, keep_last: int = 0) -> None:
        """
        Clear conversation history, optionally keeping recent trajectories.
        
        Args:
            keep_last: Number of recent trajectories to preserve
        """
        if keep_last > 0:
            self.trajectories = self.trajectories[-keep_last:]
        else:
            self.trajectories = []
        
        self.summaries = []
        self.total_trajectories_processed = len(self.trajectories)
```

### 2. SlidingWindowManager Class (Existing, with improvements)

```python
# File: shared/sliding_window.py

from typing import Optional, Set, List
from pydantic import BaseModel, Field, ConfigDict
from shared.trajectory_models import (
    Trajectory, 
    TrajectoryStep, 
    ThoughtStep,
    ToolInvocation,
    ToolObservation,
    ToolStatus
)

class SlidingWindowConfig(BaseModel):
    """Configuration for sliding window behavior using Pydantic."""
    model_config = ConfigDict(frozen=True)
    
    max_steps: int = Field(
        default=10,
        ge=1,
        description="Maximum number of trajectory steps to keep"
    )
    truncate_observations: bool = Field(
        default=True,
        description="Whether to truncate large observations before removing steps"
    )
    observation_max_chars: int = Field(
        default=500,
        ge=100,
        description="Maximum characters per tool observation"
    )
    preserve_first_steps: int = Field(
        default=1,
        ge=0,
        description="Always keep first N steps for context continuity"
    )
    preserve_last_steps: int = Field(
        default=5,
        ge=1,
        description="Always keep last N steps (most recent context)"
    )


class WindowMetadata(BaseModel):
    """Metadata about the sliding window operations performed."""
    model_config = ConfigDict(frozen=True)
    
    steps_removed: int = Field(
        default=0,
        description="Total number of steps removed"
    )
    observations_truncated: Set[int] = Field(
        default_factory=set,
        description="Iteration numbers of truncated observations"
    )
    window_applied: bool = Field(
        default=False,
        description="Whether the window was applied to this trajectory"
    )
    original_step_count: int = Field(
        default=0,
        description="Original number of steps before windowing"
    )


class SlidingWindowManager:
    """
    Manages trajectory size using a sliding window approach with Pydantic models.
    
    This manager works with the type-safe Trajectory object, preserving
    complete TrajectoryStep objects to maintain coherence in the React pattern.
    """
    
    def __init__(self, config: Optional[SlidingWindowConfig] = None):
        """Initialize with configuration."""
        self.config = config or SlidingWindowConfig()
        self.metadata = WindowMetadata()
    
    def apply_window(self, trajectory: Trajectory) -> Trajectory:
        """
        Apply sliding window to trajectory, maintaining complete steps.
        
        Args:
            trajectory: The current Trajectory object
            
        Returns:
            A new Trajectory with window applied if needed
        """
        original_count = len(trajectory.steps)
        
        # Check if window needs to be applied
        if original_count <= self.config.max_steps:
            return trajectory
        
        # Create a working copy of steps
        steps = list(trajectory.steps)
        
        # Try truncating large observations first
        if self.config.truncate_observations:
            steps = self._truncate_large_observations(steps)
            
            # If truncation was enough, update and return
            if self._estimate_size(steps) <= self._estimate_size_limit():
                return self._create_windowed_trajectory(trajectory, steps, original_count)
        
        # Apply step removal strategy
        steps = self._apply_step_removal(steps)
        
        # Create new trajectory with windowed steps
        return self._create_windowed_trajectory(trajectory, steps, original_count)
    
    def _truncate_large_observations(self, steps: List[TrajectoryStep]) -> List[TrajectoryStep]:
        """
        Truncate large observations to reduce context size.
        
        Since TrajectoryStep is immutable (frozen=True), we need to create
        new instances with truncated observations.
        """
        modified_steps = []
        
        for step in steps:
            if step.observation and step.observation.result:
                result_str = str(step.observation.result)
                
                if len(result_str) > self.config.observation_max_chars:
                    # Create truncated observation
                    truncated_result = (
                        f"[TRUNCATED: {len(result_str)} chars → "
                        f"{self.config.observation_max_chars} chars]\n"
                        f"{result_str[:self.config.observation_max_chars]}..."
                    )
                    
                    # Create new observation with truncated result
                    new_observation = ToolObservation(
                        tool_name=step.observation.tool_name,
                        status=step.observation.status,
                        result=truncated_result,
                        error=step.observation.error,
                        execution_time_ms=step.observation.execution_time_ms
                    )
                    
                    # Create new step with truncated observation
                    new_step = TrajectoryStep(
                        iteration=step.iteration,
                        thought=step.thought,
                        tool_invocation=step.tool_invocation,
                        observation=new_observation
                    )
                    
                    modified_steps.append(new_step)
                    
                    # Track truncation in metadata
                    self.metadata = WindowMetadata(
                        steps_removed=self.metadata.steps_removed,
                        observations_truncated=self.metadata.observations_truncated | {step.iteration},
                        window_applied=True,
                        original_step_count=self.metadata.original_step_count
                    )
                else:
                    modified_steps.append(step)
            else:
                modified_steps.append(step)
        
        return modified_steps
    
    def _apply_step_removal(self, steps: List[TrajectoryStep]) -> List[TrajectoryStep]:
        """
        Remove steps according to preservation strategy.
        
        Preserves:
        - First N steps (for initial context)
        - Last M steps (for recent context)
        - Removes middle steps to fit within max_steps
        """
        if len(steps) <= self.config.max_steps:
            return steps
        
        # Calculate indices
        preserve_first = min(self.config.preserve_first_steps, len(steps))
        preserve_last = min(self.config.preserve_last_steps, len(steps))
        
        # Ensure we don't preserve more than max_steps
        if preserve_first + preserve_last > self.config.max_steps:
            # Adjust preservation to fit within limits
            preserve_first = self.config.max_steps // 2
            preserve_last = self.config.max_steps - preserve_first
        
        # Select steps to keep
        kept_steps = []
        
        # Add first N steps
        kept_steps.extend(steps[:preserve_first])
        
        # Add last M steps
        if preserve_last > 0:
            kept_steps.extend(steps[-preserve_last:])
        
        # Update metadata
        removed_count = len(steps) - len(kept_steps)
        self.metadata = WindowMetadata(
            steps_removed=self.metadata.steps_removed + removed_count,
            observations_truncated=self.metadata.observations_truncated,
            window_applied=True,
            original_step_count=len(steps)
        )
        
        # Renumber iterations to maintain continuity
        renumbered_steps = []
        for idx, step in enumerate(kept_steps, start=1):
            renumbered_step = TrajectoryStep(
                iteration=idx,
                thought=step.thought,
                tool_invocation=step.tool_invocation,
                observation=step.observation
            )
            renumbered_steps.append(renumbered_step)
        
        return renumbered_steps
    
    def _estimate_size(self, steps: List[TrajectoryStep]) -> int:
        """Estimate the total size of steps in characters for context management."""
        total_size = 0
        for step in steps:
            # Count thought
            total_size += len(step.thought.content)
            
            # Count tool invocation
            if step.tool_invocation:
                total_size += len(step.tool_invocation.tool_name)
                total_size += len(str(step.tool_invocation.tool_args))
            
            # Count observation
            if step.observation:
                if step.observation.result:
                    total_size += len(str(step.observation.result))
                if step.observation.error:
                    total_size += len(step.observation.error)
        
        return total_size
    
    def _estimate_size_limit(self) -> int:
        """Calculate the approximate size limit based on configuration."""
        # Rough estimate: max_steps * average content per step
        avg_thought_size = 200  # Estimated average thought size
        avg_observation_size = self.config.observation_max_chars
        return self.config.max_steps * (avg_thought_size + avg_observation_size)
    
    def _create_windowed_trajectory(
        self, 
        original: Trajectory, 
        steps: List[TrajectoryStep],
        original_count: int
    ) -> Trajectory:
        """Create a new Trajectory with windowed steps and metadata."""
        
        # Create new trajectory with windowed steps
        windowed = Trajectory(
            user_query=original.user_query,
            steps=steps,
            started_at=original.started_at,
            completed_at=original.completed_at,
            tool_set_name=original.tool_set_name,
            max_iterations=original.max_iterations
        )
        
        # Add window metadata as a property (would need to extend Trajectory model)
        # For now, we can add a summary to the trajectory
        if self.metadata.window_applied and self.metadata.steps_removed > 0:
            # Inject a context note in the first step's thought
            if windowed.steps:
                first_step = windowed.steps[0]
                context_note = (
                    f"[Context: {self.metadata.steps_removed} earlier steps "
                    f"removed from trajectory. Original: {original_count} steps, "
                    f"Current: {len(steps)} steps]"
                )
                
                # Create new first step with context note
                new_thought = ThoughtStep(
                    content=f"{context_note}\n\n{first_step.thought.content}"
                )
                
                windowed.steps[0] = TrajectoryStep(
                    iteration=first_step.iteration,
                    thought=new_thought,
                    tool_invocation=first_step.tool_invocation,
                    observation=first_step.observation
                )
        
        return windowed
    
    def get_metadata(self) -> WindowMetadata:
        """Get the current window metadata."""
        return self.metadata
    
    def reset_metadata(self) -> None:
        """Reset the window metadata for a new trajectory."""
        self.metadata = WindowMetadata()
```

### 3. Integration with Core Loop (Using Option A: Context via Signature)

Based on DSPy's established patterns, we'll pass conversation context as a separate InputField in the signature. This follows the same pattern used in DSPy's test_baleen.py and other examples:

```python
# File: agentic_loop/demo_conversation_history.py

import dspy
from typing import Optional, Dict, Any
from shared.conversation_history import ConversationHistory, ConversationHistoryConfig
from shared.sliding_window import SlidingWindowConfig
from shared.trajectory_models import Trajectory, ToolStatus
from agentic_loop.react_agent import ReactAgent
from agentic_loop.extract_agent import ExtractAgent

# Define signatures with context field (following DSPy convention)
class ConversationReactSignature(dspy.Signature):
    """React signature with conversation context support."""
    context = dspy.InputField(desc="Summary of previous conversation interactions")
    user_query = dspy.InputField(desc="The user's current question or request")
    final_answer = dspy.OutputField(desc="The comprehensive answer based on context and current query")

class ConversationExtractSignature(dspy.Signature):
    """Extract signature with conversation context for better synthesis."""
    context = dspy.InputField(desc="Summary of previous conversation interactions")
    user_query = dspy.InputField(desc="The user's current question")
    trajectory = dspy.InputField(desc="Current interaction trajectory")
    answer = dspy.OutputField(desc="Synthesized answer considering full conversation context")

class ConversationAgent:
    """
    Agent that maintains conversation history across multiple interactions.
    
    This wraps the React-Extract pattern with conversation history management,
    providing context from previous interactions to improve responses.
    """
    
    def __init__(
        self,
        tool_registry,
        history_config: Optional[ConversationHistoryConfig] = None
    ):
        """Initialize agent with conversation history."""
        self.tool_registry = tool_registry
        self.history = ConversationHistory(history_config)
        
        # Create React agent with context-aware signature
        self.react_agent = ReactAgent(
            signature=ConversationReactSignature,
            tool_registry=tool_registry
        )
        # Create Extract agent with context-aware signature for better synthesis
        self.extract_agent = ReactExtract(signature=ConversationExtractSignature)
    
    def process_query(
        self,
        user_query: str,
        tool_set_name: str,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Process a user query with full conversation context.
        
        Args:
            user_query: The user's question or request
            tool_set_name: Name of the tool set to use
            max_iterations: Maximum React iterations
            
        Returns:
            Dictionary with trajectory and final answer
        """
        # Get conversation context
        context = self.history.get_context_for_agent()
        
        # Create trajectory with metadata field (added to Trajectory model)
        trajectory = Trajectory(
            user_query=user_query,
            tool_set_name=tool_set_name,
            max_iterations=max_iterations,
            metadata={  # New metadata field in Trajectory model
                "conversation_context": {
                    "previous_interactions": context["trajectory_count"],
                    "total_interactions": context["total_processed"],
                    "has_summaries": context["has_summaries"],
                    "context_string": context_string  # Store for Extract agent
                }
            }
        )
        
        # Build context string from history
        context_string = self._build_context_prompt(context) if context["trajectories"] else "No previous conversation history."
        
        # Store context in trajectory metadata for Extract agent
        trajectory.metadata["conversation_context"]["context_string"] = context_string
        
        # Run React loop with context as separate input field
        trajectory = self._run_react_loop(
            trajectory,
            user_query,
            context_string,
            max_iterations
        )
        
        # Add completed trajectory to history
        self.history.add_trajectory(trajectory)
        
        # Extract final answer with context for better synthesis
        final_answer = self.extract_agent(
            trajectory=trajectory,
            context=context_string,  # Pass context to Extract agent
            user_query=user_query
        )
        
        return {
            "trajectory": trajectory,
            "final_answer": final_answer,
            "conversation_stats": {
                "total_interactions": self.history.total_trajectories_processed,
                "active_trajectories": len(self.history.trajectories),
                "summarized_count": len(self.history.summaries)
            }
        }
    
    def _build_context_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build a context prompt from conversation history.
        
        This creates a concise summary of recent interactions that
        helps the agent maintain context across queries.
        
        Args:
            context: Conversation context dictionary
            
        Returns:
            Formatted context string
        """
        lines = []
        
        # Add summary context if available
        if context["summaries"]:
            latest_summary = context["summaries"][-1]
            lines.append(f"[Previous Context: {latest_summary.summary_text}]")
        
        # Add recent trajectory information
        recent_trajectories = context["trajectories"][-3:]  # Last 3 interactions
        if recent_trajectories:
            lines.append("\nRecent Interactions:")
            for i, traj in enumerate(recent_trajectories, 1):
                tools_used = set()
                for step in traj.steps:
                    if step.tool_invocation:
                        tools_used.add(step.tool_invocation.tool_name)
                
                lines.append(
                    f"{i}. Query: {traj.user_query[:50]}... "
                    f"(Used: {', '.join(tools_used) if tools_used else 'reasoning only'})"
                )
        
        return "\n".join(lines)
    
    def _run_react_loop(
        self,
        trajectory: Trajectory,
        user_query: str,
        context_string: str,
        max_iterations: int
    ) -> Trajectory:
        """
        Run React loop with conversation context as a separate input field.
        
        This follows DSPy's pattern of using context as an InputField,
        allowing the agent to explicitly reason about previous interactions.
        """
        # Main agent loop (simplified for demo)
        for iteration in range(max_iterations):
            # Call React agent with context as separate field
            trajectory = self.react_agent.forward(
                trajectory=trajectory,
                context=context_string,  # Passed as separate InputField
                user_query=user_query
            )
            
            # Get the last step to check if agent is done
            last_step = trajectory.steps[-1]
            
            # Check if agent has decided to finish
            if last_step.tool_invocation and last_step.tool_invocation.tool_name == "finish":
                break
            
            # Execute tool and add observation
            if last_step.tool_invocation:
                tool_name = last_step.tool_invocation.tool_name
                tool_args = last_step.tool_invocation.tool_args
                
                # Execute tool (simplified)
                if tool_name in self.tool_registry.get_all_tools():
                    tool = self.tool_registry.get_tool(tool_name)
                    result = tool.execute(**tool_args)
                    trajectory.add_observation(
                        tool_name=tool_name,
                        status=ToolStatus.SUCCESS,
                        result=result
                    )
        
        return trajectory

def run_react_loop(
    react_agent: ReactAgent,
    tool_registry: ToolRegistry,
    user_query: str,
    tool_set_name: str,
    max_iterations: int = 5,
    sliding_window_config: Optional[SlidingWindowConfig] = None
) -> Trajectory:
    """
    Run the React agent loop with sliding window management.
    
    Args:
        react_agent: The initialized ReactAgent instance
        tool_registry: The tool registry for executing tools
        user_query: The user's question or task
        tool_set_name: Name of the tool set being used
        max_iterations: Maximum number of iterations
        sliding_window_config: Optional sliding window configuration
        
    Returns:
        Complete Trajectory object with window management applied
    """
    # Initialize trajectory and sliding window
    trajectory = Trajectory(
        user_query=user_query,
        tool_set_name=tool_set_name,
        max_iterations=max_iterations
    )
    
    # Initialize sliding window manager if config provided
    sliding_window = SlidingWindowManager(sliding_window_config) if sliding_window_config else None
    
    logger.debug("Starting ReactAgent loop with sliding window")
    logger.debug(f"Query: {user_query}")
    
    # Main agent loop
    while trajectory.iteration_count < max_iterations:
        iteration_start = time.time()
        
        # Apply sliding window before each iteration (if configured)
        if sliding_window:
            trajectory = sliding_window.apply_window(trajectory)
            
            # Log window status
            metadata = sliding_window.get_metadata()
            if metadata.window_applied:
                logger.info(
                    f"[Sliding Window Applied: {metadata.steps_removed} steps removed, "
                    f"{len(metadata.observations_truncated)} observations truncated]"
                )
        
        logger.debug(f"Iteration {trajectory.iteration_count + 1}/{max_iterations}")
        
        # Get next action from agent (trajectory is updated in-place)
        trajectory = react_agent(
            trajectory=trajectory,
            user_query=user_query
        )
        
        # Get the last step that was just added
        last_step = trajectory.steps[-1]
        
        # Check if agent has decided to finish
        if last_step.is_finish:
            logger.debug("Agent selected 'finish' - task complete")
            trajectory.completed_at = datetime.now()
            break
        
        # Execute the tool from the last step
        tool_invocation = last_step.tool_invocation
        if not tool_invocation:
            logger.warning("No tool invocation in step")
            trajectory.completed_at = datetime.now()
            break
        
        tool_name = tool_invocation.tool_name
        tool_args = tool_invocation.tool_args
        
        logger.debug(f"Tool selected: {tool_name}")
        logger.debug(f"Tool args: {tool_args}")
        
        # Execute tool and add observation
        if tool_name in tool_registry.get_all_tools():
            try:
                tool = tool_registry.get_tool(tool_name)
                logger.debug(f"Executing tool: {tool_name}")
                result = tool.execute(**tool_args)
                logger.debug(f"Tool result: {result}")
                
                execution_time = (time.time() - iteration_start) * 1000
                trajectory.add_observation(
                    tool_name=tool_name,
                    status=ToolStatus.SUCCESS,
                    result=result,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                trajectory.add_observation(
                    tool_name=tool_name,
                    status=ToolStatus.ERROR,
                    error=str(e),
                    execution_time_ms=(time.time() - iteration_start) * 1000
                )
        else:
            logger.error(f"Tool not found: {tool_name}")
            trajectory.add_observation(
                tool_name=tool_name,
                status=ToolStatus.ERROR,
                error=f"Tool '{tool_name}' not found in registry",
                execution_time_ms=0
            )
    
    # Log final window statistics if sliding window was used
    if sliding_window:
        metadata = sliding_window.get_metadata()
        if metadata.window_applied:
            logger.info(
                f"[Final Window Stats: Original {metadata.original_step_count} steps, "
                f"Final {len(trajectory.steps)} steps, "
                f"Removed {metadata.steps_removed} steps, "
                f"Truncated {len(metadata.observations_truncated)} observations]"
            )
    
    return trajectory
```

### 4. Configuration Examples

Here are example configurations for different use cases:

```python
# File: agentic_loop/history_configs.py

from shared.conversation_history import ConversationHistoryConfig
from shared.sliding_window import SlidingWindowConfig

# Configuration presets for different conversation scenarios

# For interactive demos - configured as requested by engineer
DEMO_HISTORY_CONFIG = ConversationHistoryConfig(
    max_trajectories=10,  # Keep last 10 interactions (engineer confirmed)
    summarize_removed=True,  # Use Extract agent for intelligent summaries
    preserve_first_trajectories=1,  # Keep initial context
    preserve_last_trajectories=7,  # Keep recent context
    step_window_config=SlidingWindowConfig(
    max_steps=10,
    truncate_observations=True,
    observation_max_chars=300,
    preserve_first_steps=1,
    preserve_last_steps=7
)

# For complex conversations - extensive history
EXTENDED_HISTORY_CONFIG = ConversationHistoryConfig(
    max_trajectories=20,  # Keep more interactions
    summarize_removed=True,
    preserve_first_trajectories=2,
    preserve_last_trajectories=15,
    step_window_config=SlidingWindowConfig(
    max_steps=15,
    truncate_observations=True,
    observation_max_chars=500,
    preserve_first_steps=2,
    preserve_last_steps=10
)

# For debugging - maximum retention
DEBUG_HISTORY_CONFIG = ConversationHistoryConfig(
    max_trajectories=50,  # Keep many interactions
    summarize_removed=False,  # Don't summarize, keep everything
    preserve_first_trajectories=5,
    preserve_last_trajectories=45,
    step_window_config=SlidingWindowConfig(
    max_steps=50,
    truncate_observations=True,
    observation_max_chars=1000,
    preserve_first_steps=5,
    preserve_last_steps=40
)

# Minimal for token optimization
MINIMAL_HISTORY_CONFIG = ConversationHistoryConfig(
    max_trajectories=3,  # Very limited history
    summarize_removed=True,
    preserve_first_trajectories=0,
    preserve_last_trajectories=3,
    step_window_config=SlidingWindowConfig(
    max_steps=3,
    truncate_observations=True,
    observation_max_chars=100,
    preserve_first_steps=0,
    preserve_last_steps=3
)

# Balanced configuration for production
PRODUCTION_HISTORY_CONFIG = ConversationHistoryConfig(
    max_trajectories=10,  # Reasonable history depth
    summarize_removed=True,
    preserve_first_trajectories=1,
    preserve_last_trajectories=7,
    step_window_config=SlidingWindowConfig(
    max_steps=10,
    truncate_observations=True,
    observation_max_chars=300,
    preserve_first_steps=1,
    preserve_last_steps=7
)
```

### 5. Demo Script

Here's a comprehensive demo showing the conversation history in action:

```python
# File: demo_conversation_history.py

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agentic_loop.core_loop import run_agent_loop
from agentic_loop.window_configs import DEMO_CONFIG, REASONING_CONFIG, MINIMAL_CONFIG
from shared.sliding_window import SlidingWindowManager
from shared import setup_llm, ConsoleFormatter
from shared.tool_utils.agriculture_tool_set import AgricultureToolSet
from shared.tool_utils.registry import ToolRegistry

def demo_conversation_history():
    """
    Demonstrate conversation history management across multiple interactions.
    
    This demo shows how the system:
    1. Maintains context across queries
    2. Manages memory through sliding windows
    3. Creates summaries of old interactions
    4. Provides full conversation awareness to the agent
    """
    
    # Setup
    console = ConsoleFormatter()
    logger = logging.getLogger(__name__)
    
    # Configure LLM
    setup_llm()
    
    # Create tool registry
    tool_set = AgricultureToolSet()
    registry = ToolRegistry()
    registry.register_tool_set(tool_set)
    
    # Custom conversation-oriented questions (as requested by engineer)
    questions = [
        "What's the current weather in Iowa?",
        "How does that compare to Nebraska?",  # References previous query
        "What's the 7-day forecast for both locations?",  # Builds on context
        "Based on our discussion, which location is better for planting corn?",  # Synthesizes
        "What about wheat instead?",  # Changes topic but maintains context
        "Can you summarize all the weather data we've discussed?",  # Tests memory
        "What were the key differences between Iowa and Nebraska?",  # Tests recall
        "Should I plant this week or wait?",  # Requires context understanding
        "What other factors should I consider?",  # Open-ended with context
        "Compare today's weather with the forecast"  # Complex comparison
    ]
    
    logger.info(console.section_header("🗂️ Conversation History Demo"))
    logger.info(f"Configuration: DEMO_HISTORY_CONFIG")
    logger.info(f"  - Max Trajectories: 10")  # As confirmed by engineer
    logger.info(f"  - Summary Method: Extract Agent (intelligent summaries)")
    logger.info(f"  - Context Passing: Signature Input Fields")
    logger.info("")
    
    # Create conversation agent with history
    conversation_agent = ConversationAgent(
        tool_registry=registry,
        history_config=DEMO_HISTORY_CONFIG
    )
    
    # Process each question in sequence
    for i, question in enumerate(questions, 1):
        logger.info(console.section_header(f"📝 Query {i}/{len(questions)}", char='-', width=60))
        logger.info(f"User: {question}")
        logger.info("")
        
        # Process query with conversation context
        result = conversation_agent.process_query(
            user_query=question,
            tool_set_name=AgricultureToolSet.NAME,
            max_iterations=5
        )
    
        # Show response
        logger.info(f"Agent: {result['final_answer'][:200]}..." if len(result['final_answer']) > 200 else f"Agent: {result['final_answer']}")
        logger.info("")
        
        # Show conversation statistics
        stats = result['conversation_stats']
        logger.info(f"📊 Stats: Total={stats['total_interactions']}, Active={stats['active_trajectories']}, Summarized={stats['summarized_count']}")
        logger.info("")
    
    # Show final conversation history
    logger.info(console.section_header("📚 Final Conversation History", char='=', width=80))
    logger.info(conversation_agent.history.get_full_history_text())
    
    # Demonstrate memory management
    logger.info(console.section_header("💾 Memory Management Demo", char='=', width=80))
    
    # Add more queries to trigger trajectory removal
    overflow_queries = [
        f"Question {i}: What's the weather like?" 
        for i in range(7, 15)  # Add 8 more queries
    ]
    
    for question in overflow_queries:
        result = conversation_agent.process_query(
            user_query=question,
            tool_set_name=AgricultureToolSet.NAME,
            max_iterations=3
        )
    
    logger.info("After adding more queries:")
    logger.info(conversation_agent.history.get_full_history_text())
    
    # Show how summaries preserve removed content
    if conversation_agent.history.summaries:
        logger.info(console.section_header("📋 Summaries of Removed Trajectories", char='-', width=60))
        for i, summary in enumerate(conversation_agent.history.summaries, 1):
            logger.info(f"\nSummary {i}:")
            logger.info(f"  {summary.summary_text}")
            logger.info(f"  Tools: {', '.join(summary.tools_used)}")
            logger.info(f"  Created: {summary.created_at.strftime('%H:%M:%S')}")

def compare_history_configurations():
    """Compare different conversation history configurations."""
    console = ConsoleFormatter()
    logger = logging.getLogger(__name__)
    
    configs = {
        "MINIMAL": MINIMAL_HISTORY_CONFIG,
        "DEMO": DEMO_HISTORY_CONFIG,
        "EXTENDED": EXTENDED_HISTORY_CONFIG,
        "PRODUCTION": PRODUCTION_HISTORY_CONFIG
    }
    
    logger.info(console.section_header("⚙️ History Configuration Comparison"))
    logger.info("")
    
    for name, config in configs.items():
        logger.info(f"{name} Configuration:")
        logger.info(f"  Trajectory Management:")
        logger.info(f"    - Max Trajectories: {config.max_trajectories}")
        logger.info(f"    - Preserve First: {config.preserve_first_trajectories}")
        logger.info(f"    - Preserve Last: {config.preserve_last_trajectories}")
        logger.info(f"    - Summarize Removed: {config.summarize_removed}")
        
        if config.step_window_config:
            logger.info(f"  Step Management:")
            logger.info(f"    - Max Steps: {config.step_window_config.max_steps}")
            logger.info(f"    - Truncate Observations: {config.step_window_config.truncate_observations}")
            logger.info(f"    - Max Observation Chars: {config.step_window_config.observation_max_chars}")
        logger.info("")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Conversation History Demo")
    parser.add_argument(
        "--compare", 
        action="store_true",
        help="Compare different window configurations"
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_history_configurations()
    else:
        demo_conversation_history()
```

## Key Design Decisions

### 1. Two-Level Management Architecture

**Level 1 - Trajectory Management (New)**:
- Manages complete user interactions as atomic units
- Each trajectory represents one complete React-Extract cycle
- Preserves conversation continuity across interactions
- Creates summaries of removed trajectories for long-term context

**Level 2 - Step Management (Existing)**:
- Manages individual steps within each trajectory
- Preserves React pattern coherence (thought → action → observation)
- Truncates large observations to save tokens
- Maintains type safety with Pydantic models

### 2. Conversation Context Preservation

**What We Preserve**:
- Complete trajectories (not partial steps)
- Tool usage patterns across interactions
- User query progression and topic evolution
- Summary of removed content for long-term awareness

**How We Preserve It**:
- First N trajectories for establishing context
- Last M trajectories for recent context
- Summaries of removed middle trajectories
- Metadata about total interactions

### 3. Memory Management Strategy

**Trajectory Level**:
- Keep first trajectory (establishes context)
- Keep recent trajectories (maintains continuity)
- Summarize and remove middle trajectories
- Track total interactions processed

**Step Level** (within each trajectory):
- Preserve first steps (initial reasoning)
- Preserve last steps (recent actions)
- Truncate large observations
- Maintain complete thought-action-observation triplets

### 4. Type-Safe Implementation

**Pydantic Models Throughout**:
- `ConversationHistory`: Top-level manager
- `ConversationSummary`: Summaries of removed trajectories
- `ConversationHistoryConfig`: Validated configuration
- `Trajectory` and `TrajectoryStep`: Immutable data structures

**Benefits**:
- Compile-time type checking
- Runtime validation
- Clear data contracts
- Self-documenting code

### 5. DSPy-Aligned Architecture

**Design Principles**:
- Purely synchronous (no async complexity)
- Type-safe with Pydantic models
- Compatible with DSPy's Chain-of-Thought
- Maintains external control over execution

**Integration Points**:
- Works with existing React/Extract agents
- Preserves manual iteration control
- Supports DSPy debugging (DSPY_DEBUG)
- Compatible with all tool sets

## Advantages of This Approach

### Compared to Simple Message Lists

1. **Structured History**: Complete trajectories instead of flat messages
2. **Semantic Boundaries**: Natural conversation units preserved
3. **Tool Awareness**: Tracks tool usage patterns across interactions
4. **Context Preservation**: Summaries maintain long-term awareness

### Compared to AWS Strands Approach

1. **Simpler Implementation**: No async complexity or message interleaving
2. **Type Safety**: Pydantic models throughout vs dictionaries
3. **DSPy Native**: Built for DSPy patterns, not adapted from Bedrock
4. **Trajectory-Centric**: Preserves complete interactions vs individual messages

### For Production Use

1. **Token Optimization**: Multi-level management reduces costs
2. **Scalability**: Handles long conversations gracefully
3. **Debuggability**: Clear history and summaries for troubleshooting
4. **Flexibility**: Configurable for different use cases

## Testing Strategy

### Conversation History Tests

```python
# File: tests/test_conversation_history.py

import pytest
from shared.conversation_history import (
    ConversationHistory, 
    ConversationHistoryConfig,
    ConversationSummary
)
from shared.trajectory_models import Trajectory

def test_conversation_history_basic():
    """Test basic conversation history operations."""
    config = ConversationHistoryConfig(
        max_trajectories=3,
        summarize_removed=True
    )
    history = ConversationHistory(config)
    
    # Add trajectories
    for i in range(5):
        trajectory = Trajectory(
            user_query=f"Query {i}",
            tool_set_name="test_tools"
        )
        history.add_trajectory(trajectory)
    
    # Should only keep 3 trajectories
    assert len(history.trajectories) == 3
    
    # Should have created summaries
    assert len(history.summaries) > 0
    
    # Should track total processed
    assert history.total_trajectories_processed == 5

def test_preservation_strategy():
    """Test that first and last trajectories are preserved correctly."""
    config = ConversationHistoryConfig(
        max_trajectories=5,
        preserve_first_trajectories=1,
        preserve_last_trajectories=3,
        summarize_removed=True
    )
    history = ConversationHistory(config)
    
    # Add 10 trajectories
    trajectories = []
    for i in range(10):
        t = Trajectory(user_query=f"Query {i}", tool_set_name="test")
        trajectories.append(t)
        history.add_trajectory(t)
    
    # Should preserve first 1 and last 3
    assert len(history.trajectories) == 4
    assert history.trajectories[0].user_query == "Query 0"  # First preserved
    assert history.trajectories[-1].user_query == "Query 9"  # Last preserved
    assert history.trajectories[-2].user_query == "Query 8"
    assert history.trajectories[-3].user_query == "Query 7"

def test_context_generation():
    """Test context generation for agent."""
    history = ConversationHistory()
    
    # Add some trajectories
    for i in range(3):
        t = Trajectory(user_query=f"Query {i}", tool_set_name="test")
        history.add_trajectory(t)
    
    # Get context
    context = history.get_context_for_agent()
    
    assert "trajectories" in context
    assert "trajectory_count" in context
    assert "total_processed" in context
    assert context["trajectory_count"] == 3
    assert context["total_processed"] == 3

def test_summary_creation():
    """Test that summaries are created correctly."""
    config = ConversationHistoryConfig(
        max_trajectories=2,
        summarize_removed=True
    )
    history = ConversationHistory(config)
    
    # Add trajectories with tool usage
    for i in range(5):
        t = Trajectory(user_query=f"Query {i}", tool_set_name="test")
        # Add a step with tool usage
        t.add_step(
            thought=f"Thinking {i}",
            tool_name=f"tool_{i % 3}",  # Rotate through 3 tools
            tool_args={}
        )
        history.add_trajectory(t)
    
    # Should have summaries
    assert len(history.summaries) > 0
    
    # Check summary content
    summary = history.summaries[0]
    assert isinstance(summary, ConversationSummary)
    assert summary.trajectory_count > 0
    assert len(summary.tools_used) > 0
    assert summary.summary_text != ""

def test_clear_history():
    """Test clearing conversation history."""
    history = ConversationHistory()
    
    # Add trajectories
    for i in range(5):
        t = Trajectory(user_query=f"Query {i}", tool_set_name="test")
        history.add_trajectory(t)
    
    # Clear keeping last 2
    history.clear_history(keep_last=2)
    
    assert len(history.trajectories) == 2
    assert len(history.summaries) == 0
    assert history.trajectories[0].user_query == "Query 3"
    assert history.trajectories[1].user_query == "Query 4"
```

### Sliding Window Tests (Existing)

```python
# File: tests/test_sliding_window.py

import pytest
from shared.sliding_window import SlidingWindowManager, SlidingWindowConfig, WindowMetadata
from shared.trajectory_models import (
    Trajectory, TrajectoryStep, ThoughtStep, 
    ToolInvocation, ToolObservation, ToolStatus
)

def create_test_trajectory(num_steps: int) -> Trajectory:
    """Helper to create a test trajectory with N steps."""
    trajectory = Trajectory(
        user_query="Test query",
        tool_set_name="test_tools",
        max_iterations=10
    )
    
    for i in range(1, num_steps + 1):
        # Add step with thought and tool invocation
        step = trajectory.add_step(
            thought=f"Thinking about step {i}",
            tool_name=f"tool_{i}",
            tool_args={"param": f"value_{i}"}
        )
        
        # Add observation
        trajectory.add_observation(
            tool_name=f"tool_{i}",
            status=ToolStatus.SUCCESS,
            result=f"Result from tool {i}" * 10,  # Make it sizeable
            execution_time_ms=100.0
        )
    
    return trajectory

def test_window_preserves_complete_steps():
    """Ensure complete TrajectoryStep objects are preserved."""
    config = SlidingWindowConfig(
        max_steps=3,
        preserve_first_steps=1,
        preserve_last_steps=2
    )
    manager = SlidingWindowManager(config)
    
    # Create trajectory with 5 steps
    trajectory = create_test_trajectory(5)
    
    # Apply window
    windowed = manager.apply_window(trajectory)
    
    # Should have 3 steps total
    assert len(windowed.steps) == 3
    
    # Check metadata
    metadata = manager.get_metadata()
    assert metadata.window_applied
    assert metadata.steps_removed == 2
    assert metadata.original_step_count == 5
    
    # Verify step continuity (renumbered)
    assert windowed.steps[0].iteration == 1
    assert windowed.steps[1].iteration == 2
    assert windowed.steps[2].iteration == 3
    
    # Verify preservation strategy (first 1, last 2)
    assert "step 1" in windowed.steps[0].thought.content  # First preserved
    assert "step 4" in windowed.steps[1].thought.content or "step 5" in windowed.steps[1].thought.content

def test_observation_truncation():
    """Test that large observations are truncated before removing steps."""
    config = SlidingWindowConfig(
        max_steps=5,
        truncate_observations=True,
        observation_max_chars=50
    )
    manager = SlidingWindowManager(config)
    
    # Create trajectory with large observations
    trajectory = Trajectory(
        user_query="Test query",
        tool_set_name="test_tools"
    )
    
    # Add step with large observation
    trajectory.add_step(
        thought="Testing truncation",
        tool_name="test_tool",
        tool_args={}
    )
    
    large_result = "x" * 200  # Much larger than limit
    trajectory.add_observation(
        tool_name="test_tool",
        status=ToolStatus.SUCCESS,
        result=large_result,
        execution_time_ms=100
    )
    
    # Apply window
    windowed = manager.apply_window(trajectory)
    
    # Check observation was truncated
    observation = windowed.steps[0].observation
    assert observation is not None
    assert "[TRUNCATED" in str(observation.result)
    assert len(str(observation.result)) < len(large_result)
    
    # Check metadata
    metadata = manager.get_metadata()
    assert 1 in metadata.observations_truncated

def test_immutable_models_handled_correctly():
    """Test that frozen Pydantic models are properly recreated."""
    config = SlidingWindowConfig(
        max_steps=2,
        truncate_observations=True,
        observation_max_chars=20
    )
    manager = SlidingWindowManager(config)
    
    trajectory = create_test_trajectory(3)
    
    # Original steps should be frozen (immutable)
    with pytest.raises(Exception):  # Pydantic will raise an error
        trajectory.steps[0].thought = ThoughtStep(content="Modified")
    
    # Apply window
    windowed = manager.apply_window(trajectory)
    
    # New trajectory should have new step instances
    assert windowed is not trajectory
    assert windowed.steps[0] is not trajectory.steps[0]
    
    # But content should be preserved (except for removed steps)
    assert len(windowed.steps) == 2

def test_no_window_when_under_limit():
    """Test that window is not applied when trajectory is under limit."""
    config = SlidingWindowConfig(max_steps=10)
    manager = SlidingWindowManager(config)
    
    trajectory = create_test_trajectory(5)
    
    # Apply window
    windowed = manager.apply_window(trajectory)
    
    # Should be the same trajectory
    assert windowed is trajectory
    assert len(windowed.steps) == 5
    
    # Check metadata
    metadata = manager.get_metadata()
    assert not metadata.window_applied
    assert metadata.steps_removed == 0

def test_context_note_injection():
    """Test that context notes are injected when steps are removed."""
    config = SlidingWindowConfig(
        max_steps=2,
        preserve_first_steps=1,
        preserve_last_steps=1
    )
    manager = SlidingWindowManager(config)
    
    trajectory = create_test_trajectory(5)
    
    # Apply window
    windowed = manager.apply_window(trajectory)
    
    # First step should have context note
    first_thought = windowed.steps[0].thought.content
    assert "[Context:" in first_thought
    assert "3 earlier steps removed" in first_thought
    
    # Original thought content should still be present
    assert "step" in first_thought.lower()
```

## Integration with DSPy Patterns

### React Agent Integration

The conversation history provides context to the React agent through:

1. **Augmented Queries**: Previous context prepended to user queries
2. **Trajectory Metadata**: Conversation stats in trajectory metadata
3. **Tool Usage Patterns**: Historical tool usage informs selection
4. **Topic Continuity**: Maintains context across related queries

### Extract Agent Integration

The Extract agent benefits from:

1. **Complete Trajectories**: Full interaction history for synthesis
2. **Summary Context**: Awareness of removed interactions
3. **Pattern Recognition**: Can identify recurring themes
4. **Comprehensive Answers**: Draws on full conversation context

### DSPy Best Practices

1. **Synchronous Only**: No async complexity
2. **Type Safety**: Pydantic models throughout
3. **External Control**: Maintains manual iteration control
4. **Observability**: Full visibility into history management
5. **Testability**: Clear interfaces and predictable behavior

## Implementation Roadmap

### Phase 1: Core Implementation ✓
- [x] ConversationHistory class with trajectory management
- [x] Two-level sliding window (trajectories and steps)
- [x] Summary generation for removed trajectories
- [x] Configuration system with presets

### Phase 2: Integration
- [ ] Integrate with existing React/Extract agents
- [ ] Add context augmentation to React agent
- [ ] Update Extract agent to use full history
- [ ] Create ConversationAgent wrapper class

### Phase 3: Enhancements
- [ ] LLM-based summarization for removed trajectories
- [ ] Semantic boundary detection
- [ ] Tool usage pattern learning
- [ ] Conversation topic tracking

### Phase 4: Production Features
- [ ] Persistence (save/load conversation state)
- [ ] Conversation branching (multiple threads)
- [ ] User-specific history management
- [ ] Analytics and metrics

## Conclusion

This conversation history management system provides a comprehensive solution for maintaining context across multiple agent interactions in DSPy. By managing both complete trajectories and individual steps, it achieves:

### Technical Excellence
1. **Type Safety**: Full Pydantic validation at every level
2. **Memory Efficiency**: Multi-level sliding windows optimize token usage
3. **Context Preservation**: Summaries maintain long-term awareness
4. **Clean Architecture**: Clear separation between trajectory and step management

### Practical Benefits
1. **Conversation Continuity**: Agents maintain context across interactions
2. **Scalability**: Handles long conversations gracefully
3. **Flexibility**: Configurable for different use cases
4. **Observability**: Clear visibility into history management

### DSPy Alignment
1. **Synchronous Design**: No async complexity
2. **External Control**: Preserves manual iteration control
3. **Tool Integration**: Works with existing tool system
4. **Pattern Compatibility**: Integrates with React/Extract patterns

The system demonstrates that sophisticated conversation management can be achieved while maintaining the simplicity and clarity that makes DSPy powerful. It provides a foundation for building conversational AI systems that can maintain context, learn from interactions, and provide increasingly helpful responses over time.