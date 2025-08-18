"""
Session-based architecture for agent interactions.

This module provides the single, unified way to interact with agents.
Every interaction happens through an AgentSession, which maintains
conversation history and provides a clean, simple API.

Primary Goals:
1. Clean Implementation: No wrappers or backwards compatibility
2. Demo Simplicity: Simple, clear interface
3. Type Safety: Pydantic models throughout
4. DSPy Alignment: Synchronous, externally-controlled
"""

import os
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

import dspy

from shared.message_models import ConversationHistory, MessageList
from shared.tool_utils.registry import ToolRegistry
from agentic_loop.react_agent import ReactAgent
from agentic_loop.extract_agent import ReactExtract

logger = logging.getLogger(__name__)


class SessionResult(BaseModel):
    """
    Type-safe result from an agent query using MessageList.
    
    This is THE result type for all agent interactions.
    No dict returns, no ambiguity - just clean types.
    """
    model_config = ConfigDict(frozen=True)
    
    messages: MessageList = Field(
        ...,
        description="Complete message list of agent reasoning and tool execution"
    )
    answer: str = Field(
        ...,
        description="Final synthesized answer from the Extract agent"
    )
    execution_time: float = Field(
        ...,
        description="Total execution time in seconds"
    )
    conversation_turn: int = Field(
        ...,
        description="Which turn in the conversation this was"
    )
    had_context: bool = Field(
        ...,
        description="Whether previous context was available"
    )
    
    @property
    def tools_used(self) -> list[str]:
        """List of tools that were actually used."""
        return self.messages.tools_used
    
    @property
    def iterations(self) -> int:
        """Number of React iterations."""
        return self.messages.iteration_count


class AgentSession:
    """
    THE way to interact with agents using MessageList.
    All interactions go through a session.
    
    This class provides:
    - Always-on conversation history
    - Single, simple query() method
    - Automatic context management
    - Type-safe results
    
    Every interaction is part of a session. Even single queries are
    just sessions with one interaction.
    """
    
    def __init__(
        self,
        tool_set_name: str = "agriculture",
        user_id: str = "demo_user",
        config: Optional[Dict[str, Any]] = None,
        verbose: bool = False
    ):
        """
        Initialize an agent session for a specific user.
        
        Args:
            tool_set_name: Which tool set to use (agriculture, ecommerce, events)
            user_id: The user this session is for (defaults to demo_user for demos)
            config: Optional conversation history configuration dict with:
                    - max_messages: Maximum messages to keep in memory
                    - summarize_removed: Whether to summarize removed messages
                    If not provided, uses smart defaults based on environment.
            verbose: Whether to show detailed execution logs
        """
        self.tool_set_name = tool_set_name
        self.user_id = user_id
        self.session_id = str(uuid.uuid4())  # Unique session identifier
        self.verbose = verbose
        self.conversation_turn = 0
        
        # Session metadata (similar to strands' agent.state)
        self.session_metadata = {
            "user_id": user_id,
            "session_id": self.session_id,
            "created_at": datetime.now(),
            "tool_set": tool_set_name
        }
        
        # Always-on conversation history
        history_config = config if config else self._default_config()
        self.history = ConversationHistory(config=history_config)
        
        # Setup tools and agents
        self.tool_registry = self._setup_tools()
        self.react_agent = self._setup_react_agent()
        self.extract_agent = self._setup_extract_agent()
        
        logger.debug(f"Initialized AgentSession with {tool_set_name} tools for user {user_id}")
    
    def query(self, text: str, max_iterations: int = 5) -> SessionResult:
        """
        Process a query with automatic context management using MessageList.
        
        This is THE method for all agent interactions. Simple, clean, unified.
        
        Args:
            text: The user's query
            max_iterations: Maximum React loop iterations
            
        Returns:
            SessionResult with trajectory (MessageList), answer, and metadata
        """
        start_time = datetime.now()
        self.conversation_turn += 1
        
        # Get context from history
        context = self.history.get_context_for_agent()
        context_prompt = self.history.build_context_prompt(context)
        
        # Create message list
        messages = MessageList(
            user_query=text,
            tool_set_name=self.tool_set_name,
            max_iterations=max_iterations,
            metadata={
                "conversation_turn": self.conversation_turn,
                "has_context": len(context["messages"]) > 0,
                "context_size": len(context_prompt),
                "session_id": self.session_id
            }
        )
        
        # Add initial user message
        messages.add_user_message(text)
        
        # Run the React loop with context
        messages = self._run_react_loop(
            messages=messages,
            user_query=text,
            context_prompt=context_prompt,
            max_iterations=max_iterations
        )
        
        # Extract final answer with context
        answer = self._extract_answer(
            messages=messages,
            user_query=text,
            context_prompt=context_prompt
        )
        
        # Update conversation history
        messages.completed_at = datetime.now()
        self.history.add_messages(messages)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Return type-safe result
        return SessionResult(
            messages=messages,
            answer=answer,
            execution_time=execution_time,
            conversation_turn=self.conversation_turn,
            had_context=len(context["messages"]) > 0
        )
    
    def reset(self) -> None:
        """
        Reset the conversation, starting fresh.
        
        Useful for changing topics or starting a new conversation
        without creating a new session.
        """
        self.history.clear_history()
        self.conversation_turn = 0
        logger.info("Session reset - conversation history cleared")
    
    def _run_react_loop(
        self,
        messages: MessageList,
        user_query: str,
        context_prompt: str,
        max_iterations: int
    ) -> MessageList:
        """
        Run the React agent loop with context using MessageList.
        
        This calls the core React loop implementation with conversation context,
        passing the session object instead of just user_id.
        """
        from agentic_loop.core_loop import run_react_loop
        
        # Run the single, core React loop implementation
        # Pass self (the session) instead of user_id
        messages = run_react_loop(
            react_agent=self.react_agent,
            tool_registry=self.tool_registry,
            messages=messages,
            user_query=user_query,
            context_prompt=context_prompt,
            max_iterations=max_iterations,
            session=self,  # Pass the entire session object
            verbose=self.verbose
        )
        
        return messages
    
    def _extract_answer(
        self,
        messages: MessageList,
        user_query: str,
        context_prompt: str
    ) -> str:
        """
        Extract the final answer from the message list with context.
        """
        # Check if extract agent signature has conversation_context field
        if 'conversation_context' in self.extract_agent.signature.input_fields:
            # Context-aware extraction
            result = self.extract_agent(
                message_list=messages,
                user_query=user_query,
                conversation_context=context_prompt
            )
        else:
            # Standard extraction (fallback, shouldn't happen with our setup)
            result = self.extract_agent(
                message_list=messages,
                user_query=user_query
            )
        
        # Extract answer from result
        if hasattr(result, 'answer'):
            return result.answer
        else:
            return str(result)
    
    def _setup_tools(self) -> ToolRegistry:
        """Setup the tool registry with the specified tool set."""
        registry = ToolRegistry()
        
        # Import and register the appropriate tool set
        if self.tool_set_name == "agriculture":
            from tools.precision_agriculture.tool_set import AgricultureToolSet
            registry.register_tool_set(AgricultureToolSet())
        elif self.tool_set_name == "ecommerce":
            from tools.ecommerce.tool_set import EcommerceToolSet
            registry.register_tool_set(EcommerceToolSet())
        elif self.tool_set_name == "events":
            from tools.events.tool_set import EventsToolSet
            registry.register_tool_set(EventsToolSet())
        else:
            raise ValueError(f"Unknown tool set: {self.tool_set_name}")
        
        return registry
    
    def _setup_react_agent(self) -> ReactAgent:
        """Setup the React agent with context-aware signature."""
        # Define context-aware signature
        class ContextAwareReactSignature(dspy.Signature):
            """React agent signature with conversation context."""
            user_query = dspy.InputField(desc="The user's current question or task")
            conversation_context = dspy.InputField(
                desc="Context from previous interactions (may be empty for first query)"
            )
        
        return ReactAgent(
            signature=ContextAwareReactSignature,
            tool_registry=self.tool_registry
        )
    
    def _setup_extract_agent(self) -> ReactExtract:
        """Setup the Extract agent with context-aware signature."""
        # Define context-aware signature
        class ContextAwareExtractSignature(dspy.Signature):
            """Extract agent signature with conversation context."""
            user_query = dspy.InputField(desc="The user's current question or task")
            conversation_context = dspy.InputField(
                desc="Context from previous interactions (may be empty for first query)"
            )
            answer = dspy.OutputField(desc="Clear, direct answer to the user's question")
        
        return ReactExtract(signature=ContextAwareExtractSignature)
    
    def _default_config(self) -> Dict[str, Any]:
        """Get default configuration for ConversationHistory."""
        # Check environment for configuration hints
        provider = os.getenv("DSPY_PROVIDER", "ollama").lower()
        
        if provider in ["openai", "anthropic", "claude"]:
            # High-capacity providers
            return {
                'max_messages': 100,
                'summarize_removed': True
            }
        else:
            # Local/limited providers
            return {
                'max_messages': 30,
                'summarize_removed': True
            }