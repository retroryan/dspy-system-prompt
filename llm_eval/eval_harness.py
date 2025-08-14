#!/usr/bin/env python3
"""
LLM Evaluation Harness for E-commerce Test Cases

This script evaluates different LLM models on complex e-commerce test cases,
measuring their efficiency and effectiveness in multi-step tool use scenarios.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import dspy
from dotenv import load_dotenv
from shared.llm_utils import setup_llm
from shared.tool_utils.registry import ToolRegistry
from tools.ecommerce.tool_set import EcommerceToolSet
from agentic_loop.core_loop import run_agent_loop
from shared.trajectory_models import Trajectory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class IterationDetail(BaseModel):
    """Details of a single iteration"""
    model_config = ConfigDict(frozen=True)
    
    iteration: int = Field(..., ge=1, description="Iteration number")
    thought: str = Field(..., description="Agent's thought process")
    tool_name: str = Field(..., description="Name of tool invoked")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    tool_result: Optional[str] = Field(None, description="Tool execution result")
    execution_time: float = Field(..., ge=0, description="Execution time in seconds")


class TestResult(BaseModel):
    """Result of a single test case"""
    model_config = ConfigDict(frozen=True)
    
    test_id: int = Field(..., ge=1, description="Test case ID")
    test_description: str = Field(..., description="Test case description")
    query: str = Field(..., description="User query")
    status: str = Field(..., pattern="^(success|failed|error)$", description="Test status")
    total_iterations: int = Field(..., ge=0, description="Total iterations used")
    execution_time: float = Field(..., ge=0, description="Total execution time")
    tools_used: List[str] = Field(default_factory=list, description="Tools actually used")
    expected_tools: List[str] = Field(default_factory=list, description="Expected tools")
    tools_match: bool = Field(..., description="Whether tools match expected")
    final_answer: str = Field(default="", description="Final answer from agent")
    error: Optional[str] = Field(None, description="Error message if failed")
    iteration_details: List[IterationDetail] = Field(default_factory=list, description="Detailed iteration breakdown")
    
    def get_efficiency_score(self) -> float:
        """Calculate efficiency score (lower is better)"""
        if self.status != 'success':
            return float('inf')
        
        # Penalize for extra iterations and mismatched tools
        base_score = self.total_iterations
        if not self.tools_match:
            base_score += 5  # Penalty for using wrong tools
        
        return base_score


class ModelEvaluation(BaseModel):
    """Evaluation results for a single model"""
    model_config = ConfigDict(frozen=True)
    
    model_name: str = Field(..., description="Model display name")
    model_provider: str = Field(..., description="Model provider (openrouter, ollama, etc)")
    test_results: List[TestResult] = Field(default_factory=list, description="All test results")
    total_tests: int = Field(..., ge=0, description="Total number of tests")
    successful_tests: int = Field(..., ge=0, description="Number of successful tests")
    failed_tests: int = Field(..., ge=0, description="Number of failed tests")
    average_iterations: float = Field(..., ge=0, description="Average iterations for successful tests")
    average_execution_time: float = Field(..., ge=0, description="Average execution time")
    tools_accuracy: float = Field(..., ge=0, le=100, description="Percentage of tests with correct tools")
    
    @classmethod
    def from_results(cls, model_name: str, provider: str, results: List[TestResult]) -> "ModelEvaluation":
        """Create evaluation from test results"""
        successful = [r for r in results if r.status == 'success']
        failed = [r for r in results if r.status != 'success']
        
        avg_iterations = sum(r.total_iterations for r in successful) / len(successful) if successful else 0
        avg_time = sum(r.execution_time for r in successful) / len(successful) if successful else 0
        tools_accuracy = sum(1 for r in successful if r.tools_match) / len(successful) * 100 if successful else 0
        
        return cls(
            model_name=model_name,
            model_provider=provider,
            test_results=results,
            total_tests=len(results),
            successful_tests=len(successful),
            failed_tests=len(failed),
            average_iterations=avg_iterations,
            average_execution_time=avg_time,
            tools_accuracy=tools_accuracy
        )


class ModelConfig(BaseModel):
    """Configuration for a model to test"""
    provider: str = Field(..., description="Provider name (openrouter, ollama, etc)")
    model: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Display name for reports")


class EvaluatorConfig(BaseModel):
    """Configuration for the LLM evaluator"""
    output_dir: Path = Field(default=Path("llm_eval/results"), description="Output directory for results")
    max_iterations: int = Field(default=10, ge=1, description="Maximum iterations per test")
    start_index: int = Field(default=13, ge=1, description="Starting test case index")
    verbose: bool = Field(default=False, description="Verbose output")


class LLMEvaluator:
    """Main evaluator class for testing different LLMs"""
    
    def __init__(self, config: Optional[EvaluatorConfig] = None):
        """Initialize the evaluator with configuration"""
        self.config = config or EvaluatorConfig()
        self.output_dir = self.config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_cases = []
        self.models_to_test: List[ModelConfig] = []
        
    def load_test_cases(self, start_index: int = 13):
        """Load test cases from EcommerceToolSet"""
        all_test_cases = EcommerceToolSet.get_test_cases()
        # Get test cases 13 and later (complex scenarios)
        self.test_cases = all_test_cases[start_index - 1:]
        logger.info(f"Loaded {len(self.test_cases)} test cases starting from index {start_index}")
        
    def add_model(self, provider: str, model: str, name: Optional[str] = None):
        """Add a model to test"""
        model_config = ModelConfig(
            provider=provider,
            model=model,
            name=name or f"{provider}/{model}"
        )
        self.models_to_test.append(model_config)
        
    def setup_model_env(self, provider: str, model: str):
        """Set up environment for a specific model"""
        # Set provider and model
        os.environ['DSPY_PROVIDER'] = provider
        
        if provider == 'openrouter':
            os.environ['OPENROUTER_MODEL'] = model
        elif provider == 'openai':
            os.environ['OPENAI_MODEL'] = model
        elif provider == 'anthropic':
            os.environ['ANTHROPIC_MODEL'] = model
        elif provider == 'ollama':
            os.environ['OLLAMA_MODEL'] = model
            
        # Setup LLM - this will configure dspy.settings.lm
        try:
            setup_llm()
        except Exception as e:
            logger.error(f"Failed to setup LLM: {e}")
            raise
        
    def run_single_test(self, test_case, test_index: int) -> TestResult:
        """Run a single test case and capture detailed results"""
        start_time = time.time()
        
        try:
            # Create tool registry and register tools
            tool_set = EcommerceToolSet()
            registry = ToolRegistry()
            registry.register_tool_set(tool_set)
            
            # Run the agent loop
            result = run_agent_loop(
                user_query=test_case.request,
                tool_registry=registry,
                tool_set_name='ecommerce',
                max_iterations=self.config.max_iterations
            )
            
            # Extract iteration details from trajectory
            iteration_details = []
            if result['status'] == 'success':
                trajectory: Trajectory = result['trajectory']
                
                for step in trajectory.steps:
                    # Access the tool invocation information
                    if step.tool_invocation and step.tool_invocation.tool_name != 'finish':
                        # Get execution time in seconds from milliseconds
                        exec_time = step.observation.execution_time_ms / 1000.0 if step.observation else 0.0
                        
                        # Format observation result
                        obs_result = None
                        if step.observation and step.observation.result:
                            obs_str = str(step.observation.result)
                            obs_result = obs_str[:100] + '...' if len(obs_str) > 100 else obs_str
                        
                        iteration_details.append(IterationDetail(
                            iteration=step.iteration,
                            thought=step.thought.content[:100] + '...' if len(step.thought.content) > 100 else step.thought.content,
                            tool_name=step.tool_invocation.tool_name,
                            tool_args=step.tool_invocation.tool_args,
                            tool_result=obs_result,
                            execution_time=exec_time
                        ))
                
                # Use the trajectory's built-in tools_used property
                tools_used = trajectory.tools_used
                
                return TestResult(
                    test_id=test_index + 13,  # Adjust for starting at test 13
                    test_description=test_case.description,
                    query=test_case.request,
                    status='success',
                    total_iterations=trajectory.iteration_count,
                    execution_time=time.time() - start_time,
                    tools_used=tools_used,
                    expected_tools=test_case.expected_tools,
                    tools_match=set(tools_used) == set(test_case.expected_tools),
                    final_answer=result.get('answer', ''),
                    iteration_details=iteration_details
                )
            else:
                return TestResult(
                    test_id=test_index + 13,
                    test_description=test_case.description,
                    query=test_case.request,
                    status='failed',
                    total_iterations=0,
                    execution_time=time.time() - start_time,
                    tools_used=[],
                    expected_tools=test_case.expected_tools,
                    tools_match=False,
                    final_answer='',
                    error=result.get('error', 'Unknown error')
                )
                
        except Exception as e:
            logger.error(f"Error running test: {e}")
            return TestResult(
                test_id=test_index + 13,
                test_description=test_case.description,
                query=test_case.request,
                status='error',
                total_iterations=0,
                execution_time=time.time() - start_time,
                tools_used=[],
                expected_tools=test_case.expected_tools,
                tools_match=False,
                final_answer='',
                error=str(e)
            )
            
    def evaluate_model(self, provider: str, model: str, name: str) -> ModelEvaluation:
        """Evaluate a single model on all test cases"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluating model: {name}")
        logger.info(f"Provider: {provider}, Model: {model}")
        logger.info(f"{'='*60}")
        
        # Setup model environment
        self.setup_model_env(provider, model)
        
        results = []
        for i, test_case in enumerate(self.test_cases):
            logger.info(f"\nRunning test {i+13}: {test_case.description}")
            result = self.run_single_test(test_case, i)
            results.append(result)
            
            # Log iteration details
            logger.info(f"  Status: {result.status}")
            logger.info(f"  Iterations: {result.total_iterations}")
            logger.info(f"  Tools used: {', '.join(result.tools_used)}")
            logger.info(f"  Expected: {', '.join(result.expected_tools)}")
            logger.info(f"  Tools match: {result.tools_match}")
            
            if result.iteration_details:
                logger.info("  Iteration breakdown:")
                for detail in result.iteration_details:
                    logger.info(f"    [{detail.iteration}] {detail.tool_name}: {detail.thought[:50]}...")
                    
        return ModelEvaluation.from_results(name, provider, results)
        
    def run_evaluation(self) -> List[ModelEvaluation]:
        """Run evaluation for all models"""
        evaluations = []
        
        for model_config in self.models_to_test:
            try:
                eval_result = self.evaluate_model(
                    provider=model_config.provider,
                    model=model_config.model,
                    name=model_config.name
                )
                evaluations.append(eval_result)
                
                # Save individual model results
                self.save_model_results(eval_result)
                
            except Exception as e:
                logger.error(f"Failed to evaluate {model_config.name}: {e}")
                
        return evaluations
        
    def save_model_results(self, evaluation: ModelEvaluation):
        """Save model evaluation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{evaluation.model_name.replace('/', '_')}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Use Pydantic's model_dump for JSON serialization
        data = evaluation.model_dump(mode='json')
        
        # Add metadata
        data['metadata'] = {
            'timestamp': timestamp,
            'evaluator_config': self.config.model_dump(mode='json')
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
        logger.info(f"Saved results to {filepath}")
        
    def generate_comparison_report(self, evaluations: List[ModelEvaluation]):
        """Generate a comparison report of all models"""
        print("\n" + "="*80)
        print("LLM EVALUATION SUMMARY REPORT")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Cases: {len(self.test_cases)} complex e-commerce scenarios")
        print("\n" + "-"*80)
        print("MODEL PERFORMANCE COMPARISON")
        print("-"*80)
        
        # Sort by average iterations (efficiency)
        evaluations.sort(key=lambda x: x.average_iterations if x.average_iterations > 0 else float('inf'))
        
        # Print header
        print(f"{'Model':<30} {'Success':<10} {'Avg Iter':<10} {'Avg Time':<10} {'Tool Acc':<10}")
        print("-"*70)
        
        for eval in evaluations:
            success_rate = f"{eval.successful_tests}/{eval.total_tests}"
            avg_iter = f"{eval.average_iterations:.1f}" if eval.average_iterations > 0 else "N/A"
            avg_time = f"{eval.average_execution_time:.2f}s" if eval.average_execution_time > 0 else "N/A"
            tool_acc = f"{eval.tools_accuracy:.0f}%" if eval.successful_tests > 0 else "N/A"
            
            print(f"{eval.model_name:<30} {success_rate:<10} {avg_iter:<10} {avg_time:<10} {tool_acc:<10}")
            
        # Detailed breakdown by test case
        print("\n" + "-"*80)
        print("DETAILED TEST CASE BREAKDOWN")
        print("-"*80)
        
        for i, test_case in enumerate(self.test_cases):
            print(f"\nTest {i+13}: {test_case.description}")
            print(f"Query: {test_case.request[:60]}...")
            print(f"Expected tools: {', '.join(test_case.expected_tools)}")
            print()
            
            print(f"{'Model':<30} {'Status':<10} {'Iterations':<12} {'Tools Match':<12}")
            print("-"*64)
            
            for eval in evaluations:
                if i < len(eval.test_results):
                    result = eval.test_results[i]
                    status = "✓" if result.status == 'success' else "✗"
                    tools_match = "✓" if result.tools_match else "✗"
                    iterations = str(result.total_iterations) if result.status == 'success' else "N/A"
                    
                    print(f"{eval.model_name:<30} {status:<10} {iterations:<12} {tools_match:<12}")
                    
        # Save report to file
        report_path = self.output_dir / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            # Recreate the report for file
            f.write("="*80 + "\n")
            f.write("LLM EVALUATION SUMMARY REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Test Cases: {len(self.test_cases)} complex e-commerce scenarios\n\n")
            
            for eval in evaluations:
                f.write(f"\n{eval.model_name}\n")
                f.write(f"  Success Rate: {eval.successful_tests}/{eval.total_tests}\n")
                f.write(f"  Average Iterations: {eval.average_iterations:.1f}\n")
                f.write(f"  Average Time: {eval.average_execution_time:.2f}s\n")
                f.write(f"  Tools Accuracy: {eval.tools_accuracy:.0f}%\n")
                
        print(f"\n\nReport saved to: {report_path}")


def main():
    """Main evaluation function"""
    # Load environment variables
    load_dotenv()
    
    # Create evaluator
    evaluator = LLMEvaluator()
    
    # Load test cases (13 and later)
    evaluator.load_test_cases(start_index=13)
    
    # Add models to test
    # Current model from .env
    current_provider = os.getenv('DSPY_PROVIDER', 'ollama')
    if current_provider == 'ollama':
        current_model = os.getenv('OLLAMA_MODEL', 'gemma3:27b')
        evaluator.add_model('ollama', current_model, f"ollama/{current_model}")
    elif current_provider == 'openrouter':
        current_model = os.getenv('OPENROUTER_MODEL', '')
        if current_model:
            evaluator.add_model('openrouter', current_model, f"openrouter/{current_model}")
    
    # Add OpenRouter models
    evaluator.add_model('openrouter', 'openai/gpt-4o', 'OpenAI GPT-4o')
    evaluator.add_model('openrouter', 'google/gemini-2.0-flash-exp:free', 'Gemini 2.0 Flash')
    evaluator.add_model('openrouter', 'anthropic/claude-3.5-sonnet', 'Claude 3.5 Sonnet')
    evaluator.add_model('openrouter', 'anthropic/claude-3-opus', 'Claude 3 Opus')
    evaluator.add_model('openrouter', 'google/gemini-pro-1.5', 'Gemini 1.5 Pro')
    
    # Run evaluation
    print("Starting LLM evaluation...")
    print(f"Testing {len(evaluator.models_to_test)} models on {len(evaluator.test_cases)} test cases")
    
    evaluations = evaluator.run_evaluation()
    
    # Generate comparison report
    evaluator.generate_comparison_report(evaluations)
    
    print("\nEvaluation complete!")


if __name__ == "__main__":
    main()