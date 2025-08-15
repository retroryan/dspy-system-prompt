#!/usr/bin/env python3
"""
Demo: Conversation History with Context-Aware Agents

This demo shows how to maintain conversation history across multiple queries
by passing context as InputFields to the existing React and Extract agents.
No wrappers, no modifications to existing agents - just clean signature usage.

The demo demonstrates:
1. Building context from conversation history
2. Passing context through signatures to agents  
3. Multiple related queries that build on each other
4. Memory management with sliding window
5. Intelligent summarization of removed trajectories
"""

import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import dspy

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared import setup_llm
from shared.conversation_history import ConversationHistory
from shared.conversation_models import ConversationHistoryConfig
from shared.trajectory_models import Trajectory, ToolStatus
from shared.tool_utils.registry import ToolRegistry
from tools.precision_agriculture.tool_set import AgricultureToolSet
from agentic_loop.react_agent import ReactAgent
from agentic_loop.extract_agent import ReactExtract

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Reduce LiteLLM verbosity
logging.getLogger('LiteLLM').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


# Define signatures with context fields
class ConversationReactSignature(dspy.Signature):
    """React agent signature with conversation context."""
    user_query = dspy.InputField(desc="The user's current question or task")
    conversation_context = dspy.InputField(
        desc="Context from previous interactions in this conversation"
    )


class ConversationExtractSignature(dspy.Signature):
    """Extract agent signature with conversation context."""
    user_query = dspy.InputField(desc="The user's current question or task")
    conversation_context = dspy.InputField(
        desc="Context from previous interactions to help synthesize a coherent answer"
    )
    answer = dspy.OutputField(desc="The final answer to the user's query")


def run_conversation_query(
    user_query: str,
    react_agent: ReactAgent,
    extract_agent: ReactExtract,
    tool_registry: ToolRegistry,
    conversation_history: ConversationHistory,
    max_iterations: int = 5
) -> Dict[str, Any]:
    """
    Process a single query with conversation context.
    
    This function demonstrates the clean integration of conversation context
    by simply passing it as a field to the existing agents.
    
    Args:
        user_query: The user's question
        react_agent: Existing ReactAgent instance
        extract_agent: Existing ReactExtract instance
        tool_registry: Registry of available tools
        conversation_history: ConversationHistory manager
        max_iterations: Max iterations for React loop
        
    Returns:
        Result dictionary with answer and trajectory
    """
    start_time = time.time()
    
    # Get conversation context
    context = conversation_history.get_context_for_agent()
    context_prompt = conversation_history.build_context_prompt(context)
    
    # Log context info
    logger.info(f"\n{'='*60}")
    logger.info(f"🗨️  Query: {user_query}")
    logger.info(f"📚 Context: {context['trajectory_count']} previous interactions")
    if context['has_summaries']:
        logger.info(f"📝 Summaries: {len(context['summaries'])} summary groups")
    
    # Show if query requires context
    context_indicators = ["that", "previous", "both", "those", "the same", "compared to", "all", "summarize"]
    needs_context = any(indicator in user_query.lower() for indicator in context_indicators)
    if needs_context and context['trajectory_count'] > 0:
        logger.info(f"🔗 Query relies on previous context")
    
    # Initialize trajectory with metadata
    trajectory = Trajectory(
        user_query=user_query,
        tool_set_name="agriculture",
        max_iterations=max_iterations,
        metadata={
            "conversation_turn": context["total_processed"] + 1,
            "has_context": context["trajectory_count"] > 0
        }
    )
    
    # Run React loop with context - just pass it as a field!
    logger.info(f"\n🤖 Starting React loop...")
    while trajectory.iteration_count < max_iterations:
        iteration_num = trajectory.iteration_count + 1
        
        # Call React agent with context as a regular field
        trajectory = react_agent(
            trajectory=trajectory,
            user_query=user_query,
            conversation_context=context_prompt  # Just another input field!
        )
        
        # Get last step
        last_step = trajectory.steps[-1]
        
        # Log thought - truncate only if very long
        thought_text = last_step.thought.content
        if len(thought_text) > 150:
            logger.info(f"  💭 Iteration {iteration_num}: {thought_text[:150]}...")
        else:
            logger.info(f"  💭 Iteration {iteration_num}: {thought_text}")
        
        # Check if finished
        if last_step.is_finish:
            logger.info(f"  ✅ Agent finished after {iteration_num} iterations")
            break
        
        # Execute tool
        if last_step.tool_invocation:
            tool_name = last_step.tool_invocation.tool_name
            tool_args = last_step.tool_invocation.tool_args
            
            logger.info(f"  🔧 Tool: {tool_name}")
            
            if tool_name in tool_registry.get_all_tools():
                try:
                    tool = tool_registry.get_tool(tool_name)
                    result = tool.execute(**tool_args)
                    
                    trajectory.add_observation(
                        tool_name=tool_name,
                        status=ToolStatus.SUCCESS,
                        result=result,
                        execution_time_ms=100  # Simplified for demo
                    )
                    
                    # Log result - truncate only if very long
                    result_str = str(result)
                    if len(result_str) > 200:
                        logger.info(f"  📊 Result: {result_str[:200]}...")
                    else:
                        logger.info(f"  📊 Result: {result_str}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Tool error: {e}")
                    trajectory.add_observation(
                        tool_name=tool_name,
                        status=ToolStatus.ERROR,
                        error=str(e),
                        execution_time_ms=0
                    )
    
    # Extract final answer with context
    logger.info(f"\n📝 Extracting final answer...")
    extract_result = extract_agent(
        trajectory=trajectory,
        user_query=user_query,
        conversation_context=context_prompt  # Context helps synthesis!
    )
    
    # Complete trajectory
    trajectory.completed_at = datetime.now()
    
    # Add to conversation history
    conversation_history.add_trajectory(trajectory)
    
    # Prepare result
    execution_time = time.time() - start_time
    
    result = {
        "answer": extract_result.answer if hasattr(extract_result, 'answer') else str(extract_result),
        "trajectory": trajectory,
        "execution_time": execution_time,
        "tools_used": trajectory.tools_used,
        "iterations": trajectory.iteration_count
    }
    
    # Log answer - truncate only if very long
    answer_text = result['answer']
    if len(answer_text) > 300:
        logger.info(f"\n✨ Answer: {answer_text[:300]}...")
    else:
        logger.info(f"\n✨ Answer: {answer_text}")
    logger.info(f"⏱️  Time: {execution_time:.2f}s")
    
    return result


def run_demo_conversation():
    """
    Run a multi-turn conversation demonstrating context awareness.
    
    This shows how conversation history enables:
    - Context-aware responses
    - Building on previous answers
    - Memory management with sliding window
    - Intelligent summarization
    """
    print("\n" + "="*80)
    print("🌾 Agricultural Advisory Conversation Demo")
    print("="*80)
    print("\nThis demo shows how conversation history enables context-aware interactions.")
    print("Notice how each query uses pronouns and references that require previous context.")
    print("Without conversation history, queries like 'that weather' or 'both cities' would fail.\n")
    
    # Setup LLM
    setup_llm()
    
    # Create tool registry
    tool_registry = ToolRegistry()
    agriculture_tools = AgricultureToolSet()
    tool_registry.register_tool_set(agriculture_tools)
    
    # Create conversation history with demo config
    history_config = ConversationHistoryConfig(
        max_trajectories=10,  # Demo value for clear illustration
        summarize_removed=True,
        preserve_first_trajectories=1,
        preserve_last_trajectories=7
    )
    conversation_history = ConversationHistory(history_config)
    
    # Initialize agents with context-aware signatures
    react_agent = ReactAgent(
        signature=ConversationReactSignature,
        tool_registry=tool_registry
    )
    
    extract_agent = ReactExtract(
        signature=ConversationExtractSignature
    )
    
    # Define conversation queries that build on each other
    # Each query intentionally relies on context from previous queries
    queries = [
        "What's the current weather in Des Moines, Iowa?",
        "Based on that weather, should I plant corn today?",  # Refers to "that weather"
        "What about the forecast for the next few days?",  # Continues from previous location
        "Compare the conditions to Omaha, Nebraska - which is better for planting?",  # Compares to previously discussed location
        "What were the historical conditions this time last year in both cities?",  # Refers to "both cities" from context
        "Summarize all the weather data you've gathered and give me a final planting recommendation.",  # Needs all previous data
    ]
    
    # Process each query
    results = []
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Turn {i}/{len(queries)}")
        print(f"{'='*80}")
        
        result = run_conversation_query(
            user_query=query,
            react_agent=react_agent,
            extract_agent=extract_agent,
            tool_registry=tool_registry,
            conversation_history=conversation_history,
            max_iterations=5
        )
        
        results.append(result)
        
        # Show conversation growth
        print(f"\n📊 Conversation Stats:")
        print(f"  - Total interactions: {conversation_history.total_trajectories_processed}")
        print(f"  - Active trajectories: {len(conversation_history.trajectories)}")
        print(f"  - Summaries created: {len(conversation_history.summaries)}")
        
        # Brief pause for readability
        time.sleep(1)
    
    # Final summary
    print(f"\n{'='*80}")
    print("📋 Final Conversation Summary")
    print(f"{'='*80}\n")
    
    print(conversation_history.get_full_history_text())
    
    print(f"\n{'='*80}")
    print("✅ Demo Complete!")
    print(f"{'='*80}")
    print(f"\nKey Advantages of Conversation History:")
    print(f"1. **Natural language references work**: 'that weather', 'both cities', 'the same'")
    print(f"2. **Contextual understanding**: Agent knows what you're referring to")
    print(f"3. **Progressive refinement**: Each query builds on previous knowledge")
    print(f"4. **No repeated questions**: Agent remembers what it already looked up")
    print(f"5. **Clean implementation**: Just InputFields, no complex wrappers")
    print(f"\nWithout conversation history, most of these queries would fail or require")
    print(f"repeating all information in every query!\n")


def run_memory_management_demo():
    """
    Demo showing sliding window memory management.
    
    This demonstrates what happens when we exceed max_trajectories
    and how the system creates intelligent summaries.
    """
    print("\n" + "="*80)
    print("💾 Memory Management Demo")
    print("="*80)
    print("\nThis demo shows sliding window memory management in action.")
    print("Watch what happens when we exceed max_trajectories=3.")
    print("Key point: Later queries reference ALL previous cities through summaries.\n")
    
    # Setup
    setup_llm()
    
    # Create tool registry
    tool_registry = ToolRegistry()
    agriculture_tools = AgricultureToolSet()
    tool_registry.register_tool_set(agriculture_tools)
    
    # Create history with small window for demo
    history_config = ConversationHistoryConfig(
        max_trajectories=3,  # Small window to trigger management
        summarize_removed=True,
        preserve_first_trajectories=1,
        preserve_last_trajectories=1
    )
    conversation_history = ConversationHistory(history_config)
    
    # Initialize agents
    react_agent = ReactAgent(
        signature=ConversationReactSignature,
        tool_registry=tool_registry
    )
    
    extract_agent = ReactExtract(
        signature=ConversationExtractSignature
    )
    
    # Run 5 queries to trigger window management
    # Each query builds on previous context to show the value of summaries
    queries = [
        "What's the current temperature in Chicago?",
        "Is it warmer in Detroit than the previous city?",  # Refers to Chicago from context
        "How does Milwaukee compare to those two?",  # Refers to both previous cities
        "Add Cleveland to the comparison - which city is warmest?",  # Triggers window, needs summary
        "Now include Indianapolis - rank all the cities by temperature.",  # Needs summary of removed trajectories
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        
        # Show pre-query state
        print(f"Before: {len(conversation_history.trajectories)} trajectories, "
              f"{len(conversation_history.summaries)} summaries")
        
        # Process query
        run_conversation_query(
            user_query=query,
            react_agent=react_agent,
            extract_agent=extract_agent,
            tool_registry=tool_registry,
            conversation_history=conversation_history,
            max_iterations=3
        )
        
        # Show post-query state
        print(f"After: {len(conversation_history.trajectories)} trajectories, "
              f"{len(conversation_history.summaries)} summaries")
        
        if conversation_history.summaries:
            summary_text = conversation_history.summaries[-1].summary_text
            print(f"Latest summary: {summary_text}")
    
    print(f"\n{'='*80}")
    print("Memory Management Results:")
    print(f"- Processed {conversation_history.total_trajectories_processed} total queries")
    print(f"- Maintaining {len(conversation_history.trajectories)} active trajectories")
    print(f"- Created {len(conversation_history.summaries)} summaries")
    print(f"- Window triggered when exceeding max_trajectories={history_config.max_trajectories}")
    
    print(f"\n{'='*80}")
    print("Key Insights:")
    print(f"{'='*80}")
    print("1. **Context preserved**: Even after window trigger, agent remembers all cities")
    print("2. **Intelligent summaries**: Extract agent creates meaningful summaries")
    print("3. **Queries rely on context**: 'previous city', 'those two', 'all cities'")
    print("4. **Scalable memory**: Can handle long conversations without unbounded growth")
    print("\nTry running without context - these queries would be impossible to answer!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Conversation History Demo")
    parser.add_argument(
        "--demo",
        choices=["conversation", "memory"],
        default="conversation",
        help="Which demo to run"
    )
    
    args = parser.parse_args()
    
    if args.demo == "conversation":
        run_demo_conversation()
    else:
        run_memory_management_demo()