# LLM Evaluation Harness

This directory contains a comprehensive evaluation harness for testing different Large Language Models (LLMs) on complex e-commerce test scenarios that require multi-step tool use.

## Overview

The evaluation harness tests how efficiently different LLMs can:
- Understand complex multi-step tasks
- Select appropriate tools from a toolkit
- Execute tools in the correct sequence
- Handle errors and retry when needed
- Complete tasks within iteration limits

## Test Cases

The harness uses test cases 13 and later from the e-commerce tool set, which are complex scenarios including:
- Multi-step purchase workflows with budget constraints
- Comparative shopping with price optimization
- Order tracking and conditional return processing
- Cart optimization with inventory awareness
- Complex return scenarios with refund verification
- Multi-product shopping scenarios
- Abandoned cart recovery with alternatives
- Order history analysis with personalization
- Bundle shopping with compatibility checks
- Customer service escalation flows

## Metrics Tracked

For each model and test case, the harness tracks:
- **Success/Failure Rate**: Whether the task was completed successfully
- **Iteration Count**: Number of agent iterations needed (efficiency metric)
- **Execution Time**: Total time to complete the task
- **Tool Accuracy**: Whether the correct tools were used
- **Tool Sequence**: Detailed log of each tool call and its results

## Models Tested

The evaluation harness tests the following models:

### Local Models (Ollama)
- **gemma3:27b** - Google's Gemma 3 27B parameter model
- **llama3.2:3b** - Meta's Llama 3.2 3B parameter model

### OpenRouter Models
The harness tests these models via OpenRouter API:

#### OpenAI Models
- **gpt-4o** - GPT-4 Optimized
- **gpt-4-turbo** - GPT-4 Turbo (latest)
- **o1-mini** - OpenAI o1 Mini reasoning model

#### Google Gemini Models
- **gemini-2.0-flash-exp:free** - Gemini 2.0 Flash (experimental)
- **gemini-2.0-flash-thinking-exp:free** - Gemini 2.5 Flash with thinking
- **gemini-pro-1.5** - Gemini Pro 1.5
- **gemini-pro** - Gemini 2.5 Pro (latest)

#### Anthropic Claude Models
- **claude-3.5-sonnet** - Claude 3.5 Sonnet
- **claude-3.5-sonnet-20241022** - Claude Sonnet 4 (latest)
- **claude-3-opus** - Claude 3 Opus
- **claude-3-opus-20240229** - Claude Opus 4 (latest)

## Usage

### Quick Test (Current Model Only)
Test with just the model configured in your `.env` file:
```bash
poetry run python llm_eval/test_current_model.py
```

### Test Single Model
Test a specific model:
```bash
# Test OpenRouter model
poetry run python llm_eval/test_single_model.py openrouter "openai/gpt-4o" "GPT-4o"

# Test Ollama model
poetry run python llm_eval/test_single_model.py ollama "llama3.2:3b" "Llama 3.2"
```

### Full Evaluation
Run evaluation across all configured models:
```bash
poetry run python llm_eval/run_full_eval.py
```

### With API Keys
To test cloud models, set the appropriate API keys:
```bash
# OpenRouter (for GPT-4, Claude, Gemini via routing)
export OPENROUTER_API_KEY='your-key-here'

# Direct OpenAI
export OPENAI_API_KEY='your-key-here'

# Direct Anthropic
export ANTHROPIC_API_KEY='your-key-here'

# Then run evaluation
poetry run python llm_eval/run_full_eval.py
```

## Output

Results are saved to `llm_eval/results/` with:
- Individual model results: `{model_name}_{timestamp}.json`
- Comparison report: `comparison_report_{timestamp}.txt`

### Report Format

The comparison report includes:
1. **Summary Table**: Overall performance metrics for each model
2. **Test Case Breakdown**: Detailed results for each test scenario
3. **Iteration Details**: Step-by-step tool usage for debugging

### Example Output
```
MODEL PERFORMANCE COMPARISON
Model                          Success    Avg Iter   Avg Time   Tool Acc  
----------------------------------------------------------------------
GPT-4o                         10/10      5.2        2.1s       95%       
Claude 3.5 Sonnet              10/10      4.8        1.9s       98%       
Gemini Pro 1.5                 9/10       6.1        2.5s       88%       
Ollama gemma3:27b              8/10       9.2        0.8s       75%       
```

## Interpreting Results

- **Lower iteration count is better** - indicates more efficient reasoning
- **Higher tool accuracy is better** - indicates correct tool selection
- **Success rate** - most important metric for reliability
- **Execution time** - varies by model size and provider latency

## Key Insights

The evaluation reveals:
1. Which models are most efficient at multi-step reasoning
2. How different models handle error recovery
3. Tool selection accuracy across different scenarios
4. Trade-offs between speed and accuracy

## Files

- `eval_harness.py` - Main evaluation framework using Pydantic models
- `test_current_model.py` - Quick test script for current model
- `run_full_eval.py` - Full evaluation across multiple models
- `run_eval.sh` - Bash wrapper for running evaluations
- `results/` - Directory containing all evaluation outputs

## Architecture

The harness uses:
- **Pydantic models** for type-safe data structures
- **DSPy** for LLM interactions
- **Trajectory tracking** for detailed execution logs
- **Tool registry** for dynamic tool management
- **Parallel test execution** where possible

## Extending

To add new models:
1. Edit `run_full_eval.py`
2. Add model with: `evaluator.add_model(provider, model_name, display_name)`
3. Ensure appropriate API keys are set

To add new test metrics:
1. Extend `TestResult` dataclass in `eval_harness.py`
2. Update `run_single_test` to capture new metrics
3. Update report generation to display new metrics