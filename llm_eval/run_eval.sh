#!/bin/bash
# Run LLM evaluation harness

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}LLM Evaluation Harness${NC}"
echo -e "${BLUE}=================================${NC}"

# Create results directory
mkdir -p llm_eval/results

# Check if OpenRouter API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${GREEN}Warning: OPENROUTER_API_KEY not set${NC}"
    echo "To test OpenRouter models, set your API key:"
    echo "export OPENROUTER_API_KEY='your-key-here'"
    echo ""
fi

# Run the evaluation
echo -e "${GREEN}Starting evaluation...${NC}"
poetry run python llm_eval/eval_harness.py "$@"

echo -e "${GREEN}Evaluation complete! Check llm_eval/results/ for detailed results.${NC}"