# Real-Time Agent Progress Streaming Proposal

## Complete Cut-Over Requirements

* **ALWAYS FIX THE CORE ISSUE!**
* **COMPLETE CHANGE**: All occurrences must be changed in a single, atomic update
* **CLEAN IMPLEMENTATION**: Simple, direct replacements only
* **NO MIGRATION PHASES**: Do not create temporary compatibility periods
* **NO PARTIAL UPDATES**: Change everything or change nothing
* **NO COMPATIBILITY LAYERS**: Do not maintain old and new paths simultaneously
* **NO BACKUPS OF OLD CODE**: Do not comment out old code "just in case"
* **NO CODE DUPLICATION**: Do not duplicate functions to handle both patterns
* **NO WRAPPER FUNCTIONS**: Direct replacements only, no abstraction layers
* **DO NOT CALL FUNCTIONS ENHANCED or IMPROVED**: Change the actual methods, not create new ones
* **ALWAYS USE PYDANTIC**
* **USE MODULES AND CLEAN CODE!**
* **Never name things after the phases or steps of the proposal**: Clean, descriptive names only
* **if hasattr should never be used**: And never use isinstance
* **Never cast variables or add variable aliases**
* **If you are using a union type something is wrong**: Evaluate the core issue
* **If it doesn't work don't hack and mock**: Fix the core issue
* **If there are questions please ask me!!!**

## Executive Summary

The current API lacks real-time progress streaming for agent execution. This proposal outlines a simple polling-based approach to provide near real-time progress updates for the demo interface, allowing users to see what the agent is thinking and doing as it processes queries.

## Current State Analysis

### What Exists Now

The API currently has:
- Sessions that maintain conversation history via AgentSession
- Query execution that returns complete results after processing
- A SessionResult object containing the full trajectory with all steps
- Each trajectory step includes thought, tool name, tool arguments, and observation

### What's Missing

The API lacks:
- A way to retrieve partial progress during query execution
- Access to intermediate steps while the agent is still processing
- Real-time visibility into the agent's thought process
- Progress indicators for long-running queries

## Proposed Solution: Polling-Based Progress Updates

### Why Polling Instead of Streaming

For a high-quality demo that avoids production complexity:
- **Simpler implementation**: No WebSocket or SSE infrastructure needed
- **Stateless**: Each request is independent
- **Compatible**: Works with existing synchronous architecture
- **Reliable**: No connection management or reconnection logic
- **Sufficient**: 500ms polling provides near real-time feel for demos

### Core Concept

Add a simple endpoint that returns the current trajectory steps for an active query. The frontend polls this endpoint while a query is processing to show progressive updates in the terminal-like display.

## Detailed Requirements

### New API Endpoint

**Endpoint**: GET /sessions/{session_id}/progress

**Purpose**: Return the current trajectory steps for the actively processing query

**Response Structure**:
- List of trajectory steps completed so far
- Each step contains: thought, tool_name, tool_args, observation, timestamp
- Flag indicating if query is still processing
- Total elapsed time

**Behavior**:
- Returns empty list if no query is active
- Returns partial trajectory while query is processing
- Returns full trajectory when query completes
- Lightweight and fast (no processing, just data retrieval)

### Session Enhancement

**Session Storage**: 
- Store trajectory steps as they occur during execution
- Make steps accessible while query is still running
- Clear steps when starting a new query
- Thread-safe access to prevent race conditions

**Progress Tracking**:
- Mark query as "in_progress" when started
- Update trajectory list as each step completes
- Mark query as "completed" when done
- Include timing information for each step

### Frontend Integration

**Polling Mechanism**:
- Start polling when query is submitted
- Poll every 500ms for smooth updates
- Stop polling when query completes
- Display each new step as it arrives

**Terminal Display**:
- Show agent thoughts in real-time
- Display tool invocations as they happen
- Show observations/results progressively
- Include timing and status indicators

## Implementation Complexity Assessment

### Low Complexity Items

1. **Progress Endpoint**: Simple GET endpoint reading existing data
2. **Trajectory Storage**: Already exists in SessionResult, just need access during execution
3. **Polling Logic**: Standard JavaScript setInterval/clearInterval
4. **Terminal Updates**: Append new lines to existing terminal component

### Moderate Complexity Items

1. **Thread Safety**: Ensuring trajectory updates are thread-safe
2. **Session State**: Managing "in_progress" state properly
3. **Error Handling**: Gracefully handling partial failures
4. **Performance**: Ensuring polling doesn't impact query execution

### Estimated Effort

**Total Implementation Time**: 8-12 hours

This is NOT complex for a demo-quality implementation. The core mechanism leverages existing data structures and simply exposes them during execution rather than only at completion.

## Implementation Plan

### Phase 1: Backend Foundation
**Goal**: Modify session to store and expose trajectory during execution

**Tasks**:
- [ ] Add progress_trajectory list to SessionInfo class
- [ ] Add is_processing flag to SessionInfo
- [ ] Modify query execution to update progress_trajectory as steps complete
- [ ] Add thread-safe access methods for reading trajectory
- [ ] Clear trajectory when starting new query
- [ ] Add timestamp to each trajectory step
- [ ] Test concurrent access patterns
- [ ] Code review and testing

### Phase 2: API Endpoint
**Goal**: Create endpoint to retrieve current progress

**Tasks**:
- [ ] Create GET /sessions/{session_id}/progress endpoint
- [ ] Define Pydantic model for progress response
- [ ] Implement endpoint to read current trajectory
- [ ] Add is_processing flag to response
- [ ] Include elapsed time calculation
- [ ] Add proper error handling for missing sessions
- [ ] Document endpoint in OpenAPI schema
- [ ] Code review and testing

### Phase 3: Core Loop Integration
**Goal**: Update agent execution to populate progress in real-time

**Tasks**:
- [ ] Modify run_react_loop to accept progress callback
- [ ] Update SessionInfo with trajectory after each step
- [ ] Ensure observations are captured immediately
- [ ] Add step timing information
- [ ] Handle errors without losing partial progress
- [ ] Test with various query types
- [ ] Verify thread safety under load
- [ ] Code review and testing

### Phase 4: Frontend Polling
**Goal**: Implement polling mechanism in React frontend

**Tasks**:
- [ ] Create useQueryProgress hook for polling
- [ ] Add progress state to chat component
- [ ] Implement 500ms polling interval
- [ ] Handle poll start/stop lifecycle
- [ ] Parse and display trajectory steps
- [ ] Add loading indicators between steps
- [ ] Handle connection errors gracefully
- [ ] Code review and testing

### Phase 5: Terminal Display
**Goal**: Create real-time terminal output component

**Tasks**:
- [ ] Create ProgressTerminal component
- [ ] Format trajectory steps as terminal output
- [ ] Add syntax highlighting for different step types
- [ ] Implement auto-scroll to bottom
- [ ] Add timestamp display for each step
- [ ] Show tool invocations clearly
- [ ] Display observations with proper formatting
- [ ] Code review and testing

### Phase 6: Integration and Polish
**Goal**: Complete integration and user experience refinement

**Tasks**:
- [ ] Integrate progress display into chat interface
- [ ] Add expand/collapse for detailed progress view
- [ ] Include progress in demo runner interface
- [ ] Add visual indicators for step status
- [ ] Test with slow queries to verify updates
- [ ] Optimize polling performance
- [ ] Add progress percentage if possible
- [ ] Code review and testing

## Benefits for Demo Quality

### User Experience
- **Transparency**: Users see exactly what the agent is thinking
- **Engagement**: Real-time updates keep users engaged during processing
- **Trust**: Visibility into reasoning builds confidence in the system
- **Education**: Demonstrates the agent's problem-solving approach

### Technical Demonstration
- **Showcases Architecture**: Highlights the React loop pattern
- **Tool Usage**: Makes tool invocations visible and understandable
- **Performance**: Shows the system is working, not frozen
- **Debugging**: Helps identify where issues occur in the chain

## Alternative Consideration: Even Simpler Approach

If the above is deemed too complex, an even simpler alternative:

**Super Simple Solution**: 
- Add a single field to QueryResponse: trajectory_steps
- Frontend displays these steps after query completes
- No polling, no real-time updates
- Still shows the thought process, just not live

This would take 2-3 hours to implement but loses the real-time aspect that makes demos engaging.

## Recommendation

Implement the polling-based solution. It provides high demo value with moderate complexity and aligns with the existing synchronous architecture. The real-time visibility into agent reasoning will significantly enhance the demo experience without requiring complex streaming infrastructure.

## Success Criteria

1. Users can see agent thoughts within 1 second of them occurring
2. Tool invocations are visible as they happen
3. No performance impact on query execution
4. Clean, terminal-like display of progress
5. Graceful handling of errors and edge cases
6. Works reliably across different query types and durations

## Conclusion

This polling-based progress system will transform the demo experience from a "black box" that returns results to a transparent system where users can watch the agent think and work. The implementation is straightforward, leveraging existing data structures and adding minimal new complexity while delivering maximum demo impact.