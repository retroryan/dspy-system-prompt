// Custom Cypress commands for DSPy demo testing
// Keep these minimal and only add when truly needed

// Example: Wait for session to be ready
Cypress.Commands.add('waitForSession', () => {
  cy.get('.session-id', { timeout: 5000 }).should('be.visible')
})

// Example: Submit a query and wait for response
Cypress.Commands.add('submitQuery', (query) => {
  cy.get('.message-input').type(query)
  cy.get('.send-button').click()
  cy.get('.message-bubble.agent', { timeout: 20000 }).should('be.visible')
})