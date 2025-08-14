#!/usr/bin/env python3
"""
Quick evaluation of OpenRouter models on a subset of test cases
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from llm_eval.eval_harness import LLMEvaluator

def main():
    """Run quick evaluation with fewer test cases"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Create evaluator
    evaluator = LLMEvaluator()
    
    # Load test cases but only use a subset for quick testing
    evaluator.load_test_cases(start_index=13)
    # Only test cases 13, 15, and 17 (multi-step purchase, conditional return, multi-product)
    selected_indices = [0, 2, 4]  # Indices 0, 2, 4 correspond to test cases 13, 15, 17
    evaluator.test_cases = [evaluator.test_cases[i] for i in selected_indices if i < len(evaluator.test_cases)]
    
    print(f"Quick evaluation: Testing {len(evaluator.test_cases)} scenarios")
    print("Selected test cases:")
    for i, test in enumerate(evaluator.test_cases):
        print(f"  - {test.description}")
    print()
    
    # Check if OpenRouter API key is available
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_key:
        print("❌ ERROR: No OPENROUTER_API_KEY found in .env file")
        print("Please add to your .env file:")
        print("  OPENROUTER_API_KEY=your-key-here")
        return
    
    print("✓ OpenRouter API key loaded from .env")
    print("Adding models for quick evaluation...")
    
    # Test a smaller subset of models for quick results
    quick_models = [
        ('openai/gpt-4o', 'GPT-4o'),
        ('google/gemini-2.0-flash-exp:free', 'Gemini 2.0 Flash'),
        ('anthropic/claude-3.5-sonnet', 'Claude 3.5 Sonnet'),
    ]
    
    for model_path, display_name in quick_models:
        evaluator.add_model('openrouter', model_path, display_name)
        print(f"  ✓ {display_name}")
    
    print(f"\nTotal models: {len(evaluator.models_to_test)}")
    print(f"Total test cases: {len(evaluator.test_cases)}")
    print(f"Estimated tests: {len(evaluator.models_to_test) * len(evaluator.test_cases)}")
    print()
    
    # Run evaluation
    print("="*60)
    print("Starting quick evaluation...")
    print("="*60)
    
    try:
        evaluations = evaluator.run_evaluation()
        
        # Generate comparison report
        evaluator.generate_comparison_report(evaluations)
        
        print("\n" + "="*60)
        print("Quick evaluation complete!")
        print(f"Results saved to: llm_eval/results/")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()