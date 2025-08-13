"""
Extract Agent - Isolated ReAct Extract functionality
This module synthesizes the final answer from a trajectory using dspy.ChainOfThought.
"""

import logging
from typing import TYPE_CHECKING, Type

import dspy
from dspy.primitives.module import Module
from dspy.signatures.signature import ensure_signature
from shared.trajectory_models import Trajectory

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dspy.signatures.signature import Signature


class ReactExtract(Module):
    """
    ReAct Extract functionality - synthesizes final answers from trajectories.
    This is the reasoning module that processes the complete trajectory to produce final outputs.
    """
    
    def __init__(self, signature: Type["Signature"]):
        """
        Initialize the ReactExtract module with signature.
        
        Args:
            signature: The signature defining input/output fields for final extraction
        """
        super().__init__()
        self.signature = signature = ensure_signature(signature)

        # Create fallback signature that includes trajectory as input
        # This allows ChainOfThought to reason over the complete interaction history
        fallback_signature = dspy.Signature(
            {**signature.input_fields, **signature.output_fields},
            signature.instructions,
        ).append("trajectory", dspy.InputField(), type_=str)

        self.extract = dspy.ChainOfThought(fallback_signature)

    def forward(self, trajectory: Trajectory, **input_args):
        """
        Extract final answer from trajectory using Chain of Thought reasoning.
        
        Args:
            trajectory: Trajectory object containing the complete interaction history
            **input_args: Original input arguments from the signature
            
        Returns:
            dspy.Prediction with final extracted answers and reasoning
        """
        # Format trajectory for the LLM
        formatted_trajectory = trajectory.to_llm_format()
        
        # Use ChainOfThought to reason over the trajectory and extract final answer
        extract_result = self.extract(
            **input_args,
            trajectory=formatted_trajectory
        )
        
        return dspy.Prediction(
            **extract_result,
            trajectory=trajectory,
            formatted_trajectory=formatted_trajectory
        )