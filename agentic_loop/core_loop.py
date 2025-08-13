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
from shared.llm_utils import save_dspy_history
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
    user_query: str,
    tool_set_name: str,
    max_iterations: int = 5
) -> Trajectory:
    """
    Run the React agent loop with type-safe trajectory.
    
    This is the core loop that implements the React pattern:
    - Thought: Agent reasons about the current state
    - Action: Agent selects a tool and arguments
    - Observation: Tool is executed and result is observed
    
    The loop continues until:
    - The agent selects the "finish" action
    - Maximum iterations are reached
    - An unrecoverable error occurs
    
    Args:
        react_agent: The initialized ReactAgent instance
        tool_registry: The tool registry for executing tools
        user_query: The user's question or task
        tool_set_name: Name of the tool set being used (for history saving)
        max_iterations: Maximum number of iterations (default: 5)
        
    Returns:
        Complete Trajectory object with all steps and observations
    """
    # Initialize trajectory
    trajectory = Trajectory(
        user_query=user_query,
        tool_set_name=tool_set_name,
        max_iterations=max_iterations
    )
    
    # Check if DSPY debug mode is enabled for saving prompts
    dspy_debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"
    
    logger.debug("Starting ReactAgent loop")
    logger.debug(f"Query: {user_query}")
    
    # Main agent loop
    while trajectory.iteration_count < max_iterations:
        iteration_start = time.time()
        logger.debug(f"Iteration {trajectory.iteration_count + 1}/{max_iterations}")
        
        # Get next action from agent (trajectory is updated in-place)
        trajectory = react_agent(
            trajectory=trajectory,
            user_query=user_query
        )
        
        # Save ReactAgent history if debug mode is enabled
        if dspy_debug_enabled:
            try:
                saved_path = save_dspy_history(
                    tool_set_name=tool_set_name,
                    agent_type="react",
                    index=trajectory.iteration_count
                )
                if saved_path:
                    logger.debug(f"Saved ReactAgent history to: {saved_path}")
            except Exception as e:
                logger.warning(f"Failed to save ReactAgent history: {e}")
        
        # Get the last step that was just added
        last_step = trajectory.steps[-1]
        
        # Check if agent has decided to finish
        if last_step.is_finish:
            logger.debug("Agent selected 'finish' - task complete")
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
    
    return trajectory


def extract_final_answer(
    trajectory: Trajectory,
    user_query: str,
    tool_set_name: str
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
    # Check if DEMO debug mode is enabled
    demo_debug_enabled = os.getenv("DEMO_DEBUG", "false").lower() == "true"
    
    logger.debug("Extracting final answer from trajectory")
    logger.debug(f"Trajectory has {trajectory.iteration_count} steps")
    
    # Create a signature for answer extraction
    # This defines the contract for the Extract Agent
    class AnswerExtractionSignature(dspy.Signature):
        """Extract a clear, concise answer from the gathered information."""
        user_query: str = dspy.InputField(desc="The user's original question")
        answer: str = dspy.OutputField(desc="Clear, direct answer to the user's question")
    
    # Initialize Extract Agent with Chain of Thought reasoning
    extract_agent = ReactExtract(signature=AnswerExtractionSignature)
    
    # Extract answer from trajectory
    logger.debug("Calling Extract Agent")
    result = extract_agent(
        trajectory=trajectory,
        user_query=user_query
    )
    
    # Save ExtractAgent history if debug mode is enabled
    if demo_debug_enabled:
        try:
            saved_path = save_dspy_history(
                tool_set_name=tool_set_name,
                agent_type="extract",
                index=1  # Extract is typically called once at the end
            )
            if saved_path:
                logger.debug(f"Saved ExtractAgent history to: {saved_path}")
        except Exception as e:
            logger.warning(f"Failed to save ExtractAgent history: {e}")
    
    logger.debug("Successfully extracted final answer")
    
    # Return structured ExtractResult
    return ExtractResult(
        answer=result.answer,
        reasoning=getattr(result, 'reasoning', '')
    )


def run_agent_loop(
    user_query: str,
    tool_registry: ToolRegistry,
    tool_set_name: str,
    signature: Optional[dspy.Signature] = None,
    max_iterations: int = 5
) -> Dict[str, Any]:
    """
    Run the complete agent loop: React → Extract → Observe.
    
    This is the main entry point for running the agentic loop. It orchestrates:
    1. Initializing the React agent with the appropriate signature
    2. Running the React loop to gather information
    3. Extracting the final answer from the trajectory
    4. Returning comprehensive results
    
    Args:
        user_query: The user's question or task to complete
        tool_registry: Registry containing available tools
        tool_set_name: Name of the active tool set
        signature: Optional custom signature for the React agent.
                  If not provided, uses tool set signature or default.
        max_iterations: Maximum iterations for the React loop (default: 5)
        
    Returns:
        Dictionary containing:
        - status: 'success' or 'error'
        - trajectory: Complete Trajectory object
        - tools_used: List of tools that were actually used
        - execution_time: Total execution time in seconds
        - answer: The final answer (if successful)
        - reasoning: The reasoning process (if available)
        - total_iterations: Number of iterations performed
        - error: Error message (if status is 'error')
    """
    try:
        # Determine which signature to use
        if signature is None:
            # Try to get tool set specific signature
            tool_set_signature = tool_registry.get_react_signature()
            
            if tool_set_signature:
                # Format the signature's docstring with current date if needed
                current_date = datetime.now().strftime("%Y-%m-%d")
                if hasattr(tool_set_signature, '__doc__') and tool_set_signature.__doc__:
                    tool_set_signature.__doc__ = tool_set_signature.__doc__.format(current_date=current_date)
                signature = tool_set_signature
            else:
                # Fallback to generic signature
                class DefaultReactSignature(dspy.Signature):
                    """Use tools to answer the user's question."""
                    user_query: str = dspy.InputField(desc="The user's question")
                signature = DefaultReactSignature
        
        # Initialize ReactAgent
        react_agent = ReactAgent(
            signature=signature,
            tool_registry=tool_registry
        )
        
        # Run React loop - returns complete trajectory
        trajectory = run_react_loop(
            react_agent=react_agent,
            tool_registry=tool_registry,
            user_query=user_query,
            tool_set_name=tool_set_name,
            max_iterations=max_iterations
        )
        
        # Extract final answer using Extract Agent
        extract_result = extract_final_answer(
            trajectory=trajectory,
            user_query=user_query,
            tool_set_name=tool_set_name
        )
        
        # Calculate execution time
        if trajectory.completed_at and trajectory.started_at:
            execution_time = (trajectory.completed_at - trajectory.started_at).total_seconds()
        else:
            execution_time = 0
        
        return {
            'status': 'success',
            'trajectory': trajectory,  # Clean Trajectory object
            'tools_used': trajectory.tools_used,
            'execution_time': execution_time,
            'answer': extract_result.answer,
            'reasoning': extract_result.reasoning,
            'total_iterations': trajectory.iteration_count
        }
        
    except Exception as e:
        logger.error(f"Agent loop failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'execution_time': 0,
            'tools_used': [],
            'trajectory': None  # Changed from {} to None for clean break
        }