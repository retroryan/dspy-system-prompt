"""
Clean Manual Agent Loop implementation following DSPy ReAct patterns.

This module provides a stateless agent loop that uses type-safe Pydantic
trajectory models, following the React pattern with explicit tool selection.
"""

import logging
from typing import Dict, Optional, Any
import dspy

from shared.tool_utils import BaseTool
from shared.tool_utils.registry import ToolRegistry
from shared.trajectory_models import Trajectory

from typing import TYPE_CHECKING, Literal, Type

if TYPE_CHECKING:
    from dspy.signatures.signature import Signature

class ReactAgent(dspy.Module):
    """
    React agent using type-safe Pydantic trajectory.
    """

    def __init__(self, signature: Type["Signature"], tool_registry: ToolRegistry):
        """
        Initialize the ReactAgent.
        
        Args:
            signature: The signature defining input/output fields
            tool_registry: Registry containing tool implementations
        """
        super().__init__()
        if not tool_registry:
            raise ValueError("tool_registry is required for ReactAgent")
        
        # Setup logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.tool_registry = tool_registry
        self.all_tools: Dict[str, BaseTool] = tool_registry.get_all_tools()

        # Build instruction components
        inputs = ", ".join([f"`{k}`" for k in signature.input_fields.keys()])
        outputs = ", ".join([f"`{k}`" for k in signature.output_fields.keys()])
        instr = [f"{signature.instructions}\n"] if signature.instructions else []

        instr.extend([
            f"You are an Agent. In each episode, you will be given the fields {inputs} as input. And you can see your past trajectory so far.",
            f"Your goal is to use one or more of the supplied tools to collect any necessary information for producing {outputs}.\n",
            "To do this, you will interleave next_thought, next_tool_name, and next_tool_args in each turn, and also when finishing the task.",
            "After each tool call, you receive a resulting observation, which gets appended to your trajectory.\n",
            "When writing next_thought, you may reason about the current situation and plan for future steps.",
            "When selecting the next_tool_name and its next_tool_args, the tool must be one of:\n",
        ])
        
        # Add finish tool to the tools dictionary before enumeration
        tools_with_finish = self.all_tools.copy()
        
        # Create a mock finish tool object for consistent formatting
        class FinishTool:
            NAME = "finish"
            description = f"Marks the task as complete. That is, signals that all information for producing the outputs, i.e. {outputs}, are now available to be extracted."
            
            def get_argument_details(self):
                return {}
        
        tools_with_finish["finish"] = FinishTool()
        
        # Add tool descriptions to instructions
        for idx, tool in enumerate(tools_with_finish.values()):
            # Get argument details from the tool
            arg_details = tool.get_argument_details()
            instr.append(f"({idx + 1}) Tool(name={tool.NAME}, desc={tool.description}, args={arg_details})")

        instr.append("When providing `next_tool_args`, the value inside the field must be in JSON format")

        self.logger.debug("=" * 25)
        self.logger.debug(f"Using instructions: {instr}")
        self.logger.debug("=" * 25)

        # Create the react signature for tool calling
        react_signature = (
            dspy.Signature({**signature.input_fields}, "\n".join(instr))
            .append("trajectory", dspy.InputField(), type_=str)
            .append("next_thought", dspy.OutputField(), type_=str)
            .append("next_tool_name", dspy.OutputField(), type_=Literal[tuple(tools_with_finish.keys())])
            .append("next_tool_args", dspy.OutputField(), type_=dict[str, Any])
        )

        self.react = dspy.Predict(react_signature)

    def forward(self, trajectory: Trajectory, **input_args) -> Trajectory:
        """
        Execute the reactive tool-calling loop with type-safe trajectory.
        
        The trajectory is updated with a new step containing the agent's
        thought and tool invocation decision (including 'finish' if complete).

        Args:
            trajectory: The Trajectory object to update
            **input_args: Other signature input fields (e.g., user_query)

        Returns:
            Updated trajectory with new step added
        """
        # Format trajectory for LLM
        trajectory_text = trajectory.to_llm_format()
        
        try:
            # Get prediction from LLM
            pred = self.react(
                **input_args,
                trajectory=trajectory_text
            )
            
            # Add step to trajectory with type safety
            # This handles both regular tools and the 'finish' pseudo-tool
            
            # Check if we got a valid response from the LLM
            if not pred.next_thought and not pred.next_tool_name:
                error_msg = "LLM failed to provide valid structured output (empty response). This model may not support DSPy's structured output format."
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Use the prediction values, ensuring they're not None
            thought_content = pred.next_thought if pred.next_thought is not None else "Analyzing the situation..."
            tool_name = pred.next_tool_name if pred.next_tool_name is not None else "finish"
            tool_args = pred.next_tool_args if pred.next_tool_args is not None else {}
            
            trajectory.add_step(
                thought=thought_content,
                tool_name=tool_name,
                tool_args=tool_args
            )
            
        except Exception as err:
            self.logger.warning(f"Agent failed to select a valid tool: {err}")
            # On error, signal finish to prevent infinite loops
            trajectory.add_step(
                thought=f"Error in agent reasoning: {str(err)}",
                tool_name="finish",
                tool_args={}
            )

        return trajectory
