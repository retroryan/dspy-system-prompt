import React from 'react';

// Featured Real Estate queries at the top
const FEATURED_REAL_ESTATE_QUERIES = [
  {
    icon: '🏡',
    title: 'Find Your Dream Home',
    text: 'Modern family homes with pools',
    prompt: 'Find a great family home in San Francisco',
    toolSet: 'real_estate_mcp'
  },
  {
    icon: '🌆',
    title: 'Explore Neighborhoods',
    text: 'Learn about Oakland neighborhoods',
    prompt: 'Tell me about the Temescal neighborhood in Oakland - what amenities and culture does it offer?',
    toolSet: 'real_estate_mcp'
  }
];

const SUGGESTED_PROMPTS = [
  // Real Estate queries
  {
    icon: '🏠',
    text: 'Search luxury properties with views',
    prompt: 'Find luxury properties with stunning views and modern kitchens',
    toolSet: 'real_estate_mcp'
  },
  {
    icon: '🎓',
    text: 'Properties near good schools',
    prompt: 'Show me family homes near top-rated schools in San Francisco',
    toolSet: 'real_estate_mcp'
  },
  {
    icon: '🌊',
    text: 'Luxury waterfront condo in San Francisco',
    prompt: 'Luxury waterfront condo in San Francisco',
    toolSet: 'real_estate_mcp'
  },
  {
    icon: '🏘️',
    text: 'Family home in Salinas California',
    prompt: 'Family home in Salinas California',
    toolSet: 'real_estate_mcp'
  },
  {
    icon: '🍳',
    text: 'Modern kitchen in San Francisco',
    prompt: 'Modern kitchen in San Francisco',
    toolSet: 'real_estate_mcp'
  },
  // Original queries
  {
    icon: '🌤️',
    text: 'Get weather forecast and recommendations',
    prompt: 'Compare the weather between Tokyo and Paris and tell me which city has better weather for outdoor activities and explain why',
    toolSet: 'agriculture'
  },
  {
    icon: '💻',
    text: 'Search for products and compare prices',
    prompt: 'Help me find a laptop under $1000',
    toolSet: 'ecommerce'
  },
  {
    icon: '🌾',
    text: 'Get agricultural recommendations',
    prompt: 'What crops should I plant this season in Fresno, California?',
    toolSet: 'agriculture'
  },
  {
    icon: '📦',
    text: 'View order history and status',
    prompt: 'Show me all my orders and tell me which ones are delivered',
    toolSet: 'ecommerce'
  }
];

export default function WelcomeScreen({ onSuggestedPrompt, onToolSetChange, onDemoQuery }) {
  const handleFeaturedClick = async (query) => {
    // Use the new onDemoQuery handler if available
    if (onDemoQuery) {
      await onDemoQuery(query.prompt, query.toolSet);
    } else {
      // Fallback to old behavior
      if (query.toolSet && onToolSetChange) {
        await onToolSetChange(query.toolSet);
        setTimeout(() => onSuggestedPrompt(query.prompt), 100);
      } else {
        onSuggestedPrompt(query.prompt);
      }
    }
  };

  const handleSuggestedClick = async (suggestion) => {
    // Use the new onDemoQuery handler if available
    if (onDemoQuery) {
      await onDemoQuery(suggestion.prompt, suggestion.toolSet);
    } else {
      // Fallback to old behavior
      if (suggestion.toolSet && onToolSetChange) {
        await onToolSetChange(suggestion.toolSet);
        setTimeout(() => onSuggestedPrompt(suggestion.prompt), 100);
      } else {
        onSuggestedPrompt(suggestion.prompt);
      }
    }
  };

  return (
    <div className="welcome-message">
      <div className="welcome-icon">🤖</div>
      <h2 className="welcome-title">Welcome to DSPy Agent</h2>
      <p className="welcome-text">
        I'm here to help you with various tasks using my comprehensive toolkit. 
        Choose a suggestion below or type your own question to get started.
      </p>
      
      {/* Featured Real Estate Queries */}
      <div className="featured-queries">
        <h3 className="featured-title">🏡 Try Real Estate Search (MCP Tools)</h3>
        <div className="featured-cards">
          {FEATURED_REAL_ESTATE_QUERIES.map((query, index) => (
            <div
              key={index}
              className="featured-card"
              onClick={() => handleFeaturedClick(query)}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                padding: '1.5rem',
                borderRadius: '12px',
                cursor: 'pointer',
                flex: 1,
                minHeight: '120px',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                transition: 'transform 0.2s, box-shadow 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 12px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
              }}
            >
              <div style={{ fontSize: '2rem' }}>{query.icon}</div>
              <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{query.title}</div>
              <div style={{ opacity: 0.9, fontSize: '0.95rem' }}>{query.text}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="suggested-prompts">
        {SUGGESTED_PROMPTS.map((suggestion, index) => (
          <button
            key={index}
            className="prompt-card"
            onClick={() => handleSuggestedClick(suggestion)}
          >
            <div className="prompt-icon">{suggestion.icon}</div>
            <div className="prompt-text">{suggestion.text}</div>
          </button>
        ))}
      </div>
    </div>
  );
}