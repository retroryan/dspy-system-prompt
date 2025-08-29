describe('Error Handling', () => {
  beforeEach(() => {
    cy.visit('/')
    // Wait for initial session creation
    cy.get('.session-id', { timeout: 5000 }).should('be.visible')
  })

  it('should display error message when API fails', () => {
    // Intercept query endpoint to simulate error
    cy.intercept('POST', '/sessions/*/query', {
      statusCode: 500,
      body: { detail: 'Internal server error' }
    }).as('queryError')
    
    // Submit a query
    cy.get('.message-input').type('Test query')
    cy.get('.send-button').click()
    
    // Wait for error response
    cy.wait('@queryError')
    
    // Verify error message appears
    cy.get('.error-message').should('be.visible')
    cy.get('.error-message').should('contain', 'Internal server error')
    
    // Verify reset button is available
    cy.get('.error-message button').should('be.visible')
    cy.get('.error-message button').should('contain', 'Reset Session')
  })

  it('should recover from errors with reset', () => {
    // First cause an error
    cy.intercept('POST', '/sessions/*/query', {
      statusCode: 500,
      body: { detail: 'API Error' }
    }).as('queryError')
    
    cy.get('.message-input').type('Error query')
    cy.get('.send-button').click()
    cy.wait('@queryError')
    
    // Error should be visible
    cy.get('.error-message').should('be.visible')
    
    // Click reset
    cy.get('.error-message button').click()
    
    // Wait for new session
    cy.get('.session-id', { timeout: 5000 }).should('be.visible')
    
    // Error should be cleared
    cy.get('.error-message').should('not.exist')
    
    // Should be able to send queries again
    // Remove the error intercept
    cy.intercept('POST', '/sessions/*/query', (req) => {
      req.continue()
    })
    
    cy.get('.message-input').type('Working query')
    cy.get('.send-button').click()
    
    // Should get a response
    cy.get('.message-bubble.agent', { timeout: 15000 }).should('be.visible')
  })

  it('should handle network errors gracefully', () => {
    // Simulate network failure
    cy.intercept('POST', '/sessions/*/query', { 
      forceNetworkError: true 
    }).as('networkError')
    
    // Submit a query
    cy.get('.message-input').type('Network test')
    cy.get('.send-button').click()
    
    // Wait for network error
    cy.wait('@networkError')
    
    // Error message should appear
    cy.get('.error-message').should('be.visible')
    cy.get('.error-message').should('contain', 'Error')
    
    // Reset button should be available
    cy.get('.error-message button').should('exist')
  })

  it('should remain usable after errors', () => {
    // Cause an error on first query
    let errorCount = 0
    cy.intercept('POST', '/sessions/*/query', (req) => {
      errorCount++
      if (errorCount === 1) {
        req.reply({
          statusCode: 500,
          body: { detail: 'First query failed' }
        })
      } else {
        req.continue()
      }
    }).as('conditionalError')
    
    // First query fails
    cy.get('.message-input').type('First query')
    cy.get('.send-button').click()
    cy.wait('@conditionalError')
    
    // Error appears
    cy.get('.error-message').should('be.visible')
    
    // Clear error by clicking reset
    cy.get('.error-message button').click()
    
    // Wait for new session
    cy.wait(1000)
    
    // Second query should work
    cy.get('.message-input').type('Second query')
    cy.get('.send-button').click()
    cy.wait('@conditionalError')
    
    // Should get response
    cy.get('.message-bubble.agent', { timeout: 15000 }).should('be.visible')
    
    // No error message
    cy.get('.error-message').should('not.exist')
  })

  it('should handle session deletion errors', () => {
    // Intercept session deletion to simulate error
    cy.intercept('DELETE', '/sessions/*', {
      statusCode: 404,
      body: { detail: 'Session not found' }
    }).as('deleteError')
    
    // Try to reset session
    // First send a message to make reset button appear
    cy.get('.message-input').type('Test message')
    cy.get('.send-button').click()
    cy.get('.message-bubble.user').should('be.visible')
    
    // Click reset
    cy.get('.reset-button').click()
    
    // Despite deletion error, should create new session
    cy.get('.session-id', { timeout: 5000 }).should('be.visible')
    cy.get('.empty-state').should('be.visible')
  })
})