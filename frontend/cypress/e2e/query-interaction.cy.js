describe('Query Interaction', () => {
  beforeEach(() => {
    cy.visit('/')
    // Wait for initial session creation
    cy.get('.session-id', { timeout: 5000 }).should('be.visible')
  })

  it('should submit a query and receive a response', () => {
    const testQuery = 'Show me my recent orders'
    
    // Type query into input field
    cy.get('.message-input').type(testQuery)
    
    // Verify send button is enabled
    cy.get('.send-button').should('not.be.disabled')
    
    // Click send button
    cy.get('.send-button').click()
    
    // Verify user message appears immediately
    cy.get('.message-bubble.user').should('be.visible')
    cy.get('.message-bubble.user .message-content').should('contain', testQuery)
    
    // Wait for agent response (with longer timeout for API call)
    // Note: Loading indicator may appear and disappear too quickly to consistently test
    cy.get('.message-bubble.agent', { timeout: 15000 }).should('be.visible')
    
    // Verify loading is complete (no loading indicator)
    cy.get('.loading-indicator').should('not.exist')
    
    // Verify agent message has content
    cy.get('.message-bubble.agent .message-content').should('not.be.empty')
    
    // Verify query counter increments
    cy.get('.query-count').should('contain', 'Queries: 1')
    
    // Verify input field is cleared
    cy.get('.message-input').should('have.value', '')
  })

  it('should enable send button only with text', () => {
    // Initially button should be disabled
    cy.get('.send-button').should('be.disabled')
    
    // Type text
    cy.get('.message-input').type('Test')
    cy.get('.send-button').should('not.be.disabled')
    
    // Clear text
    cy.get('.message-input').clear()
    cy.get('.send-button').should('be.disabled')
    
    // Type spaces only
    cy.get('.message-input').type('   ')
    cy.get('.send-button').should('be.disabled')
  })

  it('should handle enter key to submit', () => {
    const testQuery = 'List available products'
    
    // Type and press enter
    cy.get('.message-input').type(testQuery)
    cy.get('.message-input').type('{enter}')
    
    // Verify message was sent
    cy.get('.message-bubble.user').should('contain', testQuery)
    
    // Wait for response to verify submission worked
    cy.get('.message-bubble.agent', { timeout: 15000 }).should('be.visible')
  })

  it('should show timestamps on messages', () => {
    // Send a message
    cy.get('.message-input').type('Test message')
    cy.get('.send-button').click()
    
    // Check user message has timestamp
    cy.get('.message-bubble.user .message-timestamp').should('be.visible')
    
    // Wait for response
    cy.get('.message-bubble.agent', { timeout: 15000 }).should('be.visible')
    
    // Check agent message has timestamp
    cy.get('.message-bubble.agent .message-timestamp').should('be.visible')
  })
})