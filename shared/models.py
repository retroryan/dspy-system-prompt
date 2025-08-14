"""
Shared data models for tool selection and agentic loop implementation.

This module contains the combined Pydantic models used by both the tool selection
system and the agentic loop implementation, defining the structure for tool
invocations, decision outputs, and conversation state management.
"""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import time


# =============================================================================
# Core Tool Models (originally from tool_selection/models.py)
# =============================================================================

class ToolCall(BaseModel):
    """
    Represents a single invocation of a tool with its specified arguments.

    This model is used to structure the output of the tool selection process,
    indicating which tool should be called and with what parameters.
    """
    tool_name: str = Field(
        ..., 
        description="The unique name of the tool to be called (e.g., 'set_reminder')"
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict, 
        description="A dictionary of arguments to pass to the tool, where keys are argument names and values are their corresponding values."
    )


class MultiToolDecision(BaseModel):
    """
    Represents the comprehensive decision made by the tool selector.

    This model encapsulates the reasoning behind the tool selection and a list
    of one or more tool calls that should be executed to fulfill the user's request.
    """
    reasoning: str = Field(
        ..., 
        description="A detailed explanation or step-by-step thought process behind why the specific tools were selected and how they address the user's request."
    )
    tool_calls: List[ToolCall] = Field(
        ..., 
        description="A list of ToolCall objects, each representing a tool to be invoked. The order of tools in this list may or may not be significant depending on the 'execution_order_matters' flag in the signature."
    )


# =============================================================================
# Agentic Loop Models (originally from agentic_loop/models.py)
# =============================================================================


class ToolExecutionResult(BaseModel):
    """Result of executing a single tool."""
    
    tool_name: str = Field(
        ..., 
        description="Name of the tool that was executed"
    )
    success: bool = Field(
        default=True, 
        description="Whether the tool execution was successful"
    )
    result: Optional[Any] = Field(
        None, 
        description="Tool execution result if successful"
    )
    error: Optional[str] = Field(
        None, 
        description="Error message if execution failed"
    )
    error_type: Optional[str] = Field(
        None, 
        description="Type of error that occurred"
    )
    execution_time: float = Field(
        default=0, 
        description="Time taken to execute the tool"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Parameters passed to the tool"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage in conversation history."""
        return self.model_dump()




# =============================================================================
# Evaluation Models (originally from shared_utils/models.py)
# =============================================================================

class ToolSelectionEvaluation(BaseModel):
    """Evaluation metrics for a tool selection."""
    precision: float = Field(ge=0, le=1, description="Precision score")
    recall: float = Field(ge=0, le=1, description="Recall score")
    f1_score: float = Field(ge=0, le=1, description="F1 score")
    is_perfect_match: bool = Field(description="Whether selection perfectly matched expected")


class TestResult(BaseModel):
    """Result of a single test case execution."""
    test_case: Any = Field(description="The test case that was executed (ToolTestCase)")
    actual_tools: List[str] = Field(description="Tools actually selected")
    reasoning: str = Field(description="LLM's reasoning for the selection")
    evaluation: ToolSelectionEvaluation = Field(description="Evaluation metrics")
    execution_results: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Results from executing the selected tools"
    )
    error: Optional[str] = Field(default=None, description="Error message if test failed")
    duration_ms: Optional[float] = Field(default=None, description="Test execution time in milliseconds")


class TestSummary(BaseModel):
    """Summary of test suite execution."""
    model: str = Field(description="Model used for testing")
    timestamp: datetime = Field(default_factory=datetime.now, description="When tests were run")
    total_tests: int = Field(description="Total number of tests executed")
    passed_tests: int = Field(description="Number of tests that passed")
    perfect_matches: int = Field(description="Number of perfect matches")
    avg_precision: float = Field(ge=0, le=1, description="Average precision across all tests")
    avg_recall: float = Field(ge=0, le=1, description="Average recall across all tests")
    avg_f1_score: float = Field(ge=0, le=1, description="Average F1 score across all tests")
    total_duration_seconds: float = Field(description="Total execution time in seconds")
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        return (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0.0
    
    @property
    def perfect_match_rate(self) -> float:
        """Calculate the perfect match rate as a percentage."""
        return (self.perfect_matches / self.total_tests * 100) if self.total_tests > 0 else 0.0


class ModelComparisonResult(BaseModel):
    """Result of comparing multiple models."""
    models: List[str] = Field(description="Models that were compared")
    summaries: Dict[str, TestSummary] = Field(description="Summary for each model")
    detailed_results: Dict[str, List[TestResult]] = Field(
        description="Detailed results for each model"
    )
    comparison_timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="When comparison was run"
    )