describe('About View', () => {
  beforeEach(() => {
    cy.visit('/');
    // Navigate to About
    cy.get('.nav-link').eq(5).click();
  });

  it('should display about page with correct title', () => {
    cy.get('.about-view').should('be.visible');
    cy.get('.page-title').should('contain', 'About DSPy Agent System');
    cy.get('.page-subtitle').should('contain', 'demonstration of agentic loop');
  });

  it('should display system information section', () => {
    cy.get('.info-section').should('be.visible');
    cy.contains('.section-title', 'System Information').should('be.visible');
    cy.get('.info-grid').should('be.visible');
    cy.get('.info-item').should('have.length', 6);
    
    // Check specific info items
    cy.get('.info-item').should('contain', 'Version');
    cy.get('.info-item').should('contain', 'Framework');
    cy.get('.info-item').should('contain', 'Runtime');
  });

  it('should display key features section', () => {
    cy.get('.features-section').should('be.visible');
    cy.contains('.section-title', 'Key Features').should('be.visible');
    cy.get('.features-grid').should('be.visible');
    cy.get('.feature-card').should('have.length', 6);
    
    // Check first feature card
    cy.get('.feature-card').first().within(() => {
      cy.get('.feature-icon').should('be.visible');
      cy.get('.feature-title').should('contain', 'Session-Based Architecture');
      cy.get('.feature-description').should('exist');
    });
  });

  it('should display resources section', () => {
    cy.get('.resources-section').should('be.visible');
    cy.contains('.section-title', 'Resources & Links').should('be.visible');
    cy.get('.resources-grid').should('be.visible');
    cy.get('.resource-card').should('have.length', 4);
    
    // Check resource cards have links
    cy.get('.resource-card').each(($card) => {
      cy.wrap($card).should('have.attr', 'href');
      cy.wrap($card).should('have.attr', 'target', '_blank');
    });
  });

  it('should display architecture overview section', () => {
    cy.get('.architecture-section').should('be.visible');
    cy.contains('.section-title', 'Architecture Overview').should('be.visible');
    cy.get('.architecture-diagram').should('be.visible');
    cy.get('.arch-component').should('have.length', 5);
    cy.get('.architecture-steps').should('be.visible');
    cy.get('.architecture-steps li').should('have.length', 6);
  });

  it('should show hover effects on feature cards', () => {
    cy.get('.feature-card').first().trigger('mouseover');
    cy.get('.feature-card').first().should('have.css', 'transform');
  });

  it('should show hover effects on resource cards', () => {
    cy.get('.resource-card').first().trigger('mouseover');
    cy.get('.resource-card').first().should('have.css', 'transform');
    
    // Check arrow exists and transitions on hover
    cy.get('.resource-card').first().find('.resource-arrow').should('exist');
  });

  it('should have proper external links', () => {
    // Check that resource cards themselves have proper attributes
    cy.get('.resource-card').first().should('have.attr', 'target', '_blank');
    cy.get('.resource-card').first().should('have.attr', 'rel', 'noopener noreferrer');
  });

  it('should display all architecture components', () => {
    const expectedComponents = [
      'Frontend (React + Vite)',
      'API Service (FastAPI)',
      'AgentSession',
      'React Loop + Tools',
      'DSPy Framework'
    ];
    
    expectedComponents.forEach((component) => {
      cy.get('.arch-component').should('contain', component);
    });
  });

  it('should display all architecture steps', () => {
    cy.get('.architecture-steps li').should('have.length', 6);
    cy.get('.architecture-steps li').first().should('contain', 'User submits query');
    cy.get('.architecture-steps li').last().should('contain', 'Results returned');
  });
});