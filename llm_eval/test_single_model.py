#!/usr/bin/env python3
"""
Test a single model to verify configuration
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from llm_eval.eval_harness import LLMEvaluator, EvaluatorConfig

def main():
    """Test a single model"""
    # Load environment variables
    load_dotenv()
    
    # Get model to test from command line or use default
    if len(sys.argv) > 1:
        provider = sys.argv[1]
        model = sys.argv[2] if len(sys.argv) > 2 else None
        display_name = sys.argv[3] if len(sys.argv) > 3 else f"{provider}/{model}"
    else:
        # Default to testing GPT-4o
        provider = "openrouter"
        model = "openai/gpt-4o"
        display_name = "GPT-4o Test"
    
    print(f"Testing single model: {display_name}")
    print(f"Provider: {provider}, Model: {model}")
    print()
    
    # Create evaluator with custom config
    config = EvaluatorConfig(
        max_iterations=10,
        start_index=13,
        verbose=True
    )
    evaluator = LLMEvaluator(config)
    
    # Load just test case 13
    evaluator.load_test_cases(start_index=13)
    evaluator.test_cases = evaluator.test_cases[:1]
    
    # Add just the model to test
    evaluator.add_model(provider, model, display_name)
    
    print(f"Running test case: {evaluator.test_cases[0].description}")
    print()
    
    # Run evaluation
    try:
        evaluations = evaluator.run_evaluation()
        
        if evaluations:
            eval = evaluations[0]
            print("\n" + "="*60)
            print("RESULTS")
            print("="*60)
            print(f"Model: {eval.model_name}")
            print(f"Success: {eval.successful_tests}/{eval.total_tests}")
            print(f"Average Iterations: {eval.average_iterations:.1f}")
            print(f"Average Time: {eval.average_execution_time:.2f}s")
            print(f"Tools Accuracy: {eval.tools_accuracy:.0f}%")
            
            if eval.test_results:
                result = eval.test_results[0]
                print(f"\nTest Status: {result.status}")
                print(f"Iterations Used: {result.total_iterations}")
                print(f"Tools Used: {', '.join(result.tools_used)}")
                print(f"Tools Match: {result.tools_match}")
        else:
            print("No evaluation results")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()