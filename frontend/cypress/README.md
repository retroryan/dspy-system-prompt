# Cypress Tests for DSPy Demo Frontend

## Overview
This directory contains minimal Cypress tests for the DSPy demo frontend. These tests ensure the demo works reliably for presentations without the complexity of production-level testing.

## Quick Start

### Prerequisites
- Node.js 18+
- Frontend dev server running: `npm run dev`
- Backend API running: `poetry run python api/main.py`

### Running Tests

**Interactive Mode (with GUI):**
```bash
npm test
```

**Headless Mode (no GUI):**
```bash
npm run test:headless
```

**Run specific test file:**
```bash
npm run test:headless -- --spec cypress/e2e/app-launch.cy.js
```

## Test Files

### 1. `app-launch.cy.js`
Tests the initial application load and session creation.
- Verifies all UI elements appear correctly
- Confirms session is created automatically
- Checks for console errors

### 2. `query-interaction.cy.js`
Tests the core query-response functionality.
- Query submission and response display
- Send button state management
- Enter key submission
- Message timestamps

### 3. `tool-set.cy.js`
Tests tool set switching functionality.
- Tool set dropdown population
- Switching between domains
- Session recreation on switch
- Context maintenance

### 4. `error-handling.cy.js`
Tests error recovery mechanisms.
- API error display
- Network error handling
- Recovery with reset button
- Session recreation after errors

### 5. `conversation-flow.cy.js`
Tests multi-turn conversations.
- Sequential query handling
- Context retention across queries
- Conversation history accumulation
- Session reset functionality

## Common Issues and Solutions

### Tests timing out
- Increase timeout in specific assertions: `cy.get('.element', { timeout: 20000 })`
- Ensure both frontend and backend are running
- Check network tab for failed API calls

### Session creation failures
- Verify backend is running on port 8000
- Check API health: `curl http://localhost:8000/health`
- Clear browser cache/cookies

### Intermittent failures
- Add small waits between actions: `cy.wait(500)`
- Use more specific selectors
- Ensure unique test data

## Writing New Tests

Keep tests simple and focused on demo scenarios:

```javascript
describe('Feature Name', () => {
  beforeEach(() => {
    cy.visit('/')
    cy.get('.session-id', { timeout: 5000 }).should('be.visible')
  })

  it('should do something specific', () => {
    // User action
    cy.get('.element').click()
    
    // Verification
    cy.get('.result').should('be.visible')
  })
})
```

## Best Practices

1. **Keep it simple** - Tests should be obvious in intent
2. **Test what matters** - Focus on demo-critical features
3. **Avoid complexity** - No page objects or complex abstractions
4. **Fast feedback** - Tests should run quickly
5. **Clear failures** - Make it obvious what went wrong

## Maintenance

- Update tests only when UI changes significantly
- Remove tests for features no longer demonstrated
- Keep total test runtime under 2 minutes
- Review and clean up quarterly

## Support

For issues or questions about these tests, check:
- Cypress documentation: https://docs.cypress.io
- Frontend README: ../README.md
- Main project documentation: ../../README.md