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
from typing import Dict, Tuple, Any, Optional
from datetime import datetime

import dspy

from agentic_loop.react_agent import ReactAgent
from agentic_loop.extract_agent import ReactExtract
from shared.llm_utils import save_dspy_history
from shared.tool_utils.registry import ToolRegistry

# Initialize module-level logger
logger = logging.getLogger(__name__)


def run_react_loop(
    react_agent: ReactAgent,
    tool_registry: ToolRegistry,
    user_query: str,
    tool_set_name: str,
    max_iterations: int = 5
) -> Tuple[Dict[str, Any], float, Dict[str, Any]]:
    """
    Run the React agent loop until completion or max iterations.
    
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
        Tuple of (trajectory dictionary, execution time in seconds, iteration details)
        
    The trajectory dictionary contains:
        - thought_N: The agent's reasoning at iteration N
        - tool_name_N: The selected tool name at iteration N  
        - tool_args_N: The tool arguments at iteration N
        - observation_N: The tool execution result at iteration N
        
    The iteration details contains:
        - iteration_count: Number of iterations performed
        - iteration_timings: List of timing info for each iteration
    """
    trajectory = {}
    current_iteration = 1
    start_time = time.time()
    iteration_details = {
        'iteration_count': 0,
        'iteration_timings': []
    }
    
    # Check if DSPY debug mode is enabled for saving prompts
    dspy_debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"
    
    logger.debug("Starting ReactAgent loop")
    logger.debug(f"Query: {user_query}")
    
    # Main agent loop
    while current_iteration <= max_iterations:
        iteration_start = time.time()
        logger.debug(f"Iteration {current_iteration}/{max_iterations}")
        
        # Call ReactAgent to get next action
        # The agent receives the full trajectory and decides the next step
        trajectory, tool_name, tool_args = react_agent(
            trajectory=trajectory,
            current_iteration=current_iteration,
            user_query=user_query
        )
        
        # Save ReactAgent history if debug mode is enabled
        if dspy_debug_enabled:
            try:
                saved_path = save_dspy_history(
                    tool_set_name=tool_set_name,
                    agent_type="react",
                    index=current_iteration
                )
                if saved_path:
                    logger.debug(f"Saved ReactAgent history to: {saved_path}")
            except Exception as e:
                logger.warning(f"Failed to save ReactAgent history: {e}")
        
        logger.debug(f"Tool selected: {tool_name}")
        logger.debug(f"Tool args: {tool_args}")
        
        # Check if agent has decided to finish
        if tool_name == "finish":
            logger.debug("Agent selected 'finish' - task complete")
            # Add final observation to indicate completion
            trajectory[f"observation_{current_iteration-1}"] = "Completed."
            break
        
        # Execute the selected tool
        if tool_name in tool_registry.get_all_tools():
            try:
                tool = tool_registry.get_tool(tool_name)
                logger.debug(f"Executing tool: {tool_name}")
                result = tool.execute(**tool_args)
                logger.debug(f"Tool result: {result}")
                
                # Add tool result to trajectory as observation
                idx = current_iteration - 1
                trajectory[f"observation_{idx}"] = result
                
            except Exception as e:
                # Handle tool execution errors
                logger.error(f"Tool execution error: {e}", exc_info=True)
                trajectory[f"observation_{current_iteration-1}"] = f"Error: {e}"
        else:
            # Handle unknown tool selection
            logger.warning(f"Unknown tool: {tool_name}")
            trajectory[f"observation_{current_iteration-1}"] = f"Error: Unknown tool {tool_name}"
        
        # Track iteration timing
        iteration_time = time.time() - iteration_start
        iteration_details['iteration_timings'].append({
            'iteration': current_iteration,
            'time': iteration_time,
            'tool': tool_name,
            'thought': trajectory.get(f"thought_{current_iteration}", "")
        })
        
        current_iteration += 1
    
    # Check if we hit the iteration limit
    if current_iteration > max_iterations:
        logger.warning(f"Reached maximum iterations ({max_iterations})")
    
    execution_time = time.time() - start_time
    iteration_details['iteration_count'] = current_iteration - 1
    return trajectory, execution_time, iteration_details


def extract_final_answer(
    trajectory: Dict[str, Any],
    user_query: str,
    tool_set_name: str
) -> Tuple[str, str]:
    """
    Extract the final answer from the trajectory using the Extract Agent.
    
    This implements the Extract phase of the React → Extract → Observe pattern.
    The Extract Agent analyzes the complete trajectory of thoughts, actions,
    and observations to synthesize a coherent final answer.
    
    Args:
        trajectory: The complete trajectory from the React loop containing
                   all thoughts, actions, and observations
        user_query: The original user query for context
        tool_set_name: Name of the tool set being used (for history saving)
        
    Returns:
        Tuple of (answer, reasoning)
        - answer: The final synthesized answer to the user's query
        - reasoning: The agent's reasoning process (if available)
    """
    # Check if DEMO debug mode is enabled
    demo_debug_enabled = os.getenv("DEMO_DEBUG", "false").lower() == "true"
    
    logger.debug("Extracting final answer from trajectory")
    logger.debug(f"Trajectory keys: {list(trajectory.keys())}")
    
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
    return result.answer, getattr(result, 'reasoning', '')


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
        - trajectory: Complete trajectory of thoughts, actions, observations
        - tools_used: List of tools that were actually used
        - execution_time: Total execution time in seconds
        - answer: The final answer (if successful)
        - reasoning: The reasoning process (if available)
        - error: Error message (if status is 'error')
        
    Example:
        ```python
        registry = ToolRegistry()
        registry.register_tool_set(AgricultureToolSet())
        
        result = run_agent_loop(
            user_query="What's the weather forecast for Seattle?",
            tool_registry=registry,
            tool_set_name="agriculture"
        )
        
        print(result['answer'])
        ```
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
        
        # Run React loop
        trajectory, react_time, iteration_details = run_react_loop(
            react_agent=react_agent,
            tool_registry=tool_registry,
            user_query=user_query,
            tool_set_name=tool_set_name,
            max_iterations=max_iterations
        )
        
        # Extract tools that were actually used
        tools_used = []
        for key in sorted(trajectory.keys()):
            if key.startswith("tool_name_") and trajectory[key] != "finish":
                tools_used.append(trajectory[key])
        
        # Extract final answer using Extract Agent
        answer, reasoning = extract_final_answer(
            trajectory=trajectory,
            user_query=user_query,
            tool_set_name=tool_set_name
        )
        
        return {
            'status': 'success',
            'trajectory': trajectory,
            'tools_used': tools_used,
            'execution_time': react_time,
            'answer': answer,
            'reasoning': reasoning,
            'iteration_details': iteration_details
        }
        
    except Exception as e:
        logger.error(f"Agent loop failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'execution_time': 0,
            'tools_used': [],
            'trajectory': {}
        }