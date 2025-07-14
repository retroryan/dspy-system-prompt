
# ==============================================================================
# DSPy ARCHITECTURE DOCUMENTATION
# ==============================================================================
# 
# This documentation explains the DSPy concepts implemented in this module.
# It's kept separate from docstrings to avoid bloating DSPy prompts.
#
# DSPY MODULE PATTERN:
# ManualAgentLoop inherits from dspy.Module to leverage DSPy's optimization
# and composition capabilities. This enables:
# - Module composition with other DSPy components
# - Automatic optimization through DSPy's training procedures
# - Consistent interface for forward() method calls
# - Integration with DSPy's caching and debugging systems
#
# STATELESS DESIGN PATTERN:
# Each forward() call receives complete context rather than maintaining state.
# Benefits:
# - Predictable behavior (no hidden state side effects)
# - Easy debugging (all inputs visible in each call)
# - Robust error recovery (can restart from any point)
# - Enables optimization through complete context visibility
#
# MODULE COMPOSITION PATTERN:
# AgentReasoner is composed as a sub-module, demonstrating:
# - Clear separation of concerns (control vs reasoning)
# - Independent optimization of reasoning logic
# - Modular testing and replacement capabilities
# - Ability to swap reasoning implementations
#
# CONTEXT COMPRESSION PATTERN:
# Uses structured summaries instead of full conversation history:
# - Prevents prompt bloat (faster inference, lower costs)
# - Focuses LLM attention on relevant decision factors
# - Maintains important state while reducing noise
# - Enables consistent reasoning across iterations
#
# EXTERNAL ORCHESTRATION PATTERN:
# Tool execution is handled by ActivityManager for:
# - Better control over execution flow and timeouts
# - Comprehensive error handling and recovery
# - Detailed metrics and logging
# - Clean separation between reasoning and execution
#
# OUTPUT TRANSFORMATION PATTERN:
# Converts DSPy reasoning outputs to actionable decisions:
# - Maps ReasoningOutput to ActionDecision types
# - Preserves reasoning traces for debugging
# - Adds execution context (iteration counts, limits)
# - Handles error scenarios gracefully
#
# STRUCTURED INPUT FORMATTING:
# Formats all context data for optimal LLM consumption:
# - JSON tool descriptions with parameter specs
# - Compressed action summaries for context efficiency
# - Consistent success/failure formatting for tool results
# - Domain-specific tool prioritization when needed
#
# ==============================================================================



# ==============================================================================
# DSPy REASONING ARCHITECTURE DOCUMENTATION
# ==============================================================================
# 
# This documentation explains the DSPy reasoning concepts implemented here.
# It's kept separate from docstrings to avoid bloating DSPy prompts.
#
# DSPY SIGNATURE PATTERN:
# AgentReasonerSignature demonstrates DSPy's signature-based LLM interface:
# - InputField/OutputField define the data contract for LLM interactions
# - Field descriptions guide LLM understanding of expected inputs/outputs
# - Structured outputs use Pydantic models for complex, validated responses
# - Signature inheritance enables composition and extension for different use cases
#
# PREDICT VS CHAINOFTHOUGHT:
# Uses dspy.Predict for direct reasoning without intermediate steps:
# - ChainOfThought adds "thinking" steps that increase token usage
# - Predict is more efficient while maintaining reasoning quality through good prompts
# - The signature's field descriptions provide sufficient guidance for reasoning
# - Structured output validation ensures quality without intermediate steps
#
# STRUCTURED OUTPUT VALIDATION:
# Post-processing validation ensures system reliability:
# - Iteration limits prevent infinite loops
# - Tool name validation ensures only available tools are called
# - Decision consistency aligns should_use_tools with actual tool_calls
# - Response completeness ensures final_response exists when terminating
#
# CONTEXT COMPRESSION:
# Intelligent compression maintains reasoning quality within context limits:
# - Tool list compression prioritizes domain-relevant tools
# - History compression preserves recent, relevant information
# - Graceful fallback to simple truncation when parsing fails
# - Balance between information completeness and efficiency
#
# MODULE COMPOSITION:
# Can be composed with other DSPy modules for complex reasoning:
# - Used as sub-module in ManualAgentLoop for decision-making
# - Independent optimization and testing capabilities
# - Clear interface for swapping reasoning implementations
# - Stateless operation for robust error recovery
#
# ==============================================================================
