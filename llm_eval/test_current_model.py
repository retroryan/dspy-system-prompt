#!/usr/bin/env python3
"""
Test the evaluation harness with just the current model from .env
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from llm_eval.eval_harness import LLMEvaluator

def main():
    """Test with current model only"""
    # Load environment variables
    load_dotenv()
    
    # Create evaluator
    evaluator = LLMEvaluator()
    
    # Load test cases (just test 13 for quick test)
    evaluator.load_test_cases(start_index=13)
    evaluator.test_cases = evaluator.test_cases[:1]  # Just test case 13
    
    # Add only current model
    current_provider = os.getenv('DSPY_PROVIDER', 'ollama')
    if current_provider == 'ollama':
        current_model = os.getenv('OLLAMA_MODEL', 'gemma3:27b')
        evaluator.add_model('ollama', current_model, f"ollama/{current_model}")
    elif current_provider == 'openrouter':
        current_model = os.getenv('OPENROUTER_MODEL', '')
        if current_model:
            evaluator.add_model('openrouter', current_model, f"openrouter/{current_model}")
    elif current_provider == 'anthropic':
        current_model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        evaluator.add_model('anthropic', current_model, f"anthropic/{current_model}")
    
    print(f"Testing with current model: {current_provider}")
    print(f"Running test case 13 only...")
    
    # Run evaluation
    try:
        evaluations = evaluator.run_evaluation()
        
        # Generate report
        evaluator.generate_comparison_report(evaluations)
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTest complete!")


if __name__ == "__main__":
    main()