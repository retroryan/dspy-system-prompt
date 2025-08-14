"""
Pydantic models for LLM evaluation framework

This module contains all the data models used in the evaluation harness,
providing type-safe structures for test results, model configurations,
and evaluation metrics.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class IterationMetrics(BaseModel):
    """Metrics for a single iteration in the agent loop"""
    model_config = ConfigDict(frozen=True)
    
    iteration_number: int = Field(..., ge=1, description="Iteration number (1-based)")
    thought: str = Field(..., description="Agent's reasoning for this step")
    tool_name: str = Field(..., description="Name of tool invoked")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to tool")
    tool_result: Optional[str] = Field(None, description="Tool execution result (truncated)")
    execution_time_ms: float = Field(..., ge=0, description="Execution time in milliseconds")
    success: bool = Field(True, description="Whether tool execution succeeded")
    error_message: Optional[str] = Field(None, description="Error message if tool failed")


class TestCaseResult(BaseModel):
    """Result of running a single test case"""
    model_config = ConfigDict(frozen=True)
    
    # Test identification
    test_id: int = Field(..., ge=1, description="Test case ID")
    test_name: str = Field(..., description="Test case name/description")
    query: str = Field(..., description="User query for the test")
    
    # Execution results
    status: str = Field(..., pattern="^(success|failed|error|timeout)$")
    total_iterations: int = Field(..., ge=0, description="Total iterations used")
    execution_time_seconds: float = Field(..., ge=0, description="Total execution time")
    
    # Tool usage analysis
    tools_used: List[str] = Field(default_factory=list, description="Tools actually used")
    expected_tools: List[str] = Field(default_factory=list, description="Expected tools")
    tools_match: bool = Field(False, description="Whether tools match expected")
    unexpected_tools: List[str] = Field(default_factory=list, description="Tools used but not expected")
    missing_tools: List[str] = Field(default_factory=list, description="Expected tools not used")
    
    # Detailed metrics
    iterations: List[IterationMetrics] = Field(default_factory=list)
    final_answer: str = Field(default="", description="Final answer from agent")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Computed metrics
    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score (lower is better)"""
        if self.status != 'success':
            return float('inf')
        
        base_score = self.total_iterations
        if not self.tools_match:
            base_score += 5  # Penalty for wrong tools
        if self.total_iterations >= 10:
            base_score += 3  # Penalty for hitting iteration limit
        
        return base_score
    
    @property
    def average_iteration_time(self) -> float:
        """Average time per iteration in seconds"""
        if self.total_iterations == 0:
            return 0
        return self.execution_time_seconds / self.total_iterations


class ModelPerformance(BaseModel):
    """Performance metrics for a single model across all tests"""
    model_config = ConfigDict(frozen=True)
    
    # Model identification
    model_name: str = Field(..., description="Display name for the model")
    provider: str = Field(..., description="Provider (openrouter, ollama, etc)")
    model_id: str = Field(..., description="Model identifier")
    
    # Test results
    test_results: List[TestCaseResult] = Field(default_factory=list)
    
    # Aggregate metrics
    total_tests: int = Field(..., ge=0)
    successful_tests: int = Field(..., ge=0)
    failed_tests: int = Field(..., ge=0)
    error_tests: int = Field(..., ge=0)
    
    # Performance metrics
    average_iterations: float = Field(..., ge=0, description="Avg iterations for successful tests")
    average_execution_time: float = Field(..., ge=0, description="Avg time for successful tests")
    median_iterations: float = Field(..., ge=0, description="Median iterations for successful tests")
    tools_accuracy_percent: float = Field(..., ge=0, le=100, description="% of tests with correct tools")
    
    # Efficiency metrics
    average_efficiency_score: float = Field(..., ge=0)
    success_rate_percent: float = Field(..., ge=0, le=100)
    
    @classmethod
    def from_test_results(cls, model_name: str, provider: str, model_id: str, 
                          results: List[TestCaseResult]) -> "ModelPerformance":
        """Create performance metrics from test results"""
        successful = [r for r in results if r.status == 'success']
        failed = [r for r in results if r.status == 'failed']
        errors = [r for r in results if r.status == 'error']
        
        # Calculate metrics
        avg_iterations = sum(r.total_iterations for r in successful) / len(successful) if successful else 0
        avg_time = sum(r.execution_time_seconds for r in successful) / len(successful) if successful else 0
        
        # Calculate median iterations
        if successful:
            sorted_iterations = sorted(r.total_iterations for r in successful)
            n = len(sorted_iterations)
            median_iterations = sorted_iterations[n//2] if n % 2 else (sorted_iterations[n//2-1] + sorted_iterations[n//2]) / 2
        else:
            median_iterations = 0
        
        tools_accuracy = sum(1 for r in successful if r.tools_match) / len(successful) * 100 if successful else 0
        avg_efficiency = sum(r.efficiency_score for r in successful) / len(successful) if successful else float('inf')
        success_rate = len(successful) / len(results) * 100 if results else 0
        
        return cls(
            model_name=model_name,
            provider=provider,
            model_id=model_id,
            test_results=results,
            total_tests=len(results),
            successful_tests=len(successful),
            failed_tests=len(failed),
            error_tests=len(errors),
            average_iterations=avg_iterations,
            average_execution_time=avg_time,
            median_iterations=median_iterations,
            tools_accuracy_percent=tools_accuracy,
            average_efficiency_score=avg_efficiency,
            success_rate_percent=success_rate
        )


class EvaluationSession(BaseModel):
    """Complete evaluation session with all models and results"""
    model_config = ConfigDict(frozen=True)
    
    # Session metadata
    session_id: str = Field(..., description="Unique session identifier")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None)
    
    # Configuration
    test_suite: str = Field(..., description="Name of test suite used")
    max_iterations: int = Field(..., ge=1, description="Max iterations per test")
    test_cases_count: int = Field(..., ge=1, description="Number of test cases")
    
    # Results
    model_performances: List[ModelPerformance] = Field(default_factory=list)
    
    # Rankings
    @property
    def efficiency_ranking(self) -> List[str]:
        """Models ranked by efficiency (best first)"""
        return [
            m.model_name for m in sorted(
                self.model_performances,
                key=lambda x: x.average_efficiency_score
            )
        ]
    
    @property
    def accuracy_ranking(self) -> List[str]:
        """Models ranked by tool accuracy (best first)"""
        return [
            m.model_name for m in sorted(
                self.model_performances,
                key=lambda x: x.tools_accuracy_percent,
                reverse=True
            )
        ]
    
    @property
    def success_rate_ranking(self) -> List[str]:
        """Models ranked by success rate (best first)"""
        return [
            m.model_name for m in sorted(
                self.model_performances,
                key=lambda x: x.success_rate_percent,
                reverse=True
            )
        ]
    
    def get_comparison_matrix(self) -> Dict[str, Dict[str, Any]]:
        """Get comparison matrix of all models"""
        matrix = {}
        for perf in self.model_performances:
            matrix[perf.model_name] = {
                'success_rate': f"{perf.success_rate_percent:.1f}%",
                'avg_iterations': f"{perf.average_iterations:.1f}",
                'median_iterations': f"{perf.median_iterations:.1f}",
                'avg_time': f"{perf.average_execution_time:.2f}s",
                'tools_accuracy': f"{perf.tools_accuracy_percent:.1f}%",
                'efficiency_score': f"{perf.average_efficiency_score:.2f}"
            }
        return matrix


class EvaluationReport(BaseModel):
    """Formatted evaluation report for display"""
    model_config = ConfigDict(frozen=True)
    
    session: EvaluationSession
    summary: str = Field(..., description="Executive summary")
    detailed_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    def generate_markdown(self) -> str:
        """Generate markdown report"""
        lines = [
            "# LLM Evaluation Report",
            f"**Session ID**: {self.session.session_id}",
            f"**Date**: {self.session.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Test Suite**: {self.session.test_suite}",
            f"**Test Cases**: {self.session.test_cases_count}",
            "",
            "## Executive Summary",
            self.summary,
            "",
            "## Model Rankings",
            "",
            "### By Efficiency",
            *[f"{i+1}. {name}" for i, name in enumerate(self.session.efficiency_ranking)],
            "",
            "### By Tool Accuracy",
            *[f"{i+1}. {name}" for i, name in enumerate(self.session.accuracy_ranking)],
            "",
            "### By Success Rate",
            *[f"{i+1}. {name}" for i, name in enumerate(self.session.success_rate_ranking)],
            "",
            "## Detailed Findings",
            *[f"- {finding}" for finding in self.detailed_findings],
            "",
            "## Recommendations",
            *[f"- {rec}" for rec in self.recommendations],
        ]
        return "\n".join(lines)