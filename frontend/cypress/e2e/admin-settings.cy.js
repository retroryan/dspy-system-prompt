describe('Admin Settings View', () => {
  beforeEach(() => {
    cy.visit('/');
    // Navigate to Admin Settings
    cy.get('.nav-link').eq(3).click();
  });

  it('should display admin settings page with correct title', () => {
    cy.get('.admin-settings-view').should('be.visible');
    cy.get('.page-title').should('contain', 'Admin Settings');
    cy.get('.page-subtitle').should('contain', 'System configuration');
  });

  it('should display settings sidebar with navigation', () => {
    cy.get('.settings-sidebar').should('be.visible');
    cy.get('.settings-nav-item').should('have.length', 5);
    
    // Check navigation items
    cy.get('.settings-nav-item').should('contain', 'LLM Settings');
    cy.get('.settings-nav-item').should('contain', 'Agent Configuration');
    cy.get('.settings-nav-item').should('contain', 'Tool Management');
    cy.get('.settings-nav-item').should('contain', 'API Settings');
    cy.get('.settings-nav-item').should('contain', 'Health Status');
  });

  it('should show LLM configuration by default', () => {
    cy.get('.config-section').should('be.visible');
    cy.get('.section-title').should('contain', 'LLM Configuration');
    cy.get('.config-field').should('have.length.at.least', 3);
  });

  it('should switch between configuration sections', () => {
    // Click Agent Configuration
    cy.contains('.settings-nav-item', 'Agent Configuration').click();
    cy.get('.section-title').should('contain', 'Agent Settings');
    
    // Click Tool Management
    cy.contains('.settings-nav-item', 'Tool Management').click();
    cy.get('.section-title').should('contain', 'Tool Management');
    
    // Click API Settings
    cy.contains('.settings-nav-item', 'API Settings').click();
    cy.get('.section-title').should('contain', 'API Configuration');
  });

  it('should show system health status', () => {
    // Click Health Status
    cy.contains('.settings-nav-item', 'Health Status').click();
    
    cy.get('.system-health').should('be.visible');
    cy.get('.health-status').should('be.visible');
    cy.get('.status-indicator').should('be.visible');
    cy.get('.health-metrics').should('be.visible');
    cy.get('.metric-card').should('have.length', 4);
  });

  it('should handle configuration changes', () => {
    // Change a text input
    cy.get('.config-input').first().clear().type('new-value');
    cy.get('.settings-actions').should('be.visible');
    cy.get('.btn-primary').should('contain', 'Save Configuration');
    cy.get('.btn-secondary').should('contain', 'Reset Changes');
  });

  it('should handle toggle switches', () => {
    // Go to tools section
    cy.contains('.settings-nav-item', 'Tool Management').click();
    
    // Toggle a switch by clicking the slider (input is hidden)
    cy.get('.toggle-slider').first().click();
    cy.get('.settings-actions').should('be.visible');
  });

  it('should save configuration', () => {
    cy.get('.config-input').first().clear().type('test-value');
    cy.get('.btn-primary').click();
    
    // Should show alert (in real implementation, this would be mocked)
    cy.window().then((win) => {
      cy.stub(win, 'alert').as('alert');
    });
  });
});