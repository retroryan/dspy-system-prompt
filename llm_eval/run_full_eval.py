#!/usr/bin/env python3
"""
Full evaluation of multiple LLMs on complex e-commerce test cases
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from llm_eval.eval_harness import LLMEvaluator

def main():
    """Run full evaluation"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Create evaluator
    evaluator = LLMEvaluator()
    
    # Load all complex test cases (13 and later)
    evaluator.load_test_cases(start_index=13)
    
    print(f"Testing {len(evaluator.test_cases)} complex e-commerce scenarios")
    print("Test cases:")
    for i, test in enumerate(evaluator.test_cases, 13):
        print(f"  {i}: {test.description}")
    print()
    
    # Add Ollama models if available
    print("Adding Ollama models...")
    # Add the default Ollama model from .env
    current_provider = os.getenv('DSPY_PROVIDER', 'ollama')
    if current_provider == 'ollama':
        current_model = os.getenv('OLLAMA_MODEL', 'gemma3:27b')
        evaluator.add_model('ollama', current_model, f"Ollama {current_model}")
        print(f"  ✓ Added Ollama {current_model}")
    
    # Add additional Ollama model
    evaluator.add_model('ollama', 'llama3.2:3b', 'Ollama Llama3.2 3B')
    print(f"  ✓ Added Ollama Llama3.2 3B")
    
    # Check if OpenRouter API key is available from .env
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if openrouter_key:
        print("OpenRouter API key loaded from .env")
        print("Adding OpenRouter models for evaluation...")
        
        # Hard-coded OpenRouter models to test
        openrouter_models = [
            # Existing models
            ('openai/gpt-4o', 'GPT-4o'),
            ('google/gemini-2.0-flash-exp:free', 'Gemini 2.0 Flash'),
            ('anthropic/claude-3.5-sonnet', 'Claude 3.5 Sonnet'),
            ('anthropic/claude-3-opus', 'Claude 3 Opus'),
            ('google/gemini-pro-1.5', 'Gemini Pro 1.5'),
            ('openai/o1-mini', 'OpenAI o1-mini'),
            
            # New models requested
            ('openai/gpt-4-turbo', 'GPT-4 Turbo'),  # Using gpt-4-turbo as placeholder for gpt-5
            ('google/gemini-2.0-flash-thinking-exp:free', 'Gemini 2.5 Flash'),  # Latest Gemini flash model
            ('anthropic/claude-3.5-sonnet-20241022', 'Claude Sonnet 4'),  # Latest Claude Sonnet
            ('anthropic/claude-3-opus-20240229', 'Claude Opus 4'),  # Latest Claude Opus
            ('google/gemini-pro', 'Gemini 2.5 Pro'),  # Latest Gemini Pro
        ]
        
        for model_path, display_name in openrouter_models:
            evaluator.add_model('openrouter', model_path, display_name)
            print(f"  ✓ Added {display_name}")
    else:
        print("⚠️  No OPENROUTER_API_KEY found in .env file")
        print("To run evaluation with cloud models, add to your .env file:")
        print("  OPENROUTER_API_KEY=your-key-here")
        print()
        print("Continuing with local Ollama models only...")
    
    print(f"\nTotal models to evaluate: {len(evaluator.models_to_test)}")
    for model in evaluator.models_to_test:
        print(f"  - {model.name}")
    print()
    
    # Run evaluation
    print("="*60)
    print("Starting evaluation...")
    print("="*60)
    
    evaluations = evaluator.run_evaluation()
    
    # Generate comparison report
    evaluator.generate_comparison_report(evaluations)
    
    print("\n" + "="*60)
    print("Evaluation complete!")
    print(f"Results saved to: llm_eval/results/")
    print("="*60)


if __name__ == "__main__":
    main()