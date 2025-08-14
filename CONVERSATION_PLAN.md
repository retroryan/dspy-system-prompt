# Conversation History Implementation Plan

## Core Principles & Goals

### 🎯 Primary Goals
1. **Clean Implementation**: No backwards compatibility layers or migration paths
2. **Demo Simplicity**: Focus on demonstrating concepts, not production-grade complexity
3. **Clear Decision Points**: Ask the engineer when design choices arise - never guess
4. **Type Safety**: Leverage Pydantic models throughout for validation
5. **DSPy Alignment**: Maintain synchronous, externally-controlled architecture

### ⚠️ Critical Constraints
- **NO backwards compatibility**: This is a new feature, not an upgrade
- **NO complex workarounds**: Keep it simple and clean
- **NO production optimizations**: Focus on clarity over performance
- **NO assumptions**: When in doubt, ask for clarification
- **PRESERVE existing React/Extract implementation**: Enhance, don't replace

## Implementation Phases

### Phase 0: Pre-Implementation Review ✅ **COMPLETE**
**Goal**: Ensure understanding and alignment before coding

- [x] Review existing codebase structure
  - [x] Understand current Trajectory model in `shared/trajectory_models.py`
  - [x] Review React agent in `agentic_loop/react_agent.py`
  - [x] Review Extract agent in `agentic_loop/extract_agent.py`
  - [x] Check demo script in `agentic_loop/demo_react_agent.py`

- [x] Identify integration points
  - [x] Where trajectories are created (line 79-83 in core_loop.py)
  - [x] Where trajectories are passed to agents (line 95-98 in core_loop.py)
  - [x] Where final answers are extracted (line 205-208 in core_loop.py)
  - [x] How tool registry is used (throughout core_loop.py)

- [x] **DECISION POINT**: Confirm architecture approach with engineer
  - Should ConversationHistory be a separate class or integrated?  **✓ separate class**
  - Should we modify existing demo or create new demo file?    **✓ create new demo file**
  - How should context be passed to React agent?   **✓ Context via Signature Input Fields**

### Context Passing Implementation: Signature Input Fields ✅

Context is passed as a separate InputField in the signature, following DSPy's established patterns.
Both React and Extract agents receive context for maintaining conversation continuity.

---

### Phase 1: Core Models & Data Structures ✅ **COMPLETE**
**Goal**: Create foundational data models without breaking existing code

#### Step 1.1: Create Conversation Models ✅
- [x] Create `shared/conversation_models.py`
  - [x] Define `ConversationSummary` Pydantic model
    - trajectory_count: int
    - total_steps: int
    - tools_used: List[str]
    - summary_text: str
    - created_at: datetime
  - [x] Define `ConversationHistoryConfig` Pydantic model
    - max_trajectories: int (default: 10)
    - summarize_removed: bool (default: True)
    - preserve_first_trajectories: int (default: 1)
    - preserve_last_trajectories: int (default: 7)
  - [x] Add proper Pydantic validation and frozen configs

#### Step 1.2: Extend Trajectory Model ✅
- [x] Add optional metadata field to Trajectory model
  - Field type: `Optional[Dict[str, Any]]`
  - Default: None
  - Used for storing conversation context information

#### Step 1.3: Create Tests for Models ✅
- [x] Create `tests/test_conversation_models.py`
  - [x] Test ConversationSummary creation
  - [x] Test ConversationHistoryConfig validation
  - [x] Test edge cases (negative values, etc.)
  - [x] Test Trajectory metadata field

**Checkpoint**: Models created, tests pass, no existing code broken

---

### Phase 2: Conversation History Manager ✅ **COMPLETE**
**Goal**: Implement core conversation history management

#### Step 2.1: Create ConversationHistory Class ✅
- [x] Create `shared/conversation_history.py`
  - [x] Implement `__init__` with config
  - [x] Add trajectories list
  - [x] Add summaries list
  - [x] Initialize counters

#### Step 2.2: Implement Trajectory Management ✅
- [x] Implement `add_trajectory(trajectory: Trajectory)`
  - [x] Add to trajectories list
  - [x] Increment counter
  - [x] Call window management
  
- [x] Implement `_apply_trajectory_window()`
  - [x] Check if over max_trajectories
  - [x] Calculate what to preserve
  - [x] Create summaries if needed
  - [x] Remove excess trajectories

#### Step 2.3: Implement Summary Creation ✅
- [x] Implement `_create_summary(trajectories: List[Trajectory])`
  - [x] Extract tool usage
  - [x] Count total steps
  - [x] Use Extract agent to create intelligent summaries
  - [x] Create SummarySignature for summarization
  - [x] Pass trajectories to Extract agent for synthesis
  - [x] Include query texts and outcomes in summary

#### Step 2.4: Implement Context Methods ✅
- [x] Implement `get_context_for_agent() -> Dict`
  - [x] Return current trajectories
  - [x] Include summaries
  - [x] Add metadata
  
- [x] Implement `get_full_history_text() -> str`
  - [x] Format summaries
  - [x] Format active trajectories
  - [x] Make human-readable
  
- [x] Implement `build_context_prompt() -> str`
  - [x] Format context for agent consumption
  - [x] Include summaries and recent interactions

#### Step 2.5: Create Tests ✅
- [x] Create `tests/test_conversation_history.py`
  - [x] Test adding trajectories
  - [x] Test window management
  - [x] Test summary creation
  - [x] Test context generation
  - [x] Test edge cases

**Checkpoint**: ConversationHistory works independently, all tests pass

---

### Phase 3: Integration with Existing System ✅ **COMPLETE**
**Goal**: Connect conversation history to React/Extract agents

#### Step 3.1: Direct Signature Integration ✅
- [x] NO wrapper classes created (kept it clean)
- [x] Created context-aware signatures in demo
- [x] Leveraged existing agent flexibility

#### Step 3.2: Demo Implementation ✅
- [x] Created `demo_conversation_history.py`
  - [x] Defined ConversationReactSignature with context field
  - [x] Defined ConversationExtractSignature with context field
  - [x] Pass context as regular InputField to existing agents
  - [x] Manage ConversationHistory directly in demo
  - [x] Show multiple related queries building on each other

#### Step 3.3: Memory Management Demo ✅
- [x] Demonstrate sliding window triggering
  - [x] Show trajectory removal when exceeding max
  - [x] Display summary creation
  - [x] Track conversation statistics

#### Step 3.4: Integration Tests ✅
- [x] Create `tests/test_conversation_integration.py`
  - [x] Test React agent receives context through signature
  - [x] Test Extract agent receives context through signature
  - [x] Test end-to-end flow with context
  - [x] Test agents still work without context (optional)

**Checkpoint**: Clean integration without wrappers - context passed via signatures

---

### Phase 4: Demo Implementation ✅ **COMPLETE**
**Goal**: Create clear demonstration of conversation history

#### Step 4.1: Create Demo Script ✅
- [x] Create `demo_conversation_history.py`
  - [x] Import necessary components
  - [x] Setup logging and formatting
  - [x] Create tool registry with agriculture tools

#### Step 4.2: Implement Demo Scenarios ✅
- [x] Single conversation thread
  - [x] Create custom conversation-oriented questions
  - [x] Show context awareness between queries
  - [x] Display history stats
  
- [x] Memory management demo
  - [x] Add queries to trigger windowing at max_trajectories=3 (clearer demo)
  - [x] Show summary creation using Extract agent
  - [x] Display what was preserved/removed

#### Step 4.3: Configuration Examples ✅
- [x] Inline configurations in demo
  - [x] DEMO_CONFIG (max_trajectories=10 for conversation demo)
  - [x] MEMORY_CONFIG (max_trajectories=3 for memory management demo)
  - [x] Configurations defined directly in demo functions

#### Step 4.4: Documentation ✅
- [x] Add docstrings to all new classes
- [x] Clear inline comments for complex logic
  - Note: README update deferred as per clean implementation principle

**Checkpoint**: Demo runs successfully, shows conversation continuity ✅

---

### Phase 5: Testing & Validation
**Goal**: Ensure everything works correctly

#### Step 5.1: Unit Tests
- [ ] All model tests pass
- [ ] All manager tests pass
- [ ] All integration tests pass

#### Step 5.2: Integration Testing
- [ ] Test with agriculture tool set
- [ ] Test with ecommerce tool set
- [ ] Test with events tool set
- [ ] Verify no impact on existing demos

#### Step 5.3: Edge Case Testing
- [ ] Empty conversation
- [ ] Single trajectory
- [ ] Maximum trajectories
- [ ] Very long trajectories
- [ ] Rapid trajectory addition

#### Step 5.4: Demo Validation
- [ ] Demo runs without errors
- [ ] Output is clear and informative
- [ ] Shows conversation continuity
- [ ] Shows memory management

**Checkpoint**: All tests pass, demo is compelling

---

### Phase 6: Final Review & Cleanup
**Goal**: Ensure clean, simple implementation

#### Step 6.1: Code Review
- [ ] Remove any complex workarounds
- [ ] Ensure no backwards compatibility code
- [ ] Verify synchronous-only implementation
- [ ] Check for proper error handling

#### Step 6.2: Simplification Pass
- [ ] Remove any production optimizations
- [ ] Simplify any complex logic
- [ ] Ensure code is readable

#### Step 6.3: Documentation Review
- [ ] All new files have headers
- [ ] All public methods have docstrings
- [ ] Complex logic has comments
- [ ] README is updated

#### Step 6.4: Final Testing
- [ ] Run all tests
- [ ] Run all demos
- [ ] Verify no regression in existing functionality
- [ ] Check memory usage is reasonable

**Final Checkpoint**: Implementation complete, clean, and working

---

## Decision Points Summary (ALL RESOLVED)

All key decisions have been made by the engineer:

1. **Architecture**: ✓ Separate ConversationHistory class
2. **Trajectory Metadata**: ✓ Add metadata field to Trajectory model
3. **Summary Detail**: ✓ Use Extract agent for intelligent summaries
4. **Context Passing**: ✓ Option A - Context via Signature Input Fields
5. **Context Format**: ✓ Structured context with summaries and interactions
6. **Demo Configs**: ✓ max_trajectories=10 for main demo
7. **Test Cases**: ✓ Create custom conversation-oriented questions
8. **Extract Context**: ✓ Pass context to Extract agent for better synthesis

## Success Criteria

✅ **Implementation is successful when:**
- [ ] Conversation history maintains context across queries
- [ ] Memory is managed through sliding windows
- [ ] Summaries preserve awareness of removed content
- [ ] Integration doesn't break existing functionality
- [ ] Code is simple and understandable
- [ ] No backwards compatibility layers exist
- [ ] Demo clearly shows the benefits
- [ ] All tests pass

## Anti-Patterns to Avoid

❌ **Do NOT:**
- Add migration code or compatibility layers
- Implement production optimizations (caching, etc.)
- Create complex abstractions
- Modify core React/Extract logic
- Add async/await patterns
- Guess when design decisions arise
- Over-engineer the solution
- Add features not in the plan

## Notes for Implementation

- Start each phase only after checkpoint is complete
- Ask for clarification at each DECISION POINT
- Keep commits small and focused
- Test after each significant change
- Maintain simplicity over cleverness
- Document why, not just what
- Remember: this is a DEMO, not production code

## Questions to Ask Before Starting

Before beginning implementation, confirm:

1. Should this be a separate demo file or modify existing?
2. Is the two-level management approach (trajectories + steps) appropriate?
3. Should summaries be simple text or more structured?
4. How should context influence the React agent's reasoning?
5. What level of conversation continuity should we demonstrate?
6. Should we show tool usage patterns across conversations?
7. Is the proposed architecture aligned with project goals?

---

**Remember**: The goal is a clean, simple demonstration of conversation history management that enhances the existing DSPy agentic loop without adding unnecessary complexity. When in doubt, ask rather than assume.