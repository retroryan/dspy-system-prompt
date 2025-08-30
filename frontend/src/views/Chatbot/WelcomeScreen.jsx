import React from 'react';

const SUGGESTED_PROMPTS = [
  {
    icon: '🌤️',
    text: 'Get weather forecast and recommendations',
    prompt: 'Compare the weather between Tokyo and Paris and tell me which city has better weather for outdoor activities'
  },
  {
    icon: '💻',
    text: 'Search for products and compare prices',
    prompt: 'Help me find a laptop under $1000'
  },
  {
    icon: '🌾',
    text: 'Agricultural recommendations for Fresno',
    prompt: 'What crops should I plant this season in Fresno, California?'
  },
  {
    icon: '📦',
    text: 'View order history and status',
    prompt: 'Show me all my orders and tell me which ones are delivered'
  }
];

export default function WelcomeScreen({ onSuggestedPrompt }) {
  return (
    <div className="welcome-message">
      <div className="welcome-icon">🤖</div>
      <h2 className="welcome-title">Welcome to DSPy Agent</h2>
      <p className="welcome-text">
        I'm here to help you with various tasks using my comprehensive toolkit. 
        Choose a suggestion below or type your own question to get started.
      </p>
      <div className="suggested-prompts">
        {SUGGESTED_PROMPTS.map((suggestion, index) => (
          <button
            key={index}
            className="prompt-card"
            onClick={() => onSuggestedPrompt(suggestion.prompt)}
          >
            <div className="prompt-icon">{suggestion.icon}</div>
            <div className="prompt-text">{suggestion.text}</div>
          </button>
        ))}
      </div>
    </div>
  );
}