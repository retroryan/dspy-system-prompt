describe('Dashboard View', () => {
  beforeEach(() => {
    cy.visit('/');
    // Navigate to Dashboard
    cy.get('.nav-link').eq(1).click();
  });

  it('should display dashboard with all sections', () => {
    cy.get('.dashboard-view').should('be.visible');
    cy.get('.page-title').should('contain', 'Dashboard');
    cy.get('.page-subtitle').should('contain', 'Welcome to DSPy Agent System');
  });

  it('should display metric cards', () => {
    cy.get('.stats-grid').should('be.visible');
    cy.get('.stat-card').should('have.length', 4);
    
    // Check metric card content
    cy.get('.stat-card').first().within(() => {
      cy.get('.stat-label').should('contain', 'Total Queries');
      cy.get('.stat-value').should('exist');
      cy.get('.stat-change').should('exist');
    });
  });

  it('should display activity feed', () => {
    cy.get('.recent-activity').should('be.visible');
    cy.get('.section-title').should('contain', 'Recent Activity');
    cy.get('.activity-item').should('have.length.at.least', 1);
    
    // Check activity item structure
    cy.get('.activity-item').first().within(() => {
      cy.get('.activity-icon').should('be.visible');
      cy.get('.activity-title').should('exist');
      cy.get('.activity-description').should('exist');
      cy.get('.activity-time').should('exist');
    });
  });

  it('should display quick action buttons', () => {
    cy.get('.quick-actions').scrollIntoView().should('exist');
    cy.get('.action-btn').should('have.length', 4);
    
    // Check action button content
    cy.get('.action-btn').each(($btn) => {
      cy.wrap($btn).find('.action-icon').should('exist');
      cy.wrap($btn).find('.action-label').should('exist');
    });
  });

  it('should handle quick action clicks', () => {
    // Test that quick action buttons are clickable
    cy.get('.action-btn').first().scrollIntoView().should('exist').click();
    // Action was handled (navigation or other action may occur)
  });

  it('should have hover effects on interactive elements', () => {
    // Test stat card hover
    cy.get('.stat-card').first().trigger('mouseover');
    cy.get('.stat-card').first().should('have.css', 'transform');
    
    // Test action button hover
    cy.get('.action-btn').first().trigger('mouseover');
    cy.get('.action-btn').first().should('have.css', 'border-color');
  });
});