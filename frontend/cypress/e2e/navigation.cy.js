describe('Navigation', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should display the sidebar with all navigation items', () => {
    cy.get('.sidebar').should('be.visible');
    cy.get('.logo-text').should('contain', 'DSPy Agent');
    
    // Check all navigation items are present
    cy.get('.nav-link').should('have.length', 6);
    cy.get('.nav-link').eq(0).should('contain', 'Chatbot');
    cy.get('.nav-link').eq(1).should('contain', 'Dashboard');
    cy.get('.nav-link').eq(2).should('contain', 'Demos');
    cy.get('.nav-link').eq(3).should('contain', 'Admin Settings');
    cy.get('.nav-link').eq(4).should('contain', 'Advanced');
    cy.get('.nav-link').eq(5).should('contain', 'About');
  });

  it('should start with Chatbot view as default', () => {
    cy.get('.nav-link').eq(0).should('have.class', 'active');
    // Chatbot view doesn't have a page-title, check for welcome message instead
    cy.get('.welcome-message').should('exist');
  });

  it('should switch views when clicking navigation items', () => {
    // Click Dashboard
    cy.get('.nav-link').eq(1).click();
    cy.get('.nav-link').eq(1).should('have.class', 'active');
    cy.get('.page-title').should('contain', 'Dashboard');
    
    // Click Demos
    cy.get('.nav-link').eq(2).click();
    cy.get('.nav-link').eq(2).should('have.class', 'active');
    cy.get('.page-title').should('contain', 'Demo Runner');
    
    // Click Admin Settings
    cy.get('.nav-link').eq(3).click();
    cy.get('.nav-link').eq(3).should('have.class', 'active');
    cy.get('.page-title').should('contain', 'Admin Settings');
    
    // Click Advanced
    cy.get('.nav-link').eq(4).click();
    cy.get('.nav-link').eq(4).should('have.class', 'active');
    cy.get('.page-title').should('contain', 'Advanced Chatbot');
    
    // Click About
    cy.get('.nav-link').eq(5).click();
    cy.get('.nav-link').eq(5).should('have.class', 'active');
    cy.get('.page-title').should('contain', 'About');
    
    // Click back to Chatbot
    cy.get('.nav-link').eq(0).click();
    cy.get('.nav-link').eq(0).should('have.class', 'active');
    // Chatbot view should show welcome or chat interface
    cy.get('.chat-interface').should('exist');
  });

  it('should maintain sidebar visibility across all routes', () => {
    const views = [0, 1, 2, 3, 4, 5];
    
    views.forEach((index) => {
      cy.get('.nav-link').eq(index).click();
      cy.get('.sidebar').should('be.visible');
      cy.get('.main-content').should('be.visible');
    });
  });

  it('should show correct active state for navigation', () => {
    cy.get('.nav-link').eq(2).click();
    
    // Check that only the clicked item is active
    cy.get('.nav-link.active').should('have.length', 1);
    cy.get('.nav-link').eq(2).should('have.class', 'active');
    
    // Other items should not be active
    cy.get('.nav-link').eq(0).should('not.have.class', 'active');
    cy.get('.nav-link').eq(1).should('not.have.class', 'active');
  });
});