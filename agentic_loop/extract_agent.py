"""
Extract Agent - Isolated ReAct Extract functionality
This module synthesizes the final answer from a message list using dspy.ChainOfThought.
"""

import logging
from typing import TYPE_CHECKING, Type

import dspy
from dspy.primitives.module import Module
from dspy.signatures.signature import ensure_signature
from shared.message_models import MessageList

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dspy.signatures.signature import Signature


class ReactExtract(Module):
    """
    ReAct Extract functionality - synthesizes final answers from message lists.
    This is the reasoning module that processes the complete message history to produce final outputs.
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

    def forward(self, message_list: MessageList, **input_args):
        """
        Extract final answer from message list using Chain of Thought reasoning.
        
        Args:
            message_list: MessageList object containing the complete interaction history
            **input_args: Original input arguments from the signature
            
        Returns:
            dspy.Prediction with final extracted answers and reasoning
        """
        # Format messages for the LLM
        formatted_messages = message_list.to_llm_format()
        
        # Use ChainOfThought to reason over the messages and extract final answer
        extract_result = self.extract(
            **input_args,
            trajectory=formatted_messages
        )
        
        return dspy.Prediction(
            **extract_result,
            message_list=message_list,
            formatted_messages=formatted_messages
        )