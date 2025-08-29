# Cypress Testing Strategy for DSPy Demo Frontend

## Why Cypress Works Well Here

Cypress is perfect for this demo because:
1. **Real API Integration Testing**: Can test against the actual DSPy backend
2. **Session Flow Testing**: Perfect for testing session creation, queries, and resets
3. **Visual Regression**: Can verify the chat UI renders correctly
4. **Network Stubbing**: Can mock API responses for edge cases
5. **Simple Setup**: Works out-of-the-box with Vite

## How It Would Work

### Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Cypress   │────▶│   Frontend   │────▶│  DSPy API   │
│    Tests    │     │  (port 3000) │     │ (port 8000) │
└─────────────┘     └──────────────┘     └─────────────┘
       │                                          │
       └──────────── Can intercept ──────────────┘
                    and stub/spy
```

### Test Execution Flow

1. **Start Services**: Both API and frontend servers run during tests
2. **Cypress Visits**: Opens http://localhost:3000 in controlled browser
3. **Real Interactions**: Clicks buttons, types text, selects dropdowns
4. **API Verification**: Monitors actual API calls or uses stubs
5. **Assertion**: Verifies UI updates and correct responses

## Implementation Plan

### Phase 1: Cypress Setup

**Installation**:
```bash
npm install --save-dev cypress
```

**Configuration** (`cypress.config.js`):
```javascript
export default {
  e2e: {
    baseUrl: 'http://localhost:3000',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: false,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 10000, // Allow time for API responses
    requestTimeout: 10000,
    responseTimeout: 10000
  }
}
```

**Package.json Scripts**:
```json
{
  "scripts": {
    "test:e2e": "cypress open",
    "test:e2e:headless": "cypress run",
    "test:e2e:ci": "start-server-and-test dev http://localhost:3000 test:e2e:headless"
  }
}
```

### Phase 2: Core Test Structure

**Directory Structure**:
```
cypress/
├── e2e/
│   ├── session-management.cy.js    # Session creation, reset, deletion
│   ├── query-execution.cy.js       # Query flow and responses
│   ├── tool-set-switching.cy.js    # Tool set selector functionality
│   ├── error-handling.cy.js        # Error states and recovery
│   └── full-workflow.cy.js         # Complete user journeys
├── fixtures/
│   ├── ecommerce-queries.json      # Sample queries and responses
│   ├── agriculture-queries.json    # Agriculture test data
│   └── error-responses.json        # Error scenarios
└── support/
    ├── commands.js                  # Custom Cypress commands
    └── e2e.js                      # Global configuration
```

### Phase 3: Test Scenarios

#### 1. Session Management Tests
```javascript
// cypress/e2e/session-management.cy.js
describe('Session Management', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('should create session on load', () => {
    cy.intercept('POST', '/sessions').as('createSession')
    cy.wait('@createSession').then((interception) => {
      expect(interception.request.body).to.have.property('tool_set', 'ecommerce')
      expect(interception.response.body).to.have.property('session_id')
    })
    
    // Verify session ID displays in header
    cy.get('.session-id').should('contain', 'Session:')
  })

  it('should reset session when button clicked', () => {
    // Send a query first
    cy.get('.message-input').type('Show orders')
    cy.get('.send-button').click()
    cy.wait(3000) // Wait for response
    
    // Click reset
    cy.get('.reset-button').click()
    
    // Verify messages cleared
    cy.get('.empty-state').should('be.visible')
    cy.get('.query-count').should('contain', 'Queries: 0')
  })
})
```

#### 2. Query Execution Tests
```javascript
// cypress/e2e/query-execution.cy.js
describe('Query Execution', () => {
  it('should execute query and display response', () => {
    cy.visit('/')
    
    // Type and send query
    const query = 'Show me my recent orders'
    cy.get('.message-input').type(query)
    cy.get('.send-button').click()
    
    // Verify user message appears immediately
    cy.get('.message-bubble.user').should('contain', query)
    
    // Verify loading indicator
    cy.get('.loading-indicator').should('be.visible')
    
    // Wait for and verify agent response
    cy.get('.message-bubble.agent', { timeout: 10000 }).should('be.visible')
    cy.get('.loading-indicator').should('not.exist')
    
    // Verify query count increments
    cy.get('.query-count').should('contain', 'Queries: 1')
  })

  it('should handle multiple queries in sequence', () => {
    cy.visit('/')
    
    const queries = [
      'List products',
      'Show cart',
      'Process checkout'
    ]
    
    queries.forEach((query, index) => {
      cy.get('.message-input').type(query)
      cy.get('.send-button').click()
      cy.get('.message-bubble.agent').should('have.length', index + 1)
      cy.get('.query-count').should('contain', `Queries: ${index + 1}`)
    })
  })
})
```

#### 3. Tool Set Switching Tests
```javascript
// cypress/e2e/tool-set-switching.cy.js
describe('Tool Set Switching', () => {
  it('should load available tool sets', () => {
    cy.visit('/')
    cy.get('.tool-set-dropdown').click()
    cy.get('.tool-set-dropdown option').should('have.length.at.least', 3)
    cy.get('.tool-set-dropdown option').should('contain', 'Ecommerce')
    cy.get('.tool-set-dropdown option').should('contain', 'Agriculture')
  })

  it('should switch tool sets and create new session', () => {
    cy.visit('/')
    
    // Start with ecommerce
    cy.get('.tool-set-dropdown').should('have.value', 'ecommerce')
    
    // Switch to agriculture
    cy.get('.tool-set-dropdown').select('agriculture')
    
    // Verify new session created
    cy.intercept('POST', '/sessions').as('newSession')
    cy.wait('@newSession').then((interception) => {
      expect(interception.request.body.tool_set).to.equal('agriculture')
    })
    
    // Verify messages cleared
    cy.get('.empty-state').should('be.visible')
  })
})
```

#### 4. Error Handling Tests
```javascript
// cypress/e2e/error-handling.cy.js
describe('Error Handling', () => {
  it('should handle API errors gracefully', () => {
    cy.visit('/')
    
    // Stub API to return error
    cy.intercept('POST', '/sessions/*/query', {
      statusCode: 500,
      body: { detail: 'Internal server error' }
    }).as('queryError')
    
    cy.get('.message-input').type('Test query')
    cy.get('.send-button').click()
    
    cy.wait('@queryError')
    cy.get('.error-message').should('contain', 'Internal server error')
    cy.get('.error-message button').should('contain', 'Reset Session')
  })

  it('should handle network failures', () => {
    cy.visit('/')
    
    // Simulate network failure
    cy.intercept('POST', '/sessions/*/query', { forceNetworkError: true }).as('networkError')
    
    cy.get('.message-input').type('Test query')
    cy.get('.send-button').click()
    
    cy.wait('@networkError')
    cy.get('.error-message').should('be.visible')
  })
})
```

#### 5. Full Workflow Tests
```javascript
// cypress/e2e/full-workflow.cy.js
describe('Complete User Workflows', () => {
  it('should complete e-commerce shopping flow', () => {
    cy.visit('/')
    
    // Search for products
    cy.get('.message-input').type('Find laptops under $1000')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').should('contain.text', 'laptop')
    
    // Add to cart
    cy.get('.message-input').clear().type('Add the first one to my cart')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').eq(1).should('exist')
    
    // Check cart
    cy.get('.message-input').clear().type('Show my cart')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').eq(2).should('exist')
    
    // Checkout
    cy.get('.message-input').clear().type('Checkout with saved address')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').eq(3).should('exist')
    
    // Verify conversation continuity
    cy.get('.query-count').should('contain', 'Queries: 4')
  })

  it('should complete agriculture workflow', () => {
    cy.visit('/')
    cy.get('.tool-set-dropdown').select('agriculture')
    
    // Weather check
    cy.get('.message-input').type('What is the weather forecast?')
    cy.get('.send-button').click()
    cy.wait(3000)
    
    // Soil analysis
    cy.get('.message-input').clear().type('Check soil conditions for field A')
    cy.get('.send-button').click()
    cy.wait(3000)
    
    // Planting recommendation
    cy.get('.message-input').clear().type('What should I plant based on conditions?')
    cy.get('.send-button').click()
    cy.wait(3000)
    
    // Verify context maintained
    cy.get('.message-bubble.agent').should('have.length', 3)
  })
})
```

### Phase 4: Custom Commands

**Custom Cypress Commands** (`cypress/support/commands.js`):
```javascript
// Login/session commands
Cypress.Commands.add('createSession', (toolSet = 'ecommerce') => {
  cy.request('POST', 'http://localhost:8000/sessions', {
    tool_set: toolSet,
    user_id: 'cypress_test_user',
    config: {}
  }).then((response) => {
    cy.wrap(response.body.session_id).as('sessionId')
  })
})

// Query execution
Cypress.Commands.add('sendQuery', (query) => {
  cy.get('.message-input').clear().type(query)
  cy.get('.send-button').click()
  cy.get('.loading-indicator').should('be.visible')
  cy.get('.loading-indicator', { timeout: 10000 }).should('not.exist')
})

// Wait for agent response
Cypress.Commands.add('waitForResponse', (messageIndex = 0) => {
  cy.get('.message-bubble.agent').eq(messageIndex).should('be.visible')
})

// Verify message content
Cypress.Commands.add('verifyAgentMessage', (content, index = 0) => {
  cy.get('.message-bubble.agent').eq(index).should('contain', content)
})
```

### Phase 5: CI/CD Integration

**GitHub Actions Workflow** (`.github/workflows/cypress.yml`):
```yaml
name: Cypress Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  cypress:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: pip install poetry
      
      - name: Install Python dependencies
        run: poetry install
      
      - name: Start API server
        run: |
          poetry run python api/main.py &
          sleep 5
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Run Cypress tests
        working-directory: ./frontend
        run: npm run test:e2e:ci
      
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: cypress-screenshots
          path: frontend/cypress/screenshots
```

## Advanced Testing Strategies

### 1. API Response Stubbing
```javascript
// Stub specific responses for predictable testing
cy.intercept('POST', '/sessions/*/query', (req) => {
  if (req.body.query.includes('orders')) {
    req.reply({
      statusCode: 200,
      body: {
        answer: 'You have 3 recent orders',
        execution_time: 1.5,
        iterations: 2,
        tools_used: ['list_orders']
      }
    })
  }
})
```

### 2. Performance Testing
```javascript
it('should respond within acceptable time', () => {
  cy.visit('/')
  const startTime = Date.now()
  
  cy.sendQuery('Show products')
  
  cy.waitForResponse().then(() => {
    const responseTime = Date.now() - startTime
    expect(responseTime).to.be.lessThan(5000) // 5 second max
  })
})
```

### 3. Accessibility Testing
```javascript
// Install cypress-axe for accessibility testing
it('should be accessible', () => {
  cy.visit('/')
  cy.injectAxe()
  cy.checkA11y()
  
  // Check after interaction
  cy.sendQuery('Test query')
  cy.checkA11y('.message-bubble')
})
```

### 4. Visual Regression Testing
```javascript
// Using cypress-image-snapshot
it('should match visual snapshot', () => {
  cy.visit('/')
  cy.matchImageSnapshot('initial-load')
  
  cy.sendQuery('Show orders')
  cy.waitForResponse()
  cy.matchImageSnapshot('with-messages')
})
```

## Benefits of This Approach

1. **Real Integration Testing**: Tests actual API integration, not mocks
2. **User Journey Coverage**: Tests complete workflows, not just components
3. **Regression Prevention**: Catches breaking changes automatically
4. **Visual Verification**: Ensures UI renders correctly
5. **CI/CD Ready**: Runs in pipelines for every commit
6. **Developer Friendly**: Easy to write and debug tests
7. **Living Documentation**: Tests document expected behavior

## Challenges & Solutions

### Challenge 1: API Response Times
**Solution**: Use appropriate timeouts and loading assertions

### Challenge 2: Session State
**Solution**: Use beforeEach hooks to ensure clean state

### Challenge 3: Flaky Tests
**Solution**: Use explicit waits and intercepts instead of arbitrary delays

### Challenge 4: Test Data
**Solution**: Use fixtures for consistent test data

## Next Steps to Implement

1. Install Cypress: `npm install --save-dev cypress`
2. Create cypress.config.js
3. Write initial smoke test
4. Add session management tests
5. Add query execution tests
6. Set up CI/CD pipeline
7. Add to development workflow

This Cypress setup would provide comprehensive, maintainable, and reliable automated testing for the DSPy demo frontend, ensuring quality and catching regressions early.