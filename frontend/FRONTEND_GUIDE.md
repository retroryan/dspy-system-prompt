# Frontend Guide for DSPy Agentic Loop Demo

## Overview

The DSPy Agentic Loop Demo frontend provides a clean, intuitive chat interface for interacting with the DSPy-powered agent system. Built with React and Vite, it offers real-time conversation capabilities with different tool sets for specialized workflows like e-commerce, agriculture, and event management.

### Key Features

- **Real-time Chat Interface**: Smooth, responsive messaging with auto-scrolling
- **Tool Set Selection**: Switch between different agent capabilities on the fly
- **Session Management**: Automatic session creation and lifecycle handling  
- **Performance Metrics**: View execution time, iterations, and tools used
- **Clean User Experience**: Minimal, focused design with clear visual feedback

## Quick Start

### Prerequisites

Before getting started, ensure you have:
- Node.js version 18 or higher installed
- npm or yarn package manager available
- The DSPy backend API server running on port 8000

### Installation Steps

1. **Navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to http://localhost:3000 to see the application

### Running Tests (Quick Start)

To verify the demo works correctly:

```bash
# Run all tests with visual interface
npm test

# Or run all tests in terminal (headless)
npm run test:headless
```

Tests take about 22 seconds and verify all demo-critical functionality.

### First Interaction

Once the application loads:

1. The system automatically creates a session with the default e-commerce tool set
2. Type a query in the input field at the bottom (try "Show me laptops under $1000")
3. Press Enter or click Send to submit your query
4. Watch as the agent processes your request and returns a response
5. Continue the conversation - the agent remembers context from previous messages

### Switching Tool Sets

To change the agent's capabilities:

1. Use the dropdown menu in the header labeled "Tool Set"
2. Select from available options:
   - **E-commerce**: Product search, orders, checkout workflows
   - **Agriculture**: Weather analysis, planting decisions, farming advice
   - **Events**: Event scheduling, venue management, registration handling
3. Changing tool sets creates a new session and clears the conversation

## Architecture

### Component Structure

The frontend follows a clean, modular architecture with clear separation of concerns:

```
Frontend Application
│
├── React Components
│   ├── App.jsx (Main container)
│   ├── ChatWindow (Message display)
│   ├── MessageBubble (Individual messages)
│   ├── LoadingIndicator (Processing feedback)
│   └── ToolSetSelector (Tool set switching)
│
├── Custom Hook
│   └── useSession (Session & state management)
│
├── API Client
│   └── api.js (Backend communication)
│
└── Constants & Styles
    ├── messageRoles.js (Role definitions)
    └── App.css (Styling)
```

### Data Flow

The application follows a unidirectional data flow pattern:

```
User Input → useSession Hook → API Client → Backend
                ↓                              ↓
            Local State ← ← ← ← Response Processing
                ↓
            UI Update → User Sees Response
```

### Session Lifecycle

Sessions are the core abstraction for managing conversations:

```
Application Load
      ↓
Create Session (automatic)
      ↓
User Sends Query → Add to Messages → Send to Backend
                        ↓                    ↓
                  Show Loading ← ← ← Process Query
                        ↓                    ↓
                  Hide Loading ← ← ← Return Answer
                        ↓
                  Add Response to Messages
                        ↓
                  Ready for Next Query
```

### State Management

The application uses React hooks for state management:

- **Session State**: Managed by useSession custom hook
  - Session ID for backend correlation
  - Message history array
  - Loading and error states
  - Current tool set selection
  - Query counter

- **UI State**: Managed in App component
  - Input field value
  - Component visibility

### API Integration

The frontend communicates with the backend through a clean REST API:

```
Frontend (Port 3000)
    ↓
Vite Proxy
    ↓
Backend API (Port 8000)
    ├── POST /sessions (Create session)
    ├── POST /sessions/{id}/query (Execute query)
    ├── DELETE /sessions/{id} (End session)
    └── GET /tool-sets (List available tools)
```

### Component Responsibilities

Each component has a single, well-defined purpose:

**App.jsx**
- Main application container
- Handles form submission
- Manages input state
- Coordinates child components

**useSession Hook**
- Encapsulates all session logic
- Manages API communication
- Handles state updates
- Provides clean interface to components

**ChatWindow**
- Displays message list
- Handles auto-scrolling
- Shows empty state
- Manages loading indicator

**MessageBubble**
- Renders individual messages
- Applies role-based styling
- Displays metadata when available

**ToolSetSelector**
- Fetches available tool sets
- Handles selection changes
- Shows loading state
- Provides descriptive labels

**API Client**
- Centralizes backend communication
- Handles errors consistently
- Manages request/response transformation
- Provides typed interfaces

### Error Handling

The application implements robust error handling:

1. **Network Errors**: Caught and displayed with retry option
2. **Session Errors**: Automatic recovery with new session creation
3. **Query Timeouts**: Clear feedback with option to retry
4. **Validation Errors**: Prevented through input validation

### Performance Optimizations

The frontend includes several performance optimizations:

- **Efficient Re-renders**: Components only update when necessary
- **Auto-scroll Optimization**: Smooth scrolling without layout thrashing
- **Debounced Input**: Prevents excessive validation checks
- **Lazy Tool Set Loading**: Tool sets fetched only when needed
- **Message Deduplication**: Unique IDs prevent duplicate renders

### Styling Architecture

The application uses vanilla CSS with a component-based approach:

- **App.css**: Main application styles and layout
- **index.css**: Global resets and base styles
- **Component Classes**: BEM-style naming for clarity
- **Responsive Design**: Works on desktop and tablet screens
- **Dark Mode Ready**: CSS variables for easy theming

## Testing Guide (Advanced Options)

### Test Structure

The test suite uses Cypress for end-to-end testing of demo-critical functionality:

```
cypress/
├── e2e/
│   ├── app-launch.cy.js         # Application startup (2 tests)
│   ├── query-interaction.cy.js  # Core chat features (4 tests)
│   ├── tool-set.cy.js          # Tool set switching (5 tests)
│   ├── error-handling.cy.js    # Error recovery (5 tests)
│   └── conversation-flow.cy.js # Multi-turn chats (6 tests)
└── support/
    └── commands.js              # Custom Cypress commands
```

### Running Specific Tests

```bash
# Run a single test file
npm run test:headless -- --spec cypress/e2e/app-launch.cy.js

# Run tests matching a pattern
npm run test:headless -- --spec "cypress/e2e/*interaction*.js"

# Run with Chrome specifically
npx cypress run --browser chrome
```

### Interactive Debugging

For debugging test failures:

```bash
# Open Cypress UI
npm test

# In the Cypress interface:
# 1. Click on any test file to run it
# 2. Watch tests execute step-by-step
# 3. Use time-travel to see what happened
# 4. Inspect network requests and responses
# 5. View console output and errors
```

### Custom Commands

Available helper commands in tests:

- `cy.waitForSession()` - Waits for session to be created
- `cy.submitQuery(text)` - Types query and waits for response

### Writing New Tests

Add tests for new demo features:

```javascript
// cypress/e2e/new-feature.cy.js
describe('New Feature', () => {
  beforeEach(() => {
    cy.visit('/')
    cy.waitForSession()
  })
  
  it('should work correctly', () => {
    // Your test logic here
    cy.get('.element').should('be.visible')
  })
})
```

### Test Configuration

Modify `cypress.config.js` for custom settings:

- `baseUrl`: Frontend URL (default: http://localhost:3000)
- `defaultCommandTimeout`: How long to wait for elements (default: 10s)
- `viewportWidth/Height`: Browser dimensions for tests
- `video`: Enable/disable video recording (default: false)

### Troubleshooting Test Failures

#### Common Issues and Solutions

**Timeouts waiting for elements:**
- Increase timeout: `cy.get('.element', { timeout: 20000 })`
- Ensure backend is running: `curl http://localhost:8000/health`

**Session creation failures:**
- Check backend logs for errors
- Clear browser storage: `cy.clearLocalStorage()`

**Flaky tests (intermittent failures):**
- Add explicit waits: `cy.wait(500)`
- Use more specific selectors
- Check network tab for failed requests

**Tests pass individually but fail together:**
- Add cleanup in `afterEach` hooks
- Ensure proper test isolation
- Check for state pollution between tests

### Performance Considerations

- Keep total test runtime under 2 minutes
- Focus on critical demo paths only
- Avoid testing edge cases not shown in demos
- Use `--headless` mode for faster execution

### Continuous Testing During Development

For active development:

```bash
# Terminal 1: Backend
poetry run python api/main.py

# Terminal 2: Frontend
npm run dev

# Terminal 3: Cypress (keep open)
npm test
# Re-run specific tests as you make changes
```

### Test Maintenance

- Update tests when UI changes significantly
- Remove tests for deprecated features
- Keep test code simple and readable
- Document why each test exists

## Summary

The DSPy Agentic Loop Demo frontend provides a production-ready interface for interacting with the agent system. Its clean architecture, robust error handling, and intuitive user experience make it an excellent foundation for demonstrating the capabilities of the DSPy-powered backend. The modular design allows for easy extension and customization while maintaining simplicity and performance.

The integrated Cypress test suite ensures demo reliability with minimal overhead, providing confidence that presentations will work flawlessly while keeping the testing approach simple and maintainable.