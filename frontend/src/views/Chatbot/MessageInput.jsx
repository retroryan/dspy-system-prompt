import React, { useState, useRef, useEffect } from 'react';

const QUICK_ACTIONS = [
  { label: '📚 Help', command: '/help' },
  { label: '🗑️ Clear', command: '/clear' },
  { label: '💾 Export', command: '/export' },
  { label: '🔧 Tools', command: '/tools' }
];

export default function MessageInput({ onSendMessage, isLoading, onCommand, toolSet, onToolSetChange }) {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef(null);
  
  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [inputValue]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      // Check if it's a command
      if (inputValue.startsWith('/')) {
        if (onCommand) {
          onCommand(inputValue);
        }
      } else {
        onSendMessage(inputValue);
      }
      setInputValue('');
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  const handleQuickCommand = (command) => {
    // Execute commands directly instead of inserting them
    if (command === '/clear') {
      if (onCommand) {
        onCommand(command);
      }
    } else {
      // For other commands, insert them in the input
      setInputValue(command + ' ');
      textareaRef.current?.focus();
    }
  };
  
  return (
    <div className="chat-input-container">
      <div className="input-actions">
        <div className="tool-selector">
          <label htmlFor="tool-set-select">Tools:</label>
          <select 
            id="tool-set-select"
            className="tool-set-select"
            value={toolSet} 
            onChange={(e) => onToolSetChange && onToolSetChange(e.target.value)}
            disabled={isLoading}
          >
            <option value="real_estate_mcp">🏠 Real Estate</option>
            <option value="ecommerce">🛒 E-commerce</option>
            <option value="agriculture">🌾 Agriculture</option>
            <option value="events">📅 Events</option>
          </select>
        </div>
        <div className="action-chips">
          {QUICK_ACTIONS.map((action, index) => (
            <button
              key={index}
              className="input-chip"
              onClick={() => handleQuickCommand(action.command)}
              disabled={isLoading}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
      <form className="chat-input-wrapper" onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          className={`chat-input ${isLoading ? 'disabled' : ''}`}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={isLoading ? "AI is thinking..." : "Ask me anything..."}
          disabled={isLoading}
          rows="1"
        />
        <button 
          type="submit"
          className="send-btn"
          disabled={isLoading || !inputValue.trim()}
        >
          <span>Send</span>
          <span>→</span>
        </button>
      </form>
    </div>
  );
}