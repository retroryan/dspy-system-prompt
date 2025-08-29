describe('Application Launch', () => {
  it('should load the application successfully', () => {
    // Visit the application
    cy.visit('/')
    
    // Verify the main elements are present
    cy.get('.app').should('be.visible')
    cy.get('.app-header').should('be.visible')
    cy.contains('h1', 'DSPy Agentic Loop Demo').should('be.visible')
    
    // Verify chat interface appears
    cy.get('.chat-window').should('be.visible')
    cy.get('.empty-state').should('contain', 'Start a conversation')
    
    // Verify input elements are ready
    cy.get('.message-input').should('be.visible').and('not.be.disabled')
    cy.get('.send-button').should('be.visible')
    
    // Verify tool set selector is present
    cy.get('.tool-set-selector').should('be.visible')
    cy.get('.tool-set-dropdown').should('exist')
    
    // Verify session info displays
    cy.get('.session-info').should('be.visible')
    cy.get('.user-id').should('contain', 'User:')
    cy.get('.query-count').should('contain', 'Queries: 0')
    
    // Verify no console errors
    cy.window().then((win) => {
      const consoleError = cy.spy(win.console, 'error')
      expect(consoleError).not.to.be.called
    })
  })
  
  it('should create a session on load', () => {
    // Intercept session creation
    cy.intercept('POST', '/sessions').as('createSession')
    
    // Visit the app
    cy.visit('/')
    
    // Wait for session creation
    cy.wait('@createSession').then((interception) => {
      expect(interception.response.statusCode).to.equal(201)
      expect(interception.response.body).to.have.property('session_id')
      expect(interception.request.body).to.have.property('tool_set')
      expect(interception.request.body).to.have.property('user_id')
    })
    
    // Verify session ID appears in UI
    cy.get('.session-id').should('be.visible')
    cy.get('.session-id').should('contain', 'Session:')
  })
})