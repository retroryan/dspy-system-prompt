describe('Demos View', () => {
  beforeEach(() => {
    cy.visit('/');
    // Navigate to Demos
    cy.get('.nav-link').eq(2).click();
  });

  it('should display demos page with correct title', () => {
    cy.get('.demos-view').should('be.visible');
    cy.get('.page-title').should('contain', 'Demo Runner');
    cy.get('.page-subtitle').should('contain', 'pre-configured demos');
  });

  it('should display all demo cards', () => {
    cy.get('.demo-cards-grid').should('be.visible');
    cy.get('.demo-card').should('have.length', 4);
    
    // Check first demo card content
    cy.get('.demo-card').first().within(() => {
      cy.get('.demo-icon').should('contain', '🌾');
      cy.get('.demo-title').should('contain', 'Agriculture Assistant');
      cy.get('.demo-description').should('exist');
      cy.get('.demo-tag').should('have.length.at.least', 1);
      cy.get('.run-demo-btn').should('be.visible');
    });
  });

  it('should display terminal output section', () => {
    cy.get('.terminal-section').should('be.visible');
    cy.get('.terminal-output').should('be.visible');
    cy.get('.terminal-empty').should('contain', 'Select a demo to begin');
  });

  it('should run demo when clicked', () => {
    // Click first demo
    cy.get('.demo-card').first().find('.run-demo-btn').click();
    
    // Check demo is running
    cy.get('.demo-card').first().should('have.class', 'selected');
    cy.get('.running-indicator').should('be.visible');
    cy.get('.terminal-line').should('have.length.at.least', 1);
  });

  it('should clear terminal output', () => {
    // Run a demo first
    cy.get('.demo-card').first().find('.run-demo-btn').click();
    cy.wait(1000);
    
    // Clear output
    cy.get('.clear-btn').click();
    cy.get('.terminal-empty').should('be.visible');
  });

  it('should show hover effects on demo cards', () => {
    cy.get('.demo-card').first().trigger('mouseover');
    cy.get('.demo-card').first().should('have.css', 'transform');
  });
});