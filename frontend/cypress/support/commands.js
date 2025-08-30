// Custom Cypress commands for DSPy demo testing
// Keep these minimal and only add when truly needed

// Wait for session to be ready
Cypress.Commands.add('waitForSession', () => {
  // In the new UI, session is automatically created
  // Just wait for the chat interface to be ready
  cy.get('.chatbot-view', { timeout: 5000 }).should('be.visible')
})

// Submit a query and wait for response
Cypress.Commands.add('submitQuery', (query) => {
  cy.get('.chat-input').type(query)
  cy.get('.send-btn').click()
  cy.get('.message.agent', { timeout: 20000 }).should('be.visible')
})