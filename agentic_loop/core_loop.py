"""
Core Agentic Loop Implementation

This module contains the core functionality for running the React → Extract → Observe pattern.
It handles the iterative agent loop, tool execution, and final answer extraction.

The agent loop follows these steps:
1. **React Phase**: The agent reasons about the current state and selects the next action
2. **Tool Execution**: The selected tool is executed with the provided arguments
3. **Observation**: Tool results are added to the trajectory for the next iteration
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
from typing import Dict, Any, Optional
from datetime import datetime

import dspy

from agentic_loop.react_agent import ReactAgent
from agentic_loop.extract_agent import ReactExtract
from shared.config import config
from shared.tool_utils.registry import ToolRegistry
from shared.trajectory_models import (
    Trajectory,
    ToolStatus,
    ExtractResult
)

# Initialize module-level logger
logger = logging.getLogger(__name__)


def run_react_loop(
    react_agent: ReactAgent,
    tool_registry: ToolRegistry,
    trajectory: Trajectory,
    user_query: str,
    context_prompt: str,
    max_iterations: int = 5,
    session_user_id: str = "demo_user",
    verbose: bool = False
) -> Trajectory:
    """
    Run the React agent loop with conversation context.
    
    This is the React loop implementation. All agent interactions
    go through this function via AgentSession.
    
    The loop implements the React pattern:
    - Thought: Agent reasons about the current state and context
    - Action: Agent selects a tool and arguments
    - Observation: Tool is executed and result is observed
    
    Args:
        react_agent: The initialized ReactAgent instance
        tool_registry: The tool registry for executing tools
        trajectory: Pre-initialized trajectory with metadata
        user_query: The user's question or task
        context_prompt: Conversation context (may be empty for first query)
        max_iterations: Maximum number of iterations
        verbose: Whether to show detailed execution logs
        
    Returns:
        Complete Trajectory object with all steps and observations
    """
    # Clean demo logging
    if verbose:
        print(f"{'='*80}")
        print("Starting React loop")
        print(f"{'='*80}")
    
    logger.debug("Starting ReactAgent loop")
    logger.debug(f"Query: {user_query}")
    logger.debug(f"Context size: {len(context_prompt)} chars")
    
    # Main agent loop
    while trajectory.iteration_count < max_iterations:
        iteration_start = time.time()
        iteration_num = trajectory.iteration_count + 1
        
        # Get next action from agent with context
        # Always pass context - agents created via AgentSession always support it
        trajectory = react_agent(
            trajectory=trajectory,
            user_query=user_query,
            conversation_context=context_prompt
        )

        # Get the last step that was just added
        last_step = trajectory.steps[-1]
        
        # No injection needed - will be handled during execution
        
        # Demo logging for React iteration
        if verbose:
            print(f"react loop call {iteration_num} - log of results:")
            if last_step.thought:
                print(f"  Thought: {last_step.thought.content}")
            if last_step.tool_invocation:
                print(f"  Tool: {last_step.tool_invocation.tool_name}")
                print(f"  Args: {last_step.tool_invocation.tool_args}")
            elif last_step.is_finish:
                print(f"  Action: Final Answer")
            print()
        
        # Check if agent has decided to finish
        if last_step.is_finish:
            trajectory.completed_at = datetime.now()
            break
        
        # Execute the tool from the last step (only for real tools, not 'finish')
        tool_invocation = last_step.tool_invocation
        if not tool_invocation:
            # Shouldn't happen, but handle gracefully
            logger.warning("No tool invocation in step")
            trajectory.completed_at = datetime.now()
            break
        
        tool_name = tool_invocation.tool_name
        tool_args = tool_invocation.tool_args
        
        logger.debug(f"Tool args: {tool_args}")
        
        # Execute tool and add observation
        if tool_name in tool_registry.get_all_tools():
            try:
                tool = tool_registry.get_tool(tool_name)
                
                # Check if tool has execute_with_user_id method
                if hasattr(tool, 'execute_with_user_id'):
                    result = tool.execute_with_user_id(session_user_id, **tool_args)
                else:
                    result = tool.execute(**tool_args)
                logger.debug(f"Tool result: {result}")
                
                # Demo logging for tool result
                if verbose:
                    result_str = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                    print(f"  Result: {result_str}")
                
                execution_time = (time.time() - iteration_start) * 1000
                trajectory.add_observation(
                    tool_name=tool_name,
                    status=ToolStatus.SUCCESS,
                    result=result,
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                # Handle tool execution errors
                logger.error(f"Tool execution error: {e}", exc_info=True)
                trajectory.add_observation(
                    tool_name=tool_name,
                    status=ToolStatus.ERROR,
                    error=str(e),
                    execution_time_ms=(time.time() - iteration_start) * 1000
                )
        else:
            # Handle unknown tool selection
            logger.warning(f"Unknown tool: {tool_name}")
            trajectory.add_observation(
                tool_name=tool_name,
                status=ToolStatus.ERROR,
                error=f"Unknown tool: {tool_name}",
                execution_time_ms=0
            )
    
    # Check if we hit the iteration limit
    if trajectory.iteration_count >= max_iterations:
        logger.warning(f"Reached maximum iterations ({max_iterations})")
    
    if not trajectory.completed_at:
        trajectory.completed_at = datetime.now()
    
    # Demo logging summary
    if verbose:
        print(f"summary:")
        print(f"✓ React loop completed")
        print(f"  Total iterations: {trajectory.iteration_count}")
        if trajectory.tools_used:
            print(f"  Tools used: {', '.join(trajectory.tools_used)}")
        else:
            print("  Tools used: None (used context)")
        print()
    
    return trajectory


def extract_final_answer(
    trajectory: Trajectory,
    user_query: str,
    tool_set_name: str,
    verbose: bool = False
) -> ExtractResult:
    """
    Extract the final answer from the trajectory using the Extract Agent.
    
    This implements the Extract phase of the React → Extract → Observe pattern.
    The Extract Agent analyzes the complete trajectory of thoughts, actions,
    and observations to synthesize a coherent final answer.
    
    Args:
        trajectory: The complete Trajectory object from the React loop
        user_query: The original user query for context
        tool_set_name: Name of the tool set being used (for history saving)
        
    Returns:
        ExtractResult with answer, reasoning, confidence, and sources
    """
    logger.debug("Extracting final answer from trajectory")
    logger.debug(f"Trajectory has {trajectory.iteration_count} steps")
    
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
    
    # Extract answer from trajectory
    logger.debug("Calling Extract Agent")
    result = extract_agent(
        trajectory=trajectory,
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