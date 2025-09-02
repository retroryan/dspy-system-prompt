describe('Advanced View', () => {
  beforeEach(() => {
    cy.visit('/');
    // Navigate to Advanced
    cy.get('.nav-link').eq(4).click();
  });

  it('should display advanced page with correct title', () => {
    cy.get('.advanced-view').should('be.visible');
    cy.get('.page-title').should('contain', 'Advanced Chatbot');
    cy.get('.page-subtitle').should('contain', 'real-time loop visualization');
  });

  it('should display input form', () => {
    cy.get('.advanced-form').should('be.visible');
    cy.get('.advanced-input').should('be.visible');
    cy.get('.submit-btn').should('be.visible');
    cy.get('.submit-btn').should('contain', 'Analyze');
  });

  it('should display visualization grid', () => {
    cy.get('.visualization-grid').should('be.visible');
    cy.get('.loop-section').should('be.visible');
    cy.get('.tools-section').should('be.visible');
  });

  it('should show sample trajectory by default', () => {
    cy.get('.loop-steps').should('be.visible');
    cy.get('.loop-step').should('have.length', 3);
    
    // Check first step
    cy.get('.loop-step').first().within(() => {
      cy.get('.step-number').should('contain', '1');
      cy.get('.step-tool').should('exist');
      cy.get('.step-thought').should('exist');
    });
  });

  it('should display tool execution panel', () => {
    cy.get('.tool-execution-panel').should('be.visible');
    cy.get('.tools-grid').should('be.visible');
    cy.get('.tool-card').should('have.length', 6);
    
    // Check first tool card
    cy.get('.tool-card').first().within(() => {
      cy.get('.tool-icon').should('be.visible');
      cy.get('.tool-name').should('exist');
      cy.get('.tool-stats').should('be.visible');
    });
  });

  it('should show loop statistics', () => {
    cy.get('.loop-stats').should('be.visible');
    cy.get('.stat-item').should('have.length.at.least', 2);
    cy.contains('.stat-label', 'Iterations').should('be.visible');
    cy.contains('.stat-label', 'Total Time').should('be.visible');
  });

  it('should filter tools', () => {
    cy.get('.tool-filters').should('be.visible');
    cy.get('.filter-btn').should('have.length', 3);
    
    // Click Active filter
    cy.contains('.filter-btn', 'Active').click();
    cy.contains('.filter-btn', 'Active').should('have.class', 'active');
    
    // Click Inactive filter
    cy.contains('.filter-btn', 'Inactive').click();
    cy.contains('.filter-btn', 'Inactive').should('have.class', 'active');
  });

  it('should select loop iteration', () => {
    // Click on second iteration
    cy.get('.loop-step').eq(1).click();
    cy.get('.loop-step').eq(1).should('have.class', 'selected');
    
    // Should show iteration details (may need scrolling)
    cy.get('.iteration-details').scrollIntoView().should('exist');
    cy.get('.details-title').should('contain', 'Iteration 2 Details');
    cy.get('.detail-item').should('have.length', 5);
  });

  it('should submit new query', () => {
    const testQuery = 'What is the weather in Tokyo?';
    
    cy.get('.advanced-input').type(testQuery);
    cy.get('.submit-btn').click();
    
    // Should show processing state
    cy.get('.submit-btn').should('contain', 'Processing...');
    cy.get('.advanced-input').should('be.disabled');
    
    // Wait for processing to complete (simulated)
    cy.wait(2000);
    cy.get('.submit-btn').should('contain', 'Analyze');
  });

  it('should show hover effects on loop steps', () => {
    cy.get('.loop-step').first().trigger('mouseover');
    cy.get('.loop-step').first().should('have.css', 'transform');
  });

  it('should show hover effects on tool cards', () => {
    cy.get('.tool-card').first().trigger('mouseover');
    cy.get('.tool-card').first().should('have.css', 'transform');
  });
});