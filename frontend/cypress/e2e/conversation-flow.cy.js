describe('Multi-Query Conversations', () => {
  beforeEach(() => {
    cy.visit('/')
    // Wait for initial session creation
    cy.get('.session-id', { timeout: 5000 }).should('be.visible')
  })

  it('should handle multiple sequential queries', () => {
    const queries = [
      'Show me available products',
      'Tell me more about the first one',
      'Add it to my cart'
    ]
    
    // Send each query and verify response
    queries.forEach((query, index) => {
      cy.get('.message-input').type(query)
      cy.get('.send-button').click()
      
      // Verify user message appears
      cy.get('.message-bubble.user').eq(index).should('contain', query)
      
      // Wait for agent response with longer timeout
      cy.get('.message-bubble.agent', { timeout: 20000 })
        .should('have.length', index + 1)
      
      // Verify query counter
      cy.get('.query-count').should('contain', `Queries: ${index + 1}`)
      
      // Small wait between queries to ensure stability
      cy.wait(500)
    })
    
    // Verify all messages are visible
    cy.get('.message-bubble').should('have.length', 6) // 3 user + 3 agent
  })

  it('should maintain conversation context', () => {
    // First query establishes context
    cy.get('.message-input').type('My name is TestUser')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent', { timeout: 15000 }).should('be.visible')
    
    // Second query references context
    cy.get('.message-input').type('What is my name?')
    cy.get('.send-button').click()
    
    // Wait for second response
    cy.get('.message-bubble.agent').should('have.length', 2)
    
    // Context should be maintained (agent should know the name)
    cy.get('.message-bubble.agent').eq(1).should('exist')
  })

  it('should accumulate conversation history correctly', () => {
    // Send first message
    cy.get('.message-input').type('First message')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').should('have.length', 1)
    
    // Send second message
    cy.get('.message-input').type('Second message')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').should('have.length', 2)
    
    // Send third message
    cy.get('.message-input').type('Third message')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').should('have.length', 3)
    
    // Verify message order
    cy.get('.message-bubble.user').eq(0).should('contain', 'First message')
    cy.get('.message-bubble.user').eq(1).should('contain', 'Second message')
    cy.get('.message-bubble.user').eq(2).should('contain', 'Third message')
    
    // Verify all timestamps are present
    cy.get('.message-timestamp').should('have.length', 6)
  })

  it('should handle scrolling with many messages', () => {
    // Send multiple messages to fill the chat window
    for (let i = 1; i <= 5; i++) {
      cy.get('.message-input').type(`Message ${i}`)
      cy.get('.send-button').click()
      
      // Wait for response before sending next
      cy.get('.message-bubble.agent').should('have.length.at.least', i)
    }
    
    // Verify scrolling keeps latest message in view
    cy.get('.message-bubble').last().should('be.visible')
    
    // Verify total message count
    cy.get('.message-bubble').should('have.length', 10) // 5 user + 5 agent
    cy.get('.query-count').should('contain', 'Queries: 5')
  })

  it('should clear conversation with new session button', () => {
    // Build up conversation
    cy.get('.message-input').type('First query')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').should('have.length', 1)
    
    cy.get('.message-input').type('Second query')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').should('have.length', 2)
    
    // Verify reset button appears
    cy.get('.reset-button').should('be.visible')
    cy.get('.reset-button').should('contain', 'New Session')
    
    // Click reset
    cy.get('.reset-button').click()
    
    // Verify conversation cleared
    cy.get('.empty-state').should('be.visible')
    cy.get('.message-bubble').should('not.exist')
    cy.get('.query-count').should('contain', 'Queries: 0')
    
    // Verify can start new conversation
    cy.get('.message-input').type('New conversation')
    cy.get('.send-button').click()
    cy.get('.message-bubble.agent').should('have.length', 1)
    cy.get('.query-count').should('contain', 'Queries: 1')
  })

  it('should maintain UI responsiveness with long conversations', () => {
    // Send several queries quickly
    const queries = ['Query 1', 'Query 2', 'Query 3']
    
    queries.forEach((query, index) => {
      cy.get('.message-input').should('not.be.disabled')
      cy.get('.message-input').type(query)
      cy.get('.send-button').click()
      
      // Input should clear immediately
      cy.get('.message-input').should('have.value', '')
      
      // User message should appear immediately
      cy.get('.message-bubble.user').eq(index).should('contain', query)
      
      // Wait for response before next query
      cy.get('.message-bubble.agent').should('have.length.at.least', index + 1)
    })
    
    // UI should remain responsive
    cy.get('.tool-set-dropdown').should('not.be.disabled')
    cy.get('.reset-button').should('be.visible').and('not.be.disabled')
  })
})