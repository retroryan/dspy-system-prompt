# Frontend Guide for DSPy Agentic Loop Demo SPA

## Overview

The DSPy Agentic Loop Demo frontend is a complete single-page application (SPA) that provides a comprehensive interface for interacting with the DSPy-powered agent system. Built with React and Vite, it offers six distinct views showcasing different aspects of the agent capabilities, from real-time conversations to system administration.

### Key Features

- **Six Integrated Views**: Chatbot, Dashboard, Demos, Admin Settings, Advanced, and About
- **Real-time Chat Interface**: Smooth, responsive messaging with auto-scrolling
- **Demo Execution System**: Run pre-configured workflows with live output streaming
- **Configuration Management**: Persistent settings for LLM, agents, tools, and API
- **System Monitoring**: Real-time metrics, health status, and activity tracking
- **Advanced Visualization**: React loop visualization and tool execution display
- **Error Boundaries**: Graceful error handling with user-friendly recovery
- **Professional UI**: Modern, clean design with consistent theming

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
   Navigate to http://localhost:3001 to see the application

### Backend API Setup

Ensure the backend is running:

```bash
# From project root
poetry run uvicorn api.main:app --host localhost --port 8000 --reload
```

### First Interaction

Once the application loads:

1. **Dashboard View** (default landing): See system metrics and recent activity
2. **Chatbot View**: Interactive AI conversations with different tool sets
3. **Demo Runner**: Execute pre-configured workflows like agriculture or e-commerce
4. **Admin Settings**: Configure system parameters and monitor health
5. **Advanced View**: Visualize the React loop and tool executions
6. **About Page**: Learn about the system architecture and capabilities

## Architecture

### Component Structure

The frontend follows a clean, modular architecture with clear separation of concerns:

```
Frontend Application
│
├── App.jsx (Main container with routing)
│
├── Components/
│   ├── layout/
│   │   ├── Layout.jsx (Main layout wrapper)
│   │   └── Sidebar.jsx (Navigation sidebar)
│   ├── ErrorBoundary.jsx (Error handling)
│   └── LoadingIndicator.jsx (Loading states)
│
├── Views/
│   ├── Dashboard/ (System overview)
│   │   ├── index.jsx
│   │   ├── MetricCard.jsx
│   │   ├── ActivityFeed.jsx
│   │   └── QuickActions.jsx
│   ├── Chatbot/ (AI conversation)
│   │   ├── index.jsx
│   │   ├── ChatContainer.jsx
│   │   ├── Message.jsx
│   │   ├── MessageInput.jsx
│   │   ├── SessionPanel.jsx
│   │   └── WelcomeScreen.jsx
│   ├── Demos/ (Workflow execution)
│   │   ├── index.jsx
│   │   ├── DemoCard.jsx
│   │   └── TerminalOutput.jsx
│   ├── AdminSettings/ (Configuration)
│   │   ├── index.jsx
│   │   ├── ConfigSection.jsx
│   │   └── SystemHealth.jsx
│   ├── Advanced/ (Visualization)
│   │   ├── index.jsx
│   │   ├── LoopVisualization.jsx
│   │   └── ToolExecutionPanel.jsx
│   └── About/ (Information)
│       └── index.jsx
│
├── Services/
│   └── api.js (Backend communication)
│
├── Utils/
│   └── configTransforms.js (Data transformations)
│
├── Hooks/
│   └── useSession.js (Session management)
│
└── Styles/
    └── global.css (Global styling)
```

### Data Flow

The application follows a unidirectional data flow pattern:

```
User Interaction → View Component → API Service → Backend
                        ↓                            ↓
                   Local State ← ← ← Response Processing
                        ↓
                   UI Update → User Sees Result
```

### API Integration

The frontend communicates with the backend through a comprehensive REST API:

```
Frontend (Port 3001)
    ↓
Vite Proxy Configuration
    ↓
Backend API (Port 8000)
    ├── Sessions
    │   ├── POST /sessions (Create session)
    │   ├── POST /sessions/{id}/query (Execute query)
    │   └── DELETE /sessions/{id} (End session)
    ├── Demos
    │   ├── POST /demos (Start demo)
    │   ├── GET /demos/{id} (Get status)
    │   └── GET /demos/{id}/output (Stream output)
    ├── Configuration
    │   ├── GET /config/{section} (Get config)
    │   └── POST /config/{section} (Update config)
    ├── System
    │   ├── GET /system/status (Health status)
    │   ├── GET /system/metrics (System metrics)
    │   └── POST /system/actions (Admin actions)
    └── Tools
        └── GET /tool-sets (Available tools)
```

### State Management

Each view manages its own state using React hooks:

**Dashboard State**
- Metrics data (queries, sessions, executions)
- Activity feed (recent demos and actions)
- Loading and error states

**Chatbot State**
- Session management via useSession hook
- Message history
- Tool set selection
- Conversation context

**Demo Runner State**
- Selected demo type
- Execution status
- Real-time output streaming
- Demo metrics

**Admin Settings State**
- Configuration sections (LLM, Agent, Tools, API)
- System health metrics
- Pending changes tracking

### Error Handling

Comprehensive error handling throughout:

1. **Error Boundaries**: React error boundaries catch and display errors gracefully
2. **API Error Handling**: All API calls wrapped with try-catch
3. **Loading States**: Clear feedback during async operations
4. **User Feedback**: Informative error messages with recovery options
5. **Retry Mechanisms**: Automatic retry for transient failures

### Performance Optimizations

- **Polling Optimization**: Smart polling intervals based on activity
- **Component Memoization**: Prevent unnecessary re-renders
- **Lazy Loading**: Views loaded on demand
- **Debounced Updates**: Prevent excessive API calls
- **Virtual Scrolling**: Efficient rendering of long lists

## Key Features by View

### Dashboard
- Real-time system metrics
- Activity feed from recent demos
- Quick action buttons for common tasks
- Auto-refresh every 30 seconds

### Chatbot
- Multiple tool set support (e-commerce, agriculture, events)
- Conversation history with context
- Welcome screen with suggested prompts
- Session management panel
- Markdown rendering for responses

### Demo Runner
- Pre-configured demo workflows
- Real-time output streaming
- Execution metrics (time, iterations, tools)
- Demo cards with descriptions
- Terminal-style output display

### Admin Settings
- Configuration management for:
  - LLM settings (provider, model, temperature)
  - Agent parameters (iterations, timeout, memory)
  - Tool toggles (weather, search, calculator)
  - API settings (endpoint, timeout, retries)
- System health monitoring
- Administrative actions (logs, restart, cache clear)

### Advanced View
- React loop visualization
- Tool execution timeline
- Memory management display
- Real-time updates during execution

### About Page
- System architecture overview
- API documentation links
- Version information
- Contact details

## Backend Architecture Improvements

The frontend connects to an enhanced backend with:

### Dependency Injection System
- Proper DI using FastAPI's Depends
- No global singletons
- Clean separation of concerns
- Located in `api/core/dependencies.py`

### Thread-Safe Demo Execution
- Concurrent demo execution support
- Proper locking mechanisms
- Real-time output capture
- Status tracking

### Configuration Persistence
- File-based configuration storage
- Validation with Pydantic models
- Hot-reload support

### Enhanced Monitoring
- System metrics with psutil
- Demo execution statistics
- Tool usage tracking
- Real-time health checks

## Development Guide

### Running in Development

```bash
# Terminal 1: Backend
cd /path/to/project
poetry run uvicorn api.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Tests (optional)
npm test
```

### Building for Production

```bash
npm run build
# Outputs to frontend/dist/
```

### Environment Variables

Create `.env` file in frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

### Adding New Features

1. **New View**: Create folder in `src/views/`
2. **New Component**: Add to appropriate folder
3. **New API Endpoint**: Update `src/services/api.js`
4. **New Utility**: Add to `src/utils/`

### Code Style

- Use functional components with hooks
- Follow existing naming conventions
- Keep components focused and small
- Use proper error handling
- Add loading states for async operations

## Testing Guide

### Test Structure

```
cypress/
├── e2e/
│   ├── navigation.cy.js      # View navigation
│   ├── chatbot.cy.js        # Chat functionality
│   ├── dashboard.cy.js      # Dashboard metrics
│   ├── demos.cy.js          # Demo execution
│   ├── admin-settings.cy.js # Configuration
│   └── integration.cy.js    # Full workflows
└── support/
    └── commands.js           # Helper commands
```

### Running Tests

#### Quick Start - Headless Testing

To run tests without opening a browser window (headless mode), perfect for CI/CD or quick validation:

```bash
# Run all tests headless
npm run test:headless

# Run specific test file headless
npm run test:headless -- --spec cypress/e2e/demos.cy.js

# Run tests in a specific browser headless
npm run test:headless -- --browser chrome
npm run test:headless -- --browser firefox
npm run test:headless -- --browser edge
```

#### Interactive Testing

For development and debugging with visual feedback:

```bash
# Open Cypress Test Runner (interactive)
npm test

# This opens a GUI where you can:
# - Select and run individual tests
# - See tests execute in real-time
# - Debug failures with DevTools
# - Time-travel through test steps
```

#### Prerequisites for Headless Tests

1. **Ensure backend is running**:
   ```bash
   # In a separate terminal
   poetry run uvicorn api.main:app --host localhost --port 8000
   ```

2. **Ensure frontend dev server is running**:
   ```bash
   # In another terminal
   npm run dev
   ```

3. **Run headless tests**:
   ```bash
   npm run test:headless
   ```

#### Common Headless Test Commands

```bash
# Run all e2e tests headless with video recording
npm run test:headless -- --config video=true

# Run tests and generate HTML report
npm run test:headless -- --reporter mochawesome

# Run tests with specific viewport
npm run test:headless -- --config viewportWidth=1280,viewportHeight=720

# Run tests in parallel (if configured)
npm run test:headless -- --parallel

# Run tests with debug output
DEBUG=cypress:* npm run test:headless
```

#### CI/CD Integration

For continuous integration environments:

```bash
# Install dependencies and run tests
npm ci
npm run test:headless -- --record --key <your-cypress-dashboard-key>

# Or as a single command
npm ci && npm run test:headless
```

## Deployment Considerations

### Production Build

1. Set production API URL in environment
2. Build frontend: `npm run build`
3. Serve static files from `dist/`
4. Configure reverse proxy for API

### Performance Monitoring

- Monitor API response times
- Track error rates
- Watch memory usage
- Monitor concurrent sessions

### Security

- Implement authentication if needed
- Use HTTPS in production
- Validate all user inputs
- Sanitize API responses

## Troubleshooting

### Common Issues

**Frontend won't start:**
- Check Node.js version (18+)
- Clear node_modules and reinstall
- Check port 3001 availability

**API connection errors:**
- Verify backend is running on port 8000
- Check proxy configuration in vite.config.js
- Look for CORS issues

**Demo execution fails:**
- Check backend logs for errors
- Verify tool sets are configured
- Ensure AgentSession parameters are correct

**Configuration not saving:**
- Check file permissions for config directory
- Verify Pydantic model validation
- Look for API errors in network tab

## Summary

The DSPy Agentic Loop Demo frontend is a comprehensive SPA that showcases the full capabilities of the DSPy-powered backend. With six integrated views, real-time updates, and professional error handling, it provides an excellent demonstration platform for the agent system.

The modular architecture, clean code organization, and robust testing ensure maintainability and reliability. The recent architectural improvements, including proper dependency injection and thread safety, make this a production-ready demonstration system.

Key achievements:
- ✅ Complete SPA with 6 views
- ✅ Real backend integration (no mocks)
- ✅ Professional error handling
- ✅ Clean architecture with DI
- ✅ Thread-safe operations
- ✅ Comprehensive testing
- ✅ Production-ready code quality