# Sliding Window Conversation Manager for DSPy Agentic Loop

## Executive Summary

This proposal outlines how to implement a sliding window conversation manager for the DSPy agentic loop demo, inspired by AWS STRANDS but simplified for DSPy's synchronous architecture. The implementation leverages DSPy's existing capabilities while maintaining the simplicity and clarity required for a demo system.

## Core Concept

Unlike STRANDS which manages AWS Bedrock message formats, our implementation will manage DSPy's trajectory dictionary used in the React-Extract pattern. The sliding window will:

1. Maintain a maximum number of tool interactions in the trajectory
2. Preserve tool use/result pairs to maintain coherence
3. Optionally truncate large tool results before removing interactions
4. Provide clear visibility into what was trimmed

## Proposed Architecture

### 1. SlidingWindowManager Class

```python
# File: shared/sliding_window.py

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class SlidingWindowConfig:
    """Configuration for sliding window behavior."""
    max_interactions: int = 10  # Maximum tool interactions to keep
    truncate_results: bool = True  # Whether to truncate large results first
    result_max_chars: int = 500  # Max characters per tool result
    preserve_first: int = 1  # Always keep first N interactions for context

class SlidingWindowManager:
    """Manages trajectory size using a sliding window approach."""
    
    def __init__(self, config: Optional[SlidingWindowConfig] = None):
        self.config = config or SlidingWindowConfig()
        self.removed_count = 0
        self.truncated_results = set()  # Track which results were truncated
    
    def apply_window(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sliding window to trajectory, maintaining tool pairs."""
        
        # Count current interactions
        interaction_count = self._count_interactions(trajectory)
        
        if interaction_count <= self.config.max_interactions:
            return trajectory
        
        # Try truncating large results first
        if self.config.truncate_results:
            trajectory = self._truncate_large_results(trajectory)
            interaction_count = self._count_interactions(trajectory)
            
            if interaction_count <= self.config.max_interactions:
                return trajectory
        
        # Remove oldest interactions while preserving pairs
        return self._trim_interactions(trajectory)
    
    def _count_interactions(self, trajectory: Dict[str, Any]) -> int:
        """Count tool use/result pairs in trajectory."""
        count = 0
        for key in trajectory:
            if key.startswith("tool_") and "_result_" in key:
                count += 1
        return count
    
    def _truncate_large_results(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
        """Truncate large tool results to reduce context size."""
        modified = trajectory.copy()
        
        for key, value in trajectory.items():
            if "_result_" in key and isinstance(value, str):
                if len(value) > self.config.result_max_chars:
                    # Mark as truncated and replace with summary
                    result_id = key.split("_result_")[1]
                    if result_id not in self.truncated_results:
                        modified[key] = f"[TRUNCATED: Result too large ({len(value)} chars). First {self.config.result_max_chars} chars shown]\n{value[:self.config.result_max_chars]}..."
                        self.truncated_results.add(result_id)
        
        return modified
    
    def _trim_interactions(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
        """Remove oldest interactions while preserving tool pairs."""
        # Group interactions by number
        interactions = self._group_interactions(trajectory)
        
        # Determine how many to keep
        to_keep = self.config.max_interactions
        to_preserve = self.config.preserve_first
        
        # Build new trajectory
        new_trajectory = {"question": trajectory.get("question", "")}
        
        # Add preserved interactions (first N)
        for i in range(1, min(to_preserve + 1, len(interactions) + 1)):
            self._add_interaction(new_trajectory, interactions[i], i)
        
        # Add most recent interactions
        start_idx = max(len(interactions) - (to_keep - to_preserve) + 1, to_preserve + 1)
        for idx, i in enumerate(range(start_idx, len(interactions) + 1), start=to_preserve + 1):
            self._add_interaction(new_trajectory, interactions[i], idx)
        
        # Track removed count
        self.removed_count += len(interactions) - to_keep
        
        # Add summary of removed interactions
        if self.removed_count > 0:
            new_trajectory["context_note"] = f"[Note: {self.removed_count} earlier tool interactions were removed to manage context size]"
        
        return new_trajectory
    
    def _group_interactions(self, trajectory: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        """Group trajectory items by interaction number."""
        interactions = {}
        
        for key, value in trajectory.items():
            if key == "question" or key == "context_note":
                continue
                
            # Parse interaction number from key (e.g., "thought_1", "tool_1", "tool_result_1")
            parts = key.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                num = int(parts[1])
                if num not in interactions:
                    interactions[num] = {}
                interactions[num][key] = value
        
        return interactions
    
    def _add_interaction(self, trajectory: Dict[str, Any], interaction: Dict[str, Any], new_idx: int):
        """Add an interaction to trajectory with new index."""
        for key, value in interaction.items():
            # Rename key with new index
            parts = key.rsplit("_", 1)
            new_key = f"{parts[0]}_{new_idx}"
            trajectory[new_key] = value
```

### 2. Integration with React Agent Demo

```python
# File: agentic_loop/demo_react_agent.py (modification)

from shared.sliding_window import SlidingWindowManager, SlidingWindowConfig

def run_react_loop_with_external_control(
    question: str,
    tool_set: "ToolSet",
    max_iterations: int = 5,
    sliding_window_config: Optional[SlidingWindowConfig] = None,
) -> dict:
    """Execute React loop with sliding window conversation management."""
    
    # Initialize components
    react_agent = DSPyReactAgent(tool_names=tool_set.get_tool_names())
    extract_agent = DSPyExtractAgent(signature=tool_set.signature)
    sliding_window = SlidingWindowManager(sliding_window_config)
    
    # Initialize trajectory
    trajectory = {"question": question}
    
    for i in range(1, max_iterations + 1):
        # Apply sliding window before each iteration
        trajectory = sliding_window.apply_window(trajectory)
        
        # Get next action from React agent
        react_output = react_agent(trajectory=trajectory)
        
        # Add thought to trajectory
        trajectory[f"thought_{i}"] = react_output.next_thought
        
        if react_output.next_tool_name == "finish":
            break
        
        # Execute tool
        tool_result = tool_set.execute_tool(
            react_output.next_tool_name,
            react_output.next_tool_args
        )
        
        # Add to trajectory
        trajectory[f"tool_{i}"] = react_output.next_tool_name
        trajectory[f"tool_args_{i}"] = react_output.next_tool_args
        trajectory[f"tool_result_{i}"] = tool_result.result
        
        # Log window status
        if sliding_window.removed_count > 0:
            print(f"[Sliding Window: {sliding_window.removed_count} interactions removed]")
    
    # Extract final answer with managed trajectory
    final_answer = extract_agent(trajectory=trajectory)
    
    return {
        "question": question,
        "trajectory": trajectory,
        "answer": final_answer.answer,
        "window_stats": {
            "removed_interactions": sliding_window.removed_count,
            "truncated_results": len(sliding_window.truncated_results)
        }
    }
```

### 3. Configuration Examples

```python
# File: agentic_loop/window_configs.py

from shared.sliding_window import SlidingWindowConfig

# Configuration presets for different scenarios

# For simple demos - keep last 5 interactions
DEMO_CONFIG = SlidingWindowConfig(
    max_interactions=5,
    truncate_results=True,
    result_max_chars=200,
    preserve_first=1
)

# For complex reasoning - keep more context
REASONING_CONFIG = SlidingWindowConfig(
    max_interactions=15,
    truncate_results=True,
    result_max_chars=500,
    preserve_first=2
)

# For debugging - keep everything, just truncate
DEBUG_CONFIG = SlidingWindowConfig(
    max_interactions=100,
    truncate_results=True,
    result_max_chars=1000,
    preserve_first=5
)

# Minimal for token optimization
MINIMAL_CONFIG = SlidingWindowConfig(
    max_interactions=3,
    truncate_results=True,
    result_max_chars=100,
    preserve_first=0
)
```

### 4. Demo Script

```python
# File: demo_sliding_window.py

import dspy
from agentic_loop.demo_react_agent import run_react_loop_with_external_control
from agentic_loop.window_configs import DEMO_CONFIG, REASONING_CONFIG
from shared.tool_utils.agriculture_tools import AgricultureToolSet

def demo_sliding_window():
    """Demonstrate sliding window in action with a long conversation."""
    
    # Configure DSPy
    dspy.configure(lm=dspy.LM(model="gpt-4", max_tokens=1024))
    
    tool_set = AgricultureToolSet()
    
    # Complex question requiring multiple tool calls
    question = """
    I need a comprehensive agricultural report:
    1. Current weather in Iowa
    2. 7-day forecast for Iowa
    3. Historical weather patterns for the last month
    4. Current weather in Nebraska for comparison
    5. Forecast for Nebraska
    6. Analysis of which location is better for planting corn next week
    """
    
    print("Running with DEMO_CONFIG (max 5 interactions)...")
    result = run_react_loop_with_external_control(
        question=question,
        tool_set=tool_set,
        max_iterations=10,
        sliding_window_config=DEMO_CONFIG
    )
    
    print(f"\nWindow Stats: {result['window_stats']}")
    print(f"Final Answer: {result['answer']}")
    
    # Show what was kept in trajectory
    print("\nFinal Trajectory Keys:")
    for key in sorted(result['trajectory'].keys()):
        if not key.startswith('question'):
            print(f"  - {key}")

if __name__ == "__main__":
    demo_sliding_window()
```

## Key Design Decisions

### 1. Trajectory-Based Management
Unlike STRANDS which manages message arrays, we manage DSPy's trajectory dictionary. This is simpler and more aligned with DSPy's patterns.

### 2. Interaction Counting
We count "interactions" as complete tool use/result pairs, not individual trajectory entries. This ensures we never break up a tool call and its result.

### 3. Preservation Strategy
- Always preserve the original question
- Optionally preserve first N interactions for context continuity
- Keep the most recent interactions up to the limit
- Add a context note when interactions are removed

### 4. Truncation Before Removal
Like STRANDS, we try truncating large results before removing entire interactions. This preserves more conversation flow while reducing tokens.

### 5. Simple Configuration
Configuration is via a simple dataclass, making it easy to create presets for different scenarios.

## Advantages Over Complex Solutions

1. **No Async Complexity**: Pure synchronous Python, aligned with DSPy best practices
2. **No External Dependencies**: Uses only Python standard library
3. **Transparent**: The trajectory clearly shows what was removed
4. **Testable**: Simple functions that can be easily unit tested
5. **Configurable**: Easy to tune for different use cases
6. **Demo-Friendly**: Clear, understandable code perfect for demonstrations

## Testing Strategy

```python
# File: tests/test_sliding_window.py

import pytest
from shared.sliding_window import SlidingWindowManager, SlidingWindowConfig

def test_window_preserves_pairs():
    """Ensure tool use/result pairs are never separated."""
    manager = SlidingWindowManager(SlidingWindowConfig(max_interactions=2))
    
    trajectory = {
        "question": "test",
        "thought_1": "thinking",
        "tool_1": "weather",
        "tool_result_1": "sunny",
        "thought_2": "more thinking", 
        "tool_2": "forecast",
        "tool_result_2": "rainy",
        "thought_3": "final thought",
        "tool_3": "history",
        "tool_result_3": "data"
    }
    
    result = manager.apply_window(trajectory)
    
    # Should keep question, first interaction, and last interaction
    assert "tool_1" in result
    assert "tool_result_1" in result
    assert "tool_3" in result  # Renamed to tool_2
    assert "tool_result_3" in result  # Renamed to tool_result_2
    assert "tool_2" not in result  # Middle interaction removed

def test_truncation_before_removal():
    """Test that large results are truncated before removing interactions."""
    manager = SlidingWindowManager(
        SlidingWindowConfig(
            max_interactions=3,
            truncate_results=True,
            result_max_chars=10
        )
    )
    
    trajectory = {
        "question": "test",
        "tool_1": "weather",
        "tool_result_1": "x" * 100,  # Large result
        "tool_2": "forecast", 
        "tool_result_2": "small"
    }
    
    result = manager.apply_window(trajectory)
    
    # Should truncate the large result instead of removing interactions
    assert "[TRUNCATED" in result["tool_result_1"]
    assert "tool_2" in result
```

## Integration with DSPy Patterns

This sliding window manager integrates cleanly with DSPy's existing patterns:

1. **Preserves DSPy Module Structure**: React and Extract agents remain unchanged
2. **Compatible with Trajectories**: Works with the existing trajectory dictionary format
3. **Supports DSPy Debugging**: DSPY_DEBUG still shows full prompts with managed context
4. **Works with All Tool Sets**: No changes needed to existing tool implementations

## Conclusion

This sliding window implementation provides a clean, simple solution for managing conversation context in DSPy agentic loops. It's inspired by STRANDS but simplified for DSPy's architecture, maintaining the framework's emphasis on synchronous, straightforward code that's easy to understand and extend.

The implementation can be added to the existing codebase with minimal changes, providing immediate value for long-running agent interactions while maintaining full backward compatibility.