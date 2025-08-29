# Simplified Frontend Implementation - Copy & Modify Approach

## Decision: COPY AND MODIFY
The existing frontend from `/Users/ryanknight/projects/temporal/durable-ai-agent/frontend` is clean and well-structured. We'll copy it and make targeted modifications rather than starting from scratch.

## What We Keep As-Is (90%)
- ✅ `ChatWindow.jsx` - Perfect scrolling chat container
- ✅ `MessageBubble.jsx` - Clean message display
- ✅ `LoadingIndicator.jsx` - Nice loading animation  
- ✅ `App.css` - Great styling, minor tweaks only
- ✅ `messageRoles.js` - Role constants we need
- ✅ `package.json` - Dependencies are minimal and correct
- ✅ `vite.config.js` - Dev server setup works great

## Core Modifications Required

### 1. Transform `useWorkflow.js` → `useSession.js`
**Remove:**
- Polling mechanism (lines 69-118)
- Workflow ID tracking
- Message completion tracking (`seenMessageIds`, `is_complete`)
- Random username generator

**Keep:**
- Basic state: messages, isLoading, error
- Message ID generation
- Error handling structure

**Add:**
- Session creation on mount
- Synchronous query execution (wait for full response)
- Tool set selection

### 2. Update `api.js`
**Change endpoints:**
```javascript
// FROM:
POST /chat
GET /workflow/{id}/conversation
POST /workflow/{id}/end-chat

// TO:
POST /sessions (create session with tool_set)
POST /sessions/{id}/query (execute query)
DELETE /sessions/{id} (end session)
GET /tool-sets (list available tools)
```

### 3. Simplify `App.jsx`
**Remove:**
- Workflow info display (lines 34-41)
- Username display (lines 31-32)
- Reset conversation button (make it "New Session")

**Add:**
- Tool set selector dropdown
- Session info (just ID and query count)

## Implementation Steps

### Phase 1: Copy & Initial Setup ✅ COMPLETED
1. ✅ Copy entire frontend directory to DSPy project
2. ✅ Update package.json name and description
3. ✅ Adjust vite.config.js proxy to DSPy API port
4. ✅ Remove unused views directory

### Phase 2: Core Hook Transformation (1 hour)
1. Rename `useWorkflow.js` to `useSession.js`
2. Remove all polling code (lines 69-118)
3. Remove workflow-specific state
4. Implement synchronous query execution:
   ```javascript
   const sendQuery = async (query) => {
     setIsLoading(true);
     const userMsg = { id: generateId(), content: query, role: 'user' };
     setMessages(prev => [...prev, userMsg]);
     
     try {
       const response = await api.executeQuery(sessionId, query);
       const agentMsg = { 
         id: generateId(), 
         content: response.answer, 
         role: 'agent',
         metadata: response.metadata 
       };
       setMessages(prev => [...prev, agentMsg]);
     } catch (error) {
       setError(error.message);
     } finally {
       setIsLoading(false);
     }
   };
   ```

### Phase 3: API Client Updates (30 minutes)
1. Update endpoints in `api.js`
2. Add session creation method
3. Add tool sets fetching
4. Remove workflow-specific methods

### Phase 4: UI Adjustments (30 minutes)
1. Simplify App.jsx header
2. Add tool set selector component
3. Update button text and labels
4. Remove workflow status display

### Phase 5: Testing & Polish (1 hour)
1. Test session creation and persistence
2. Verify query execution flow
3. Test error handling
4. Add any missing features from requirements

## Total Time: ~3.5 hours

## File-by-File Changes

### Files to Copy Unchanged
```
✅ src/components/ChatWindow.jsx
✅ src/components/MessageBubble.jsx  
✅ src/components/LoadingIndicator.jsx
✅ src/constants/messageRoles.js
✅ src/App.css
✅ src/index.css
✅ src/main.jsx
✅ public/
✅ package.json (update name only)
✅ vite.config.js (update proxy port)
✅ index.html
```

### Files to Modify
```
🔧 src/hooks/useWorkflow.js → useSession.js (major changes)
🔧 src/services/api.js (endpoint updates)
🔧 src/App.jsx (simplify UI)
```

### Files to Add
```
➕ src/components/ToolSetSelector.jsx (new dropdown component)
```

### Files to Delete
```
❌ src/views/ (not needed)
❌ src/assets/ (optional, can keep)
❌ Dockerfile (create new one later if needed)
❌ nginx.conf (create new one later if needed)
❌ README.md (write new one)
```

## Why This Approach is Better

1. **Faster Implementation**: 3.5 hours vs 2-3 weeks for full rewrite
2. **Proven UI**: The chat interface already works well
3. **Less Risk**: We know the components work together
4. **Easier Testing**: Most components don't change
5. **Maintain Quality**: The existing code is clean and well-organized

## Next Steps

1. Copy the frontend directory
2. Make the core modifications to hooks and API
3. Test with the DSPy backend
4. Add demo-specific features as needed

This approach gets us a working demo frontend in hours instead of weeks, while maintaining high quality and all the polish of the original.