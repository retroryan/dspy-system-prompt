# Trajectory Compression Strategy - Analysis and Proposal

## Executive Summary

This document analyzes AWS Strands' conversation management approach and proposes a trajectory compression strategy for DSPy. After deep analysis, we've identified key differences in philosophy: Strands uses **reactive emergency compression** while our proposal suggests **proactive progressive compression** better suited to DSPy's trajectory-based architecture.

## Strands vs DSPy: Architectural Comparison

### AWS Strands Approach

**Core Architecture:**
- **Three-tier structure**: Session → Agent → Messages
- **Granularity**: Individual messages (user input, tool use, tool result, assistant response)
- **Default window**: 40 messages
- **Compression timing**: ONLY when exceeding window size (emergency measure)
- **Compression target**: Most RECENT tool result (searches backwards)
- **Compression type**: Binary - either full content or "too large" error message

**Key Implementation Details:**
```python
# Strands' sliding window (default 40 messages)
if len(messages) > 40:
    # Emergency measure - find MOST RECENT tool result
    last_tool_result = find_last_message_with_tool_results()  # Searches backwards
    if truncate(last_tool_result):
        return  # Avoided removing messages
    # Only if truncation fails, remove old messages
```

**Critical Insight**: Strands truncates the **newest** tool result first, not the oldest. This is counterintuitive but logical:
- Recent tool results are often larger (fresh data queries)
- It's a last resort to avoid removing messages
- Older results may already be referenced in conversation

### DSPy Current Approach

**Core Architecture:**
- **Two-tier structure**: AgentSession → ConversationHistory → Trajectories
- **Granularity**: Complete trajectories (full query/response cycles)
- **Memory management**: In-memory with LLM summarization
- **User identity**: Passed to tools via `session_user_id`

## Proposed Compression Strategy for DSPy

### Philosophy: Proactive Progressive Compression

Unlike Strands' emergency-only approach, we propose continuous compression based on trajectory age and size, maintaining conversation coherence while optimizing memory usage.

### Compression Levels

```python
class CompressionLevel:
    FULL = "full"                          # No compression (age 0-2)
    TRUNCATE_OBSERVATIONS = "truncate"     # Truncate large results (age 3-5)
    SUMMARY_ONLY = "summary"                # Keep summary only (age 6-9)
    METADATA_ONLY = "metadata"              # Minimal info (age 10+)
```

### Proposed Implementation Architecture

#### 1. Core Models

```python
class CompressedTrajectory(BaseModel):
    """Compressed version of a trajectory."""
    # Always preserved
    user_query: str
    started_at: datetime
    completed_at: Optional[datetime]
    
    # Compression metadata
    compression_level: str
    original_step_count: int
    compressed_at: datetime
    
    # Variable content based on level
    compressed_steps: Optional[List[CompressedStep]]
    summary: Optional[str]
    tools_used: List[str]
    final_answer: Optional[str]
    
    # Metrics
    total_execution_time: float
    estimated_size: int

class TrajectoryCompressor:
    """Manages compression strategies."""
    def compress(self, trajectory: Trajectory, level: str) -> CompressedTrajectory
    def should_compress(self, trajectory: Trajectory) -> bool
    def estimate_size(self, trajectory: Trajectory) -> int
```

#### 2. Integration with ConversationHistory

```python
class CompressedConversationHistory(ConversationHistory):
    def __init__(self, config, enable_compression=True):
        super().__init__(config)
        self.compressor = TrajectoryCompressor()
        # Support both Trajectory and CompressedTrajectory
        self.trajectories: List[Union[Trajectory, CompressedTrajectory]] = []
    
    def add_trajectory(self, trajectory: Trajectory):
        self.trajectories.append(trajectory)
        self._apply_progressive_compression()
        self._apply_trajectory_window()  # Parent's sliding window
    
    def _apply_progressive_compression(self):
        """Compress based on age AND size."""
        for i, traj in enumerate(self.trajectories):
            if isinstance(traj, CompressedTrajectory):
                continue
                
            age = len(self.trajectories) - i - 1
            
            # Age-based compression
            if age < 3:
                continue  # Keep recent full
            elif age < 6:
                level = CompressionLevel.TRUNCATE_OBSERVATIONS
            elif age < 10:
                level = CompressionLevel.SUMMARY_ONLY
            else:
                level = CompressionLevel.METADATA_ONLY
            
            self.trajectories[i] = self.compressor.compress(traj, level)
```

### Hybrid Compression Strategy (Combining Strands' Insights)

Taking the best of both approaches:

```python
class HybridCompressor:
    """Combines age-based and size-based compression."""
    
    def compress_smart(self, trajectories: List[Trajectory]) -> List[Union[Trajectory, CompressedTrajectory]]:
        result = []
        
        # Step 1: Find abnormally large trajectories (Strands-inspired)
        large_indices = []
        for i, traj in enumerate(trajectories):
            size = self.estimate_size(traj)
            if size > LARGE_THRESHOLD:  # e.g., 10KB
                large_indices.append((i, size))
        
        # Step 2: Compress largest first, regardless of age
        large_indices.sort(key=lambda x: x[1], reverse=True)
        compressed_large = set()
        for idx, _ in large_indices[:3]:  # Top 3 largest
            trajectories[idx] = self.compress(trajectories[idx], CompressionLevel.TRUNCATE_OBSERVATIONS)
            compressed_large.add(idx)
        
        # Step 3: Apply age-based compression to the rest
        for i, traj in enumerate(trajectories):
            if i in compressed_large:
                result.append(traj)  # Already compressed
                continue
                
            age = len(trajectories) - i - 1
            if age < 3:
                result.append(traj)  # Keep recent full
            elif age < 6:
                result.append(self.compress(traj, CompressionLevel.TRUNCATE_OBSERVATIONS))
            # ... etc
        
        return result
```

## Key Design Decisions

### 1. Trajectory vs Message Granularity

**Why Trajectories are Better for DSPy:**
- Natural conversation boundaries
- Easier to summarize (complete interactions)
- Simpler mental model
- No tool pair ordering issues

### 2. Proactive vs Reactive Compression

**Why Proactive is Better for DSPy:**
- Predictable memory usage
- Gradual context degradation
- No emergency situations
- Better for long-running sessions

### 3. Compression Triggers

**Proposed Triggers:**
1. **Age-based**: Automatic based on position in history
2. **Size-based**: Immediate for abnormally large results
3. **Memory-based**: When approaching limits
4. **Manual**: User can force compression

## Memory Impact Analysis

### Typical Trajectory Sizes

- **Simple query**: ~1-2KB (no tools)
- **Tool-heavy**: ~5-10KB (multiple tools)
- **Data-intensive**: ~20-50KB (large results)

### Compression Effectiveness

| Level | Size Reduction | Information Preserved |
|-------|---------------|----------------------|
| TRUNCATE_OBSERVATIONS | 60-80% | Query, tools, truncated results |
| SUMMARY_ONLY | 90-95% | Query summary, tools list |
| METADATA_ONLY | 98% | Basic metadata only |

### Example: 20 Trajectory Session

**Without Compression:**
- 20 trajectories × 5KB = 100KB

**With Progressive Compression:**
- 3 full (15KB) + 3 truncated (6KB) + 4 summary (2KB) + 10 metadata (1KB) = 34KB
- **66% reduction** with minimal context loss

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Create `CompressedTrajectory` model
- Implement `TrajectoryCompressor` with basic levels
- Unit tests for compression logic

### Phase 2: Integration (Week 2)
- Extend `ConversationHistory` with compression support
- Update `build_context_prompt()` to handle compressed trajectories
- Integration tests with `AgentSession`

### Phase 3: Optimization (Week 3)
- Add size-based emergency compression
- Implement compression metrics and monitoring
- Performance testing with large sessions

### Phase 4: Production (Week 4)
- Configuration management
- Migration tools for existing sessions
- Documentation and best practices

## Configuration Proposal

```python
class CompressionConfig:
    # Enable/disable
    enabled: bool = True
    
    # Thresholds
    age_thresholds: Dict[str, int] = {
        "truncate": 3,
        "summary": 6,
        "metadata": 10
    }
    
    # Size limits
    max_trajectory_size: int = 10000  # Characters
    max_observation_size: int = 500   # Per observation
    large_trajectory_threshold: int = 20000  # Emergency compression
    
    # Strategy
    compression_strategy: str = "progressive"  # or "aggressive", "size_first"
    
    # Preservation
    preserve_recent: int = 3  # Never compress most recent N
    preserve_first: int = 1   # Keep first interaction for context
```

## Comparison with Strands

| Aspect | Strands | DSPy Proposal |
|--------|---------|---------------|
| **Philosophy** | Emergency compression | Continuous optimization |
| **Trigger** | >40 messages | Age + size based |
| **Target** | Most recent large result | Older trajectories |
| **Granularity** | Individual messages | Complete trajectories |
| **Compression** | Binary (full/truncated) | 4 progressive levels |
| **Storage** | Persistent with compression | In-memory with compression |
| **Complexity** | Higher (message ordering) | Lower (trajectory units) |

## Benefits of Proposed Approach

1. **Predictable**: Compression based on clear rules
2. **Gradual**: Progressive degradation, not sudden truncation
3. **Flexible**: Multiple compression strategies available
4. **Efficient**: 60-95% memory reduction possible
5. **Simple**: Trajectory-based is easier than message-based
6. **Transparent**: Both compressed and full trajectories handled uniformly

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Loss of important context | Preserve user queries and tool names |
| Compression overhead | Lazy compression, cache results |
| Complex debugging | Clear compression metadata and logging |
| User confusion | Document compression levels clearly |

## Future Enhancements

1. **Intelligent Compression**: Use LLM to identify important content
2. **Semantic Grouping**: Compress related trajectories together
3. **Reversible Compression**: Store diff for reconstruction
4. **Adaptive Thresholds**: Adjust based on available memory
5. **Compression Analytics**: Track effectiveness and optimize

## Conclusion

The proposed trajectory compression strategy provides a clean, efficient solution for managing conversation memory in DSPy. By taking a proactive approach (unlike Strands' reactive strategy) and leveraging trajectory-based architecture, we can achieve:

- **60-95% memory reduction**
- **Preserved conversation continuity**
- **Simple, maintainable implementation**
- **Flexible configuration for different use cases**

The key insight from analyzing Strands is that their approach is designed for emergency overflow handling in a message-based system, while DSPy benefits from a more sophisticated, proactive approach that leverages its trajectory-based architecture for cleaner compression boundaries and better context preservation.

## References

- AWS Strands: `/sdk-python/src/strands/agent/conversation_manager/sliding_window_conversation_manager.py`
- DSPy Conversation History: `/shared/conversation_history.py`
- DSPy Session Management: `/agentic_loop/session.py`