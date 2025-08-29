describe('Tool Set Functionality', () => {
  beforeEach(() => {
    cy.visit('/')
    // Wait for initial session creation
    cy.get('.session-id', { timeout: 5000 }).should('be.visible')
  })

  it('should display tool set selector with options', () => {
    // Verify tool set selector exists
    cy.get('.tool-set-selector').should('be.visible')
    cy.get('.tool-set-dropdown').should('exist')
    
    // Verify default selection
    cy.get('.tool-set-dropdown').should('have.value', 'ecommerce')
    
    // Verify dropdown has multiple options
    cy.get('.tool-set-dropdown option').should('have.length.at.least', 3)
    
    // Verify expected tool sets are present
    cy.get('.tool-set-dropdown').select('agriculture')
    cy.get('.tool-set-dropdown').should('have.value', 'agriculture')
    
    cy.get('.tool-set-dropdown').select('events')
    cy.get('.tool-set-dropdown').should('have.value', 'events')
    
    cy.get('.tool-set-dropdown').select('ecommerce')
    cy.get('.tool-set-dropdown').should('have.value', 'ecommerce')
  })

  it('should clear conversation when switching tool sets', () => {
    // Send a message first
    cy.get('.message-input').type('Show my orders')
    cy.get('.send-button').click()
    
    // Wait for response
    cy.get('.message-bubble.agent', { timeout: 15000 }).should('be.visible')
    cy.get('.query-count').should('contain', 'Queries: 1')
    
    // Switch tool set
    cy.get('.tool-set-dropdown').select('agriculture')
    
    // Verify conversation cleared
    cy.get('.empty-state').should('be.visible')
    cy.get('.empty-state').should('contain', 'Start a conversation')
    cy.get('.message-bubble').should('not.exist')
    
    // Verify query count reset
    cy.get('.query-count').should('contain', 'Queries: 0')
  })

  it('should create new session when switching tool sets', () => {
    // Intercept session creation
    cy.intercept('POST', '/sessions').as('createSession')
    
    // Get initial session ID
    cy.get('.session-id').invoke('text').then(initialSessionId => {
      // Switch tool set
      cy.get('.tool-set-dropdown').select('agriculture')
      
      // Wait for new session creation
      cy.wait('@createSession').then((interception) => {
        expect(interception.request.body.tool_set).to.equal('agriculture')
        expect(interception.response.statusCode).to.equal(201)
      })
      
      // Verify session ID changed
      cy.get('.session-id').invoke('text').should('not.equal', initialSessionId)
    })
  })

  it('should use correct tool set for queries after switching', () => {
    // Switch to agriculture
    cy.get('.tool-set-dropdown').select('agriculture')
    
    // Wait for new session to be created
    cy.get('.session-id', { timeout: 5000 }).should('be.visible')
    cy.wait(1000) // Give session time to initialize
    
    // Send agriculture-related query
    cy.get('.message-input').type('What is the weather forecast?')
    cy.get('.send-button').click()
    
    // Wait for response
    cy.get('.message-bubble.agent', { timeout: 20000 }).should('be.visible')
    
    // Response should be agriculture-related
    cy.get('.message-bubble.agent .message-content').should('exist')
    
    // Switch to ecommerce
    cy.get('.tool-set-dropdown').select('ecommerce')
    
    // Wait for new session and conversation to clear
    cy.get('.empty-state').should('be.visible')
    cy.wait(1000) // Give session time to initialize
    
    // Send ecommerce-related query
    cy.get('.message-input').type('Show products')
    cy.get('.send-button').click()
    
    // Wait for response
    cy.get('.message-bubble.agent', { timeout: 20000 }).should('be.visible')
    
    // Response should be ecommerce-related
    cy.get('.message-bubble.agent .message-content').should('exist')
  })
  
  it('should maintain tool set selection across queries', () => {
    // Switch to agriculture
    cy.get('.tool-set-dropdown').select('agriculture')
    
    // Send first query
    cy.get('.message-input').type('Check soil conditions')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent', { timeout: 15000 }).should('be.visible')
    
    // Verify tool set still selected
    cy.get('.tool-set-dropdown').should('have.value', 'agriculture')
    
    // Send second query
    cy.get('.message-input').type('What crops to plant?')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').should('have.length', 2)
    
    // Verify tool set still selected
    cy.get('.tool-set-dropdown').should('have.value', 'agriculture')
  })
})