"""
Core Agentic Loop Implementation

This module contains the core functionality for running the React → Extract → Observe pattern.
It handles the iterative agent loop, tool execution, and final answer extraction.

The agent loop follows these steps:
1. **React Phase**: The agent reasons about the current state and selects the next action
2. **Tool Execution**: The selected tool is executed with the provided arguments
3. **Observation**: Tool results are added to the message list for the next iteration
4. **Iteration**: Steps 1-3 repeat until the agent decides to finish or max iterations
5. **Extract Phase**: A separate agent synthesizes all observations into a final answer
6. **Observe Phase**: The final answer is returned to the user

This separation of concerns allows for:
- Clear separation between reasoning (React) and synthesis (Extract)
- Full observability of the agent's decision-making process
- External control over tool execution and error handling
- Extensibility for different tool sets and use cases
"""

import logging
import time
import os
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

import dspy

from agentic_loop.react_agent import ReactAgent

# Avoid circular imports
if TYPE_CHECKING:
    from agentic_loop.session import AgentSession
from agentic_loop.extract_agent import ReactExtract
from shared.config import config
from shared.tool_utils.registry import ToolRegistry
from shared.message_models import (
    MessageList,
    ToolStatus,
    ExtractResult
)

# Initialize module-level logger
logger = logging.getLogger(__name__)


def run_react_loop(
    react_agent: ReactAgent,
    tool_registry: ToolRegistry,
    messages: MessageList,
    user_query: str,
    context_prompt: str,
    max_iterations: int = 5,
    session: Optional['AgentSession'] = None,
    verbose: bool = False
) -> MessageList:
    """
    Run the React agent loop with conversation context using MessageList.
    
    This is the React loop implementation. All agent interactions
    go through this function via AgentSession.
    
    The loop implements the React pattern:
    - Thought: Agent reasons about the current state and context
    - Action: Agent selects a tool and arguments
    - Observation: Tool is executed and result is observed
    
    Args:
        react_agent: The initialized ReactAgent instance
        tool_registry: The tool registry for executing tools
        messages: Pre-initialized MessageList with metadata
        user_query: The user's question or task
        context_prompt: Conversation context (may be empty for first query)
        max_iterations: Maximum number of iterations
        session: Optional AgentSession for stateful operations
        verbose: Whether to show detailed execution logs
        
    Returns:
        Complete MessageList with all messages and tool results
    """
    # Use messages directly
    message_list = messages
    
    # Clean demo logging
    if verbose:
        print(f"{'='*80}")
        print("Starting React loop")
        print(f"{'='*80}")
    
    logger.debug("Starting ReactAgent loop")
    logger.debug(f"Query: {user_query}")
    logger.debug(f"Context size: {len(context_prompt)} chars")
    
    # Main agent loop
    while message_list.iteration_count < max_iterations:
        iteration_start = time.time()
        iteration_num = message_list.iteration_count + 1
        
        # Get next action from agent with context
        # Always pass context - agents created via AgentSession always support it
        message_list = react_agent(
            message_list=message_list,
            user_query=user_query,
            conversation_context=context_prompt
        )
        
        # Get the last message's last trajectory for tool info
        last_message = message_list.messages[-1]
        last_trajectory = None
        tool_use = None
        
        for traj in last_message.trajectories:
            if traj.thought:
                last_trajectory = traj
            if traj.tool_use:
                tool_use = traj.tool_use
        
        # Demo logging for React iteration
        if verbose:
            print(f"react loop call {iteration_num} - log of results:")
            if last_trajectory and last_trajectory.thought:
                print(f"  Thought: {last_trajectory.thought}")
            if tool_use:
                print(f"  Tool: {tool_use.tool_name}")
                print(f"  Args: {tool_use.tool_args}")
                if tool_use.tool_name == "finish":
                    print(f"  Action: Final Answer")
            print()
        
        # Check if agent has decided to finish
        if tool_use and tool_use.tool_name == "finish":
            message_list.completed_at = datetime.now()
            break
        
        # Execute the tool if not finish
        if not tool_use:
            # Shouldn't happen, but handle gracefully
            logger.warning("No tool invocation in message")
            message_list.completed_at = datetime.now()
            break
        
        tool_name = tool_use.tool_name
        tool_args = tool_use.tool_args
        
        logger.debug(f"Tool args: {tool_args}")
        
        # Execute tool and add observation
        if tool_name in tool_registry.get_all_tools():
            try:
                # Use centralized tool execution with session
                result = tool_registry.execute_tool_with_session(
                    tool_name=tool_name,
                    session=session,
                    **tool_args
                )
                logger.debug(f"Tool result: {result}")
                
                # Demo logging for tool result
                if verbose:
                    result_str = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                    print(f"  Result: {result_str}")
                
                execution_time = (time.time() - iteration_start) * 1000
                message_list.add_tool_result(
                    tool_use_id=tool_use.tool_use_id,
                    tool_name=tool_name,
                    status=ToolStatus.SUCCESS,
                    result=result,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                # Handle tool execution errors
                logger.error(f"Tool execution error: {e}", exc_info=True)
                message_list.add_tool_result(
                    tool_use_id=tool_use.tool_use_id,
                    tool_name=tool_name,
                    status=ToolStatus.ERROR,
                    error=str(e),
                    execution_time_ms=(time.time() - iteration_start) * 1000
                )
        else:
            # Handle unknown tool selection
            logger.warning(f"Unknown tool: {tool_name}")
            message_list.add_tool_result(
                tool_use_id=tool_use.tool_use_id,
                tool_name=tool_name,
                status=ToolStatus.ERROR,
                error=f"Unknown tool: {tool_name}",
                execution_time_ms=0
            )
    
    # Check if we hit the iteration limit
    if message_list.iteration_count >= max_iterations:
        logger.warning(f"Reached maximum iterations ({max_iterations})")
    
    if not message_list.completed_at:
        message_list.completed_at = datetime.now()
    
    # Demo logging summary
    if verbose:
        print(f"summary:")
        print(f"✓ React loop completed")
        print(f"  Total iterations: {message_list.iteration_count}")
        if message_list.tools_used:
            print(f"  Tools used: {', '.join(message_list.tools_used)}")
        else:
            print("  Tools used: None (used context)")
        print()
    
    return message_list


def extract_final_answer(
    messages: MessageList,
    user_query: str,
    tool_set_name: str,
    verbose: bool = False
) -> ExtractResult:
    """
    Extract the final answer from the message list using the Extract Agent.
    
    This implements the Extract phase of the React → Extract → Observe pattern.
    The Extract Agent analyzes the complete message history to synthesize
    a coherent final answer.
    
    Args:
        messages: The complete MessageList from the React loop
        user_query: The original user query for context
        tool_set_name: Name of the tool set being used (for history saving)
        verbose: Whether to show detailed execution logs
        
    Returns:
        ExtractResult with answer, reasoning, confidence, and sources
    """
    # Use messages directly
    message_list = messages
    
    logger.debug("Extracting final answer from message list")
    logger.debug(f"Message list has {message_list.iteration_count} iterations")
    
    # Create a signature for answer extraction
    # This defines the contract for the Extract Agent
    class AnswerExtractionSignature(dspy.Signature):
        """Extract a clear, concise answer from the gathered information."""
        user_query: str = dspy.InputField(desc="The user's original question")
        answer: str = dspy.OutputField(desc="Clear, direct answer to the user's question")
    
    # Demo logging Extract Agent section
    if verbose:
        print(f"{'='*80}")
        print("Extract Agent")
        print(f"{'='*80}")
    
    # Initialize Extract Agent with Chain of Thought reasoning
    extract_agent = ReactExtract(signature=AnswerExtractionSignature)
    
    # Extract answer from message list
    logger.debug("Calling Extract Agent")
    result = extract_agent(
        message_list=message_list,
        user_query=user_query
    )
    
    # Demo logging Extract Agent results
    if verbose:
        print("log of call results:")
        print("✓ Answer extracted and synthesized")
        print()
    
    # History saving removed - use dspy.inspect_history() for debugging
    
    logger.debug("Successfully extracted final answer")
    
    # Return structured ExtractResult
    return ExtractResult(
        answer=result.answer,
        reasoning=getattr(result, 'reasoning', '')
    )