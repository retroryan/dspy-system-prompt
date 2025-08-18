"""
Message-based models for simplified conversation history.

This module implements a flat message list structure inspired by AWS Strands SDK,
replacing the nested trajectory-based system with a simpler, more maintainable approach.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class ToolStatus(str, Enum):
    """Status of a tool execution."""
    SUCCESS = "success"
    ERROR = "error"


class ToolUse(BaseModel):
    """Tool invocation request."""
    model_config = ConfigDict(frozen=True)
    
    tool_use_id: str = Field(..., description="Unique identifier for this tool use")
    tool_name: str = Field(..., description="Name of the tool to invoke")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class ToolResult(BaseModel):
    """Result from tool execution."""
    model_config = ConfigDict(frozen=True)
    
    tool_use_id: str = Field(..., description="ID linking to the tool use request")
    status: ToolStatus = Field(..., description="Status of the tool execution")
    result: Optional[Any] = Field(None, description="The result if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: float = Field(0.0, description="Execution time in milliseconds")


class Trajectory(BaseModel):
    """A single trajectory within a message (content block)."""
    model_config = ConfigDict(frozen=True)
    
    text: Optional[str] = Field(None, description="Text content")
    thought: Optional[str] = Field(None, description="Agent's reasoning")
    tool_use: Optional[ToolUse] = Field(None, description="Tool invocation")
    tool_result: Optional[ToolResult] = Field(None, description="Tool execution result")


class Message(BaseModel):
    """A single message in the conversation."""
    
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    trajectories: List[Trajectory] = Field(default_factory=list, description="Content blocks")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class MessageList(BaseModel):
    """
    Container for messages in the current interaction.
    Replaces the old Trajectory class with a flat message structure.
    """
    
    messages: List[Message] = Field(default_factory=list, description="List of messages")
    user_query: str = Field(..., description="The original user query")
    tool_set_name: str = Field(..., description="Name of the tool set being used")
    max_iterations: int = Field(default=5, description="Maximum iterations allowed")
    started_at: datetime = Field(default_factory=datetime.now, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    
    # Private counter for tool use IDs
    _tool_use_counter: int = 0
    
    def _generate_tool_use_id(self) -> str:
        """Generate a unique tool use ID."""
        self._tool_use_counter += 1
        return f"tool_{self._tool_use_counter}_{datetime.now().timestamp()}"
    
    @property
    def iteration_count(self) -> int:
        """Count iterations based on assistant messages with tool calls."""
        count = 0
        for message in self.messages:
            if message.role == "assistant":
                for trajectory in message.trajectories:
                    if trajectory.tool_use and trajectory.tool_use.tool_name != "finish":
                        count += 1
                    elif trajectory.tool_use and trajectory.tool_use.tool_name == "finish":
                        count += 1  # Count finish as an iteration
                        break
        return count
    
    @property
    def is_complete(self) -> bool:
        """
        Check if the interaction is complete.
        Complete when agent selects 'finish' tool or max iterations reached.
        """
        if not self.messages:
            return False
            
        # Check for finish tool in last assistant message
        for message in reversed(self.messages):
            if message.role == "assistant":
                for trajectory in message.trajectories:
                    if trajectory.tool_use and trajectory.tool_use.tool_name == "finish":
                        return True
                break
        
        # Check if max iterations reached
        return self.iteration_count >= self.max_iterations
    
    @property
    def tools_used(self) -> List[str]:
        """Get list of unique tools used (excluding 'finish')."""
        tools = []
        for message in self.messages:
            if message.role == "assistant":
                for trajectory in message.trajectories:
                    if trajectory.tool_use:
                        tool_name = trajectory.tool_use.tool_name
                        if tool_name != "finish" and tool_name not in tools:
                            tools.append(tool_name)
        return tools
    
    @property
    def last_observation(self) -> Optional[ToolResult]:
        """Get the most recent tool result."""
        for message in reversed(self.messages):
            for trajectory in reversed(message.trajectories):
                if trajectory.tool_result:
                    return trajectory.tool_result
        return None
    
    @property
    def total_execution_time_ms(self) -> float:
        """Calculate total execution time across all tools."""
        total = 0.0
        for message in self.messages:
            for trajectory in message.trajectories:
                if trajectory.tool_result:
                    total += trajectory.tool_result.execution_time_ms
        return total
    
    def add_assistant_message(
        self,
        thought: str,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an assistant message with thought and optional tool use.
        Returns the tool_use_id if a tool was invoked.
        """
        trajectories = []
        tool_use_id = None
        
        # Add thought trajectory
        if thought:
            trajectories.append(Trajectory(thought=thought))
        
        # Add tool use trajectory if provided
        if tool_name:
            tool_use_id = self._generate_tool_use_id()
            trajectories.append(Trajectory(
                tool_use=ToolUse(
                    tool_use_id=tool_use_id,
                    tool_name=tool_name,
                    tool_args=tool_args or {}
                )
            ))
        
        # Create and add the message
        message = Message(
            role="assistant",
            trajectories=trajectories
        )
        self.messages.append(message)
        
        return tool_use_id
    
    def add_tool_result(
        self,
        tool_use_id: str,
        tool_name: str,
        status: ToolStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        execution_time_ms: float = 0
    ) -> None:
        """Add a tool result to the message list."""
        # Add as a new trajectory in the last assistant message
        # or create a new assistant message if needed
        if self.messages and self.messages[-1].role == "assistant":
            # Add to existing assistant message
            self.messages[-1].trajectories.append(Trajectory(
                tool_result=ToolResult(
                    tool_use_id=tool_use_id,
                    status=status,
                    result=result,
                    error=error,
                    execution_time_ms=execution_time_ms
                )
            ))
        else:
            # Create new assistant message with tool result
            message = Message(
                role="assistant",
                trajectories=[Trajectory(
                    tool_result=ToolResult(
                        tool_use_id=tool_use_id,
                        status=status,
                        result=result,
                        error=error,
                        execution_time_ms=execution_time_ms
                    )
                )]
            )
            self.messages.append(message)
    
    def add_user_message(self, text: str) -> None:
        """Add a user message."""
        message = Message(
            role="user",
            trajectories=[Trajectory(text=text)]
        )
        self.messages.append(message)
    
    def to_llm_format(self) -> str:
        """Format messages for LLM consumption."""
        lines = [f"User Query: {self.user_query}\n"]
        
        iteration = 0
        for message in self.messages:
            if message.role == "user":
                # User messages
                for trajectory in message.trajectories:
                    if trajectory.text:
                        lines.append(f"User: {trajectory.text}")
            
            elif message.role == "assistant":
                # Assistant messages with iterations
                for trajectory in message.trajectories:
                    if trajectory.thought:
                        iteration += 1
                        lines.append(f"Iteration {iteration}:")
                        lines.append(f"  Thought: {trajectory.thought}")
                    
                    if trajectory.tool_use:
                        lines.append(f"  Tool: {trajectory.tool_use.tool_name}")
                        if trajectory.tool_use.tool_args:
                            lines.append(f"  Args: {trajectory.tool_use.tool_args}")
                        
                        # Special handling for finish tool
                        if trajectory.tool_use.tool_name == "finish":
                            lines.append("  Status: Task complete, ready for answer extraction")
                    
                    if trajectory.tool_result:
                        if trajectory.tool_result.status == ToolStatus.SUCCESS:
                            lines.append(f"  Result: {trajectory.tool_result.result}")
                        else:
                            lines.append(f"  Error: {trajectory.tool_result.error}")
        
        return "\n".join(lines)


class ExtractResult(BaseModel):
    """Result from the Extract agent."""
    model_config = ConfigDict(frozen=True)
    
    answer: str = Field(..., description="The final answer extracted")
    reasoning: str = Field(default="", description="The reasoning process used")


class ConversationHistory:
    """
    Conversation history manager using flat message list.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration."""
        self.messages: List[Message] = []
        self.summaries: List[str] = []
        self.config = config or {}
        self.max_messages = self.config.get('max_messages', 100)
        self.summarize_removed = self.config.get('summarize_removed', True)
    
    def add_messages(self, message_list: MessageList) -> None:
        """Add messages from a MessageList to history."""
        self.messages.extend(message_list.messages)
        self._apply_sliding_window()
    
    def clear_history(self) -> None:
        """Clear all conversation history."""
        self.messages = []
        self.summaries = []
    
    def get_context_for_agent(self) -> Dict[str, Any]:
        """Get context for the agent from message history."""
        return {
            "message_count": len(self.messages),
            "messages": self.messages,
            "summaries": self.summaries
        }
    
    def build_context_prompt(self, context: Dict[str, Any]) -> str:
        """Build context prompt from message history."""
        if not context["messages"] and not context["summaries"]:
            return ""
        
        lines = ["Previous conversation context:"]
        
        # Add summaries if any
        for summary in context.get("summaries", []):
            lines.append(f"[Summary]: {summary}")
        
        # Add recent messages
        for message in context.get("messages", []):
            if message.role == "user":
                for traj in message.trajectories:
                    if traj.text:
                        lines.append(f"User: {traj.text}")
            elif message.role == "assistant":
                for traj in message.trajectories:
                    if traj.text:
                        lines.append(f"Assistant: {traj.text}")
                    elif traj.thought:
                        lines.append(f"Assistant thought: {traj.thought}")
        
        return "\n".join(lines)
    
    def _apply_sliding_window(self) -> None:
        """Apply sliding window to message list."""
        if len(self.messages) <= self.max_messages:
            return
        
        # Find safe trim point (not breaking tool pairs)
        trim_index = len(self.messages) - self.max_messages
        trim_index = self._find_safe_trim_point(trim_index)
        
        # Optionally summarize removed messages
        if self.summarize_removed and trim_index > 0:
            removed = self.messages[:trim_index]
            summary = self._create_summary(removed)
            if summary:
                self.summaries.append(summary)
        
        # Trim messages
        self.messages = self.messages[trim_index:]
    
    def _find_safe_trim_point(self, target_index: int) -> int:
        """Find a safe point to trim without breaking tool pairs."""
        pending_tools = set()
        
        # Scan forward to find complete tool pairs
        for i in range(target_index, len(self.messages)):
            message = self.messages[i]
            
            for trajectory in message.trajectories:
                if trajectory.tool_use:
                    pending_tools.add(trajectory.tool_use.tool_use_id)
                elif trajectory.tool_result:
                    pending_tools.discard(trajectory.tool_result.tool_use_id)
            
            # Safe to cut here if no pending tools
            if not pending_tools and i >= target_index:
                return i + 1
        
        return target_index  # Fallback
    
    def _create_summary(self, messages: List[Message]) -> str:
        """Create a simple text summary of removed messages."""
        # Simple implementation - can be enhanced with LLM summarization
        key_points = []
        for message in messages:
            if message.role == "user":
                for traj in message.trajectories:
                    if traj.text:
                        key_points.append(f"User asked: {traj.text[:50]}...")
            elif message.role == "assistant":
                for traj in message.trajectories:
                    if traj.text:
                        key_points.append(f"Assistant: {traj.text[:50]}...")
        
        if key_points:
            return "Earlier conversation: " + "; ".join(key_points[:3])
        return ""